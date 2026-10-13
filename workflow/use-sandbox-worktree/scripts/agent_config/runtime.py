"""仅在带契约的新容器内运行. stdin 是唯一凭据入口, 错误不含原文."""
from __future__ import annotations

import json
import os
import pwd
import re
import stat
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

from . import pi
from .common import (CONTRACT, HOME, KEY_PATH, READY_PATH, SNAPSHOT_PATH, TemplateError,
                     client_env, pretty, private_json, safe_write, valid_key)
from .template import read_json, validate_snapshot

REAL_BIN_DIR = Path("/opt/swt-agent-bin")
OVERLAY = ".pi/agent/settings.overlay.json"
# 本工具只写固定客户端路径; templates 不能自带目的路径/安装命令.
OAUTH_PATHS = (".pi/agent/auth.json", ".codex/auth.json", ".kimi-code/credentials.json",
               ".kimi-code/credentials", ".kimi-code/oauth", ".kimi/credentials.json")


def checked_path(home: Path, relative: str, *, create: bool = False, owner=None) -> Path:
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise TemplateError("拒绝非固定相对路径")
    path = home / relative
    for parent in (*reversed(path.parents), path):
        if parent != home and home not in parent.parents:
            continue
        if parent.is_symlink():
            raise TemplateError("客户端目录/文件不得是符号链接")
    if create:
        parent = path.parent
        parents = []
        current = parent
        while current != home:
            if home not in current.parents:
                raise TemplateError("拒绝在 home 外创建客户端目录")
            parents.append(current)
            current = current.parent
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if owner:
            # 既存的 root 上级目录也必须交给 bolo, 不只是本次新建的叶目录.
            for directory in reversed(parents):
                os.chown(directory, *owner)
        os.chmod(parent, 0o700)
    return path


def install_payload(payload: dict, home: Path, owner: tuple[int, int]) -> None:
    value = validate_snapshot(payload["snapshot"])
    # 完整安装已留档时只验收, 不重新写配置/读取主机最新 Key.
    snapshot_path = checked_path(home, SNAPSHOT_PATH)
    if snapshot_path.exists():
        if validate_snapshot(read_json(snapshot_path)) != value:
            raise TemplateError("容器已有不同快照, 拒绝重新安装")
        check_files(value, home, owner)
        return
    key_path = checked_path(home, KEY_PATH)
    if key_path.exists():
        existing = private_json(key_path, uid=owner[0])
        if set(existing) != {"client_api_key"}:
            raise TemplateError("容器凭据含模板外字段")
        key = valid_key(existing["client_api_key"])
    else:
        key = valid_key(payload.get("client_api_key"))
    # 如果镜像/目标不是干净的新模型环境, 拒绝而不是擦掉已有 OAuth.
    for relative in OAUTH_PATHS:
        path = checked_path(home, relative)
        if path.exists() and (not path.is_file() or path.read_text().strip() not in ("", "{}")):
            raise TemplateError("目标存在 OAuth/其他认证数据, 不覆盖")
    if checked_path(home, READY_PATH).exists():
        raise TemplateError("已验收容器不允许重装")
    for relative, content in value["files"].items():
        if relative == OVERLAY:
            continue
        path = checked_path(home, relative, create=True, owner=owner)
        safe_write(path, content, owner=owner)
    settings_path = checked_path(home, ".pi/agent/settings.json", create=True, owner=owner)
    public = read_json(settings_path) if settings_path.exists() else {}
    if not isinstance(public, dict):
        raise TemplateError("Pi 公共设置不可解析")
    settings = pi.merge_settings(public, json.loads(value["files"][OVERLAY]))
    safe_write(settings_path, pretty(settings), owner=owner)
    safe_write(checked_path(home, KEY_PATH, create=True, owner=owner), pretty({"client_api_key": key}), owner=owner)
    safe_write(checked_path(home, SNAPSHOT_PATH, create=True, owner=owner), pretty(value), owner=owner)
    # install 从来不生成 ready. 真实配置解析/凭据/网关检查全过才可启动 agent.


def check_files(value: dict, home: Path, owner: tuple[int, int]) -> str:
    paths = [p for p in value["files"] if p != OVERLAY]
    paths += [".pi/agent/settings.json", KEY_PATH, SNAPSHOT_PATH]
    for relative in paths:
        path = checked_path(home, relative)
        st = path.stat()
        if not stat.S_ISREG(st.st_mode) or st.st_uid != owner[0] or stat.S_IMODE(st.st_mode) != 0o600:
            raise TemplateError("客户端配置/凭据权限或属主错误")
    for relative, text in value["files"].items():
        if relative == OVERLAY:
            settings = read_json(home / ".pi/agent/settings.json")
            if any(settings.get(k) != v for k, v in json.loads(text).items()) or any(k in settings for k in ("modelThinkingLevels", "thinkingBudgets", "httpProxy")):
                raise TemplateError("Pi 模型设置与固定快照不同")
            continue
        content = (home / relative).read_text()
        if content != text:
            raise TemplateError("客户端模型配置与固定快照不同, 不自动覆盖")
        if relative.endswith(".toml"):
            tomllib.loads(content)
        elif relative.endswith(".json"):
            json.loads(content)
    if validate_snapshot(read_json(home / SNAPSHOT_PATH)) != value:
        raise TemplateError("容器内固定快照与创建记录不同")
    for relative in OAUTH_PATHS:
        path = checked_path(home, relative)
        if path.exists() and (not path.is_file() or path.read_text().strip() not in ("", "{}")):
            raise TemplateError("目标含模板外 OAuth/认证数据")
    credentials = private_json(home / KEY_PATH, uid=owner[0])
    if set(credentials) != {"client_api_key"}:
        raise TemplateError("容器凭据文件包含客户端 Key 以外的字段")
    return valid_key(credentials["client_api_key"])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise TemplateError("网关发生重定向, 不转发客户端 Key")


