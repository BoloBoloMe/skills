"""固定 agent 入口, 不需要 shell source, 不把秘密放进 argv."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .common import (CONTRACT, HOME, KEY_PATH, READY_PATH, TemplateError,
                     client_env, private_json, valid_key)
from .runtime import REAL_BIN_DIR, checked_path


def launch_env(home: Path, env: dict[str, str]) -> dict[str, str]:
    ready = json.loads(checked_path(home, READY_PATH).read_text())
    if ready.get("contract") != CONTRACT or not ready.get("snapshot-digest"):
        raise TemplateError("新容器 agent 模板尚未验收完成")
    key = valid_key(private_json(checked_path(home, KEY_PATH))["client_api_key"])
    return client_env(env, key, home=home)


# 入口名 -> (真实客户端, 固定默认参数). codex-d 是免审批/免沙箱的固定快捷入口,
# 仍走同一模板凭据与检查, 不另存 Key, 也不经 shell 拼接参数.
ENTRIES = {
    "pi": ("pi", ()),
    "codex": ("codex", ()),
    "kimi": ("kimi", ()),
    "codex-d": ("codex", ("--dangerously-bypass-approvals-and-sandbox",)),
}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        entry = args[0] if args else ""
        if entry not in ENTRIES:
            raise TemplateError("未知 agent 入口")
        cli, defaults = ENTRIES[entry]
        user = args[1:]
        rest = [*defaults, *user]
        binary = str(REAL_BIN_DIR / cli)
        if user in (["--version"], ["--help"]):
            # 纯元数据入口用于无凭据的镜像版本探测, 不允许夹带任务.
            from .common import filtered_env
            env, _ = filtered_env(dict(os.environ))
        else:
            env = launch_env(HOME, dict(os.environ))
        os.execve(binary, [binary, *rest], env)
    except Exception:
        print("FAIL agent 模板未就绪/凭据不可读, 不启动、不回退", file=sys.stderr)
        return 2