def check_gateway(value: dict, key: str) -> None:
    request = urllib.request.Request(value["template"]["base_url"] + "/models",
                                     headers={"Authorization": "Bearer " + key})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=10) as response:
            if response.status != 200:
                raise TemplateError("网关模型清单检查失败")
            content = response.read(1024 * 1024 + 1)
        if len(content) > 1024 * 1024:
            raise TemplateError("网关模型清单过大")
        data = json.loads(content)
        found = {m["id"] for m in data["data"]}
        if not {m["id"] for m in value["catalog"]["models"]} <= found:
            raise TemplateError("网关没有模板声明的完整模型清单")
    except TemplateError:
        raise
    except urllib.error.HTTPError as exc:
        exc.close()
        raise TemplateError("网关不可达/认证失败/模型清单非法, 不回退供应商") from None
    except Exception:
        raise TemplateError("网关不可达/认证失败/模型清单非法, 不回退供应商") from None


def check_clients(key: str, owner: tuple[int, int]) -> None:
    env = client_env(dict(os.environ), key, home=HOME)
    providers = read_json(HOME / ".pi/agent/models.json")["providers"]
    if len(providers) != 1:
        raise TemplateError("Pi 配置不是单 provider")
    provider = next(iter(providers))
    # 固定 Codex 0.162.1 的 features list 会加载配置和原生模型目录, 不启动会话.
    # doctor 还会探测更新/网络/沙盒, 不属于仅 GET /models 的模板验收边界.
    commands = (("pi", ["--list-models"]), ("pi", ["auth", "check", "--provider", provider, "--json"]),
                ("codex", ["features", "list"]), ("kimi", ["doctor", "config"]))
    for cli, args in commands:
        try:
            result = subprocess.run([str(REAL_BIN_DIR / cli), *args], env=env,
                                    cwd=str(HOME), user=owner[0], group=owner[1],
                                    capture_output=True, text=True, check=False, timeout=45)
        except (OSError, subprocess.TimeoutExpired):
            raise TemplateError("客户端解析/凭据检查不能执行或超时") from None
        # 客户端诊断可能反射凭据. 不记录、不透传任何原始 stdout/stderr.
        if result.returncode != 0:
            raise TemplateError(f"{cli} 真实配置解析/凭据检查未通过")


def check_payload(payload: dict, home: Path, owner: tuple[int, int], *, clients=None) -> dict:
    value = validate_snapshot(payload["snapshot"])
    key = check_files(value, home, owner)
    (clients or check_clients)(key, owner)
    if check_files(value, home, owner) != key:
        raise TemplateError("客户端验收期间凭据发生变化, 不交付")
    check_gateway(value, key)
    return {"ok": True, "contract": CONTRACT, "snapshot-digest": value["snapshot-digest"],
            "checks": ["permissions", "config", "credentials", "clients", "gateway-models"]}


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    try:
        if args not in (["install"], ["check"], ["state"]) or os.geteuid() != 0 or Path("/etc/swt-agent-template-contract").read_text().strip() != str(CONTRACT):
            raise TemplateError("初始化工具仅用于契约匹配的新容器")
        raw = sys.stdin.read(16 * 1024 * 1024 + 1)
        if len(raw) > 16 * 1024 * 1024:
            raise TemplateError("初始化输入过大")
        payload = json.loads(raw)
        user = pwd.getpwnam("bolo")
        owner = (user.pw_uid, user.pw_gid)
        binding = payload["binding"]
        if not isinstance(binding, dict) or set(binding) != {"creation-token", "container-id"} or not re.fullmatch(r"[0-9a-f]{32}", binding.get("creation-token", "")) or not re.fullmatch(r"[0-9a-f]{64}", binding.get("container-id", "")):
            raise TemplateError("初始化输入缺少合法创建绑定")
        value = validate_snapshot(payload["snapshot"])
        ready_path = checked_path(HOME, READY_PATH)
        ready = {**binding, "snapshot-digest": value["snapshot-digest"], "contract": CONTRACT}
        if args == ["state"]:
            installed = checked_path(HOME, SNAPSHOT_PATH).exists()
            if installed:
                check_files(value, HOME, owner)
            print(json.dumps({"installed": installed}, separators=(",", ":")))
            return 0
        if ready_path.exists():
            if read_json(ready_path) != ready:
                raise TemplateError("已验收容器创建绑定不符, 拒绝重装")
        elif args == ["install"]:
            install_payload(payload, HOME, owner)
        else:
            raise TemplateError("新容器初始化未完成, 请用同一 birth 重入")
        report = check_payload(payload, HOME, owner)
        if args == ["install"] and not ready_path.exists():
            # ready 属主 root, bolo 可读; 不作为阻止容器用户自行改配置的安全边界.
            safe_write(ready_path, pretty(ready), mode=0o644, owner=(0, 0))
        print(json.dumps(report, separators=(",", ":")))
        return 0
    except TemplateError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except Exception:
        print("FAIL 模板安装/验收失败, 原始诊断已隐藏, 未交付", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
