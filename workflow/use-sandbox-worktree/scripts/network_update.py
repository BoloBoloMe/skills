"""运行期白名单维护: 输入, 审批收据, 持久事务与有限恢复.

Host 接缝提供 locate/observe/expected/apply/checks, 不反向导入生命周期模块.
FileStore 只写本次指定的记录根; 本模块没有 stop/start/clear 或外部服务探测能力.
"""
from __future__ import annotations

import copy
import ipaddress
import json
import os
import re
import signal
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class NetworkError(Exception):
    def __init__(self, message: str, code: int = 2, *, settled: bool = True, process_group: int | None = None):
        super().__init__(message)
        self.code = code
        self.settled = settled
        self.process_group = process_group


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def cidr(raw: str) -> str:
    try:
        network = ipaddress.ip_network(raw, strict=False)
    except ValueError as exc:
        raise NetworkError("只接受 IPv4 地址或网段") from exc
    if network.version != 4:
        raise NetworkError("首版只接受 IPv4")
    return str(network)


def normalize_entries(entries) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw, reason in entries:
        address = cidr(raw)
        # 用 strip 判空, 保存原文, 不借维护改写用途.
        if not reason.strip():
            raise NetworkError("理由不能为空")
        if address in result and result[address] != reason:
            raise NetworkError(f"{address} 重复输入的理由冲突")
        result[address] = reason
    return result


def require_no_pending(runtime: dict) -> None:
    if "network-change" in runtime:
        raise NetworkError("存在未完成网络变更, 请先 network show / network recover")


@dataclass
class Request:
    action: str
    repo: Path
    records_root: Path
    name: str
    add: list = field(default_factory=list)
    remove: list = field(default_factory=list)
    reasons: list = field(default_factory=list)
    confirm: str | None = None


@dataclass
class Target:
    path: Path
    runtime: dict
    record: dict
    id: str
    running: bool
    netns: dict | None
    context: dict | None
    pair: dict


@dataclass
class ProcessResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    settled: bool = True
    process_group: int | None = None


class BoundedRunner:
    """每次独立进程组, 超时 TERM 2 秒/KILL 2 秒, 不和迟到写入抢跑."""
    @staticmethod
    def group_alive(pgid: int) -> bool:
        # 忽略僵尸: 它们已不能执行写入, 但 killpg(0) 仍会认为组存在.
        for path in Path("/proc").glob("[0-9]*/stat"):
            try:
                fields = path.read_text().rsplit(")", 1)[1].split()
                if int(fields[2]) == pgid and fields[0] != "Z":
                    return True
            except (OSError, ValueError, IndexError):
                continue
        return False

    def run(self, argv: list[str], *, input: str | None = None, timeout: float = 10) -> ProcessResult:
        try:
            proc = subprocess.Popen(argv, stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    start_new_session=True)
        except FileNotFoundError as exc:
            raise NetworkError(f"缺少环境命令: {argv[0]}", 4) from exc
        timed_out = False
        try:
            out, err = proc.communicate(input, timeout=timeout)
            if not self.group_alive(proc.pid):
                return ProcessResult(proc.returncode, out, err)
            # 主进程已退但还有子进程, 同样必须收尾后才允许回退.
            timed_out = True
        except subprocess.TimeoutExpired:
            timed_out = True
        out = err = ""
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + 2
            try:
                out, err = proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            while self.group_alive(proc.pid) and time.monotonic() < deadline:
                time.sleep(0.02)
            if proc.poll() is not None and not self.group_alive(proc.pid):
                return ProcessResult(proc.returncode, out, err, timed_out, True)
        # 不再无限 communicate/wait, 也不掩盖未回收状态.
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream:
                stream.close()
        return ProcessResult(proc.returncode if proc.returncode is not None else -1,
                             out, err, True, False, proc.pid)

    def checked(self, argv: list[str], *, input: str | None = None, timeout: float = 10):
        result = self.run(argv, input=input, timeout=timeout)
        if result.timed_out or not result.settled:
            raise NetworkError("命令超时" + (", 无法确认写进程已结束" if not result.settled else ", 进程组已结束"),
                               3, settled=result.settled, process_group=result.process_group)
        return result


class FileStore:
    def read(self, path: Path) -> dict:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise NetworkError("记录不是 JSON 对象")
        return value

    def write(self, path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def decision(self, request: Request, target: Target, fingerprint: dict) -> tuple[bool, dict]:
        """复用既有收据目录/字段协议, 只核对和消费参数指定的那张票."""
        kind = f"network-{request.action}"
        directory = request.records_root / "runtime" / target.path.stem / "decisions"
        if request.confirm:
            if not re.fullmatch(r"d-[a-zA-Z0-9-]+", request.confirm):
                raise NetworkError("确认收据 ID 非法")
            path = directory / f"{request.confirm}.json"
            try:
                payload = self.read(path)
            except (OSError, ValueError) as exc:
                raise NetworkError("确认收据不存在或已消费") from exc
            if payload.get("id") != request.confirm or payload.get("kind") != kind:
                raise NetworkError("确认收据 ID/kind 不匹配")
            if canonical(payload.get("fingerprint")) == canonical(fingerprint):
                path.unlink()  # 仓级锁内, 不调用按指纹消费另一张票的旧 helper.
                return True, payload
            path.unlink()  # 相关变化废票, 重新预览, 不执行.
        decision_id = "d-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + "-" + uuid.uuid4().hex[:8]
        payload = {"id": decision_id, "kind": kind, "fingerprint": fingerprint,
                   "options": [f"--confirm {decision_id}"], "created-at": datetime.now(timezone.utc).isoformat()}
        self.write(directory / f"{decision_id}.json", payload)
        return False, payload


def recorded_context(network: dict, record: dict) -> dict:
    return {"container-ip": network.get("container-ip") or record.get("network-ip"),
            "gateway": network.get("gateway"), "route-gateway": network.get("route-gateway"),
            "dns": list(network.get("auto-dns", []))}


def policy_for_context(network: dict, context: dict) -> dict:
    result = copy.deepcopy(network)
    users = {cidr(entry) for entry in result.get("allow", [])}
    auto = []
    for address in (context["gateway"], context.get("route-gateway"), context["container-ip"]):
        if address and cidr(address) not in users and address not in auto:
            auto.append(address)
    result.update({"auto-allow": auto,
                   "auto-dns": sorted(set(context["dns"]) - {context["gateway"]}),
                   "gateway": context["gateway"], "route-gateway": context.get("route-gateway"),
                   "container-ip": context["container-ip"], "table-present": True})
    return result


def normalized_reasons(network: dict) -> dict:
    reasons = network.get("allow-reasons", {})
    if not isinstance(reasons, dict) or any(not isinstance(v, str) for v in reasons.values()):
        raise NetworkError("allow-reasons 必须是地址到理由字符串的对应表")
    return {cidr(k): v for k, v in reasons.items()}


def entries_with_reasons(network: dict) -> list[dict]:
    normalized = normalized_reasons(network)
    return [{"address": cidr(raw), "reason": normalized.get(cidr(raw)) or "历史未记录理由",
             "ports": "全部端口"} for raw in network.get("allow", [])]


def auto_entries(network: dict) -> list[dict]:
    entries = [{"address": cidr(a), "reason": "自动基础通道 (网关/路由网关/容器自身)", "ports": "全部端口"}
               for a in network.get("auto-allow", [])]
    dns = set(network.get("auto-dns", []))
    if network.get("gateway"):
        dns.add(network["gateway"])
    entries.extend({"address": cidr(a), "reason": "自动 DNS", "ports": "仅 udp/tcp 53"} for a in sorted(dns))
    return entries


def plan_update(request: Request, network: dict, context: dict) -> tuple[dict, dict, bool]:
    add = normalize_entries(request.add)
    reasons = normalize_entries(request.reasons)
    remove = {cidr(a) for a in request.remove}
    if set(add) & (remove | set(reasons)) or remove & set(reasons):
        raise NetworkError("同一地址操作冲突")
    users = {cidr(a) for a in network.get("allow", [])}
    old_reasons = normalized_reasons(network)
    new_reasons = dict(old_reasons)
    for a, reason in add.items():
        if a in users and old_reasons.get(a) != reason:
            raise NetworkError(f"{a} 已存在, 应使用 --reason 更正已有理由")
        new_reasons[a] = reason
    for a, reason in reasons.items():
        if a not in users:
            raise NetworkError(f"{a} 用户条目不存在")
        new_reasons[a] = reason
    automatic = {cidr(a) for a in network.get("auto-allow", [])}
    automatic |= {item["address"] for item in auto_entries(network)}
    if (remove - users) & automatic:
        raise NetworkError("自动条目不是用户删除对象")
    new_users = (users | set(add)) - remove
    for a in remove:
        new_reasons.pop(a, None)
    proposed = copy.deepcopy(network)
    proposed["allow"] = sorted(new_users)
    if new_reasons or "allow-reasons" in network:
        proposed["allow-reasons"] = new_reasons
    proposed = policy_for_context(proposed, context)
    # 比较实际基础权限, 不将历史重复表示/元数据缺字段作为自动同步理由.
    old_auto = {"allow": sorted({cidr(a) for a in network.get("auto-allow", [])}),
                "gateway": network.get("gateway"), "route-gateway": network.get("route-gateway"),
                "container-ip": network.get("container-ip") or context["container-ip"],
                "dns": sorted(set(network.get("auto-dns", [])) | {network["gateway"]})}
    new_auto = {"allow": sorted({cidr(a) for a in proposed["auto-allow"]}),
                "gateway": proposed["gateway"], "route-gateway": proposed.get("route-gateway"),
                "container-ip": proposed["container-ip"],
                "dns": sorted(set(proposed["auto-dns"]) | {proposed["gateway"]})}
    # 用户条目和自动条目重叠时, 自动来源变化依旧展示, 不扩大/收缩用户条目.
    automatic_changed = old_auto != new_auto
    added, removed = sorted(new_users - users), sorted(users - new_users)
    reason_diff = [{"address": a, "before": old_reasons.get(a, "历史未记录理由"), "after": new_reasons[a]}
                   for a in sorted(new_users & users) if old_reasons.get(a) != new_reasons.get(a)]
    if reasons and not added and not removed and automatic_changed:
        raise NetworkError("自动项已变化, 请先单独执行不带用户变更的 network update 同步自动项")
    coverage = []
    final_all = new_users | {cidr(a) for a in proposed["auto-allow"]}
    for a in sorted(set(added) | set(removed)):
        if a in added:
            old_full = users | set(old_auto["allow"])
            previous = sorted(b for b in old_full if ipaddress.ip_network(a).subnet_of(ipaddress.ip_network(b)))
            if previous:
                coverage.append({"address": a, "already-allowed-by": previous,
                                 "effect": "新增用户条目, 但此前已有这些用户/自动条目放行全部端口"})
        covers = sorted(b for b in final_all if (b != a or a in removed) and ipaddress.ip_network(a).subnet_of(ipaddress.ip_network(b)))
        if covers:
            coverage.append({"address": a, "covered-by": covers, "effect": "仍被这些条目放行全部端口"})
        partial = sorted(b for b in final_all if b != a and ipaddress.ip_network(b).subnet_of(ipaddress.ip_network(a)))
        if partial and a in removed:
            coverage.append({"address": a, "partly-covered-by": partial, "effect": "这些子网仍放行, 并非全部权限收回"})
        dns_covers = sorted(d for d in new_auto["dns"] if ipaddress.ip_address(d) in ipaddress.ip_network(a))
        if a in removed and dns_covers:
            coverage.append({"address": a, "dns-still-allowed": dns_covers, "effect": "DNS udp/tcp 53 仍放行"})
    diff = {"add": [{"address": a, "reason": new_reasons[a], "ports": "全部端口"} for a in added],
            "remove": [{"address": a, "reason": old_reasons.get(a, "历史未记录理由")} for a in removed],
            "reasons": reason_diff, "automatic": {"before": old_auto, "after": new_auto} if automatic_changed else None,
            "coverage": coverage,
            "warnings": ["注意: 0.0.0.0/0 放行全部 IPv4 地址的全部端口"] if "0.0.0.0/0" in added else []}
    rules_changed = bool(added or removed or automatic_changed)
    if not rules_changed:
        # 理由提交不重放规则, 必须保留历史地址的顺序/重复表示与自动项原值.
        proposed = copy.deepcopy(network)
        if reason_diff:
            proposed["allow-reasons"] = new_reasons
    return proposed, diff, rules_changed


def blank_result(request: Request) -> dict:
    return {"schema": 1, "action": request.action, "container": {"name": request.name, "id": None},
            "stage": "rejected", "policy": None, "diff": {},
            "checks": {k: {"status": "未检查"} for k in ("rules", "ssh", "git", "dns-rules")},
            "pending": None, "decision-id": None, "error": None}


def pending_summary(runtime: dict):
    change = runtime.get("network-change")
    if "network-change" not in runtime:
        return None
    if not isinstance(change, dict):
        return {"id": None, "phase": "unrecognized"}
    summary = {"id": change.get("id"), "phase": change.get("phase")}
    if "unsettled-writer" in change:
        summary["unsettled-writer"] = change["unsettled-writer"]
    return summary


class Maintenance:
    def __init__(self, host, store: FileStore | None = None):
        self.host = host
        self.store = store or FileStore()

    def execute(self, request: Request) -> tuple[int, dict]:
        result = blank_result(request)
        try:
            if request.action not in {"show", "update", "recover"}:
                raise NetworkError("未知 network 操作")
            target = self.host.locate(request)
            if target.runtime.get("network") is not None and not isinstance(target.runtime["network"], dict):
                raise NetworkError("运行记录中的 network 不是对象")
            result.update(container={"name": request.name, "id": target.id},
                          policy=copy.deepcopy(target.runtime.get("network")), pending=pending_summary(target.runtime))
            if request.action == "show":
                return self.show(target, result)
            if request.action == "update":
                require_no_pending(target.runtime)
                if not target.running or target.record.get("retired"):
                    raise NetworkError("目标已经停止或 retired, 仅支持运行中目标")
                if (target.runtime.get("network") or {}).get("mode") != "whitelist":
                    raise NetworkError("network update 仅支持 whitelist")
                active = [r for r in target.runtime.get("containers", []) if isinstance(r, dict) and not r.get("retired")]
                if len(active) != 1:
                    raise NetworkError("多个可用或可恢复容器共用该记录网络配置, 不自动迁移")
                return self.update(request, target, result)
            return self.recover(request, target, result)
        except (NetworkError, OSError, ValueError, KeyError, TypeError) as exc:
            code = exc.code if isinstance(exc, NetworkError) else 2
            result.update(stage="unsupported" if code == 4 else "rejected",
                          error={"name": type(exc).__name__, "message": str(exc)})
            return code, result

    def show(self, target: Target, result: dict) -> tuple[int, dict]:
        network = result["policy"] or {}
        result["diff"] = {"entries": entries_with_reasons(network), "automatic": auto_entries(network)}
        if target.running:
            try:
                actual = self.host.observe(target)
                expected = self.host.expected(network, recorded_context(network, target.record))
                ok = actual == expected
                result["checks"]["rules"] = {"status": "通过" if ok else "失败", "actual": actual,
                                             "detail": "规则与记录一致" if ok else "规则与记录不一致, 仅报告, 不覆盖"}
            except (NetworkError, ValueError, KeyError) as exc:
                result["checks"]["rules"] = {"status": "失败", "detail": str(exc)}
        else:
            result["checks"]["rules"]["detail"] = "容器已停止, 实际规则不可取得"
        result["stage"] = "observed"
        return 0, result

    def approval(self, request: Request, target: Target, result: dict, actual, proposed, extra=None) -> bool:
        fingerprint = {"repo": str(request.repo), "pair": target.pair, "container": result["container"],
                       "netns": target.netns, "running": target.running,
                       "before": target.runtime.get("network"), "rules": actual, "context": target.context,
                       "request": {"add": normalize_entries(request.add), "remove": sorted({cidr(a) for a in request.remove}),
                                   "reasons": normalize_entries(request.reasons)}, "after": proposed, "transaction": extra}
        approved, receipt = self.store.decision(request, target, fingerprint)
        result["decision-id"] = receipt["id"]
        if not approved:
            result["stage"] = "decision-required"
            print(f"DECIDE {receipt['id']} network-{request.action} 目标 {request.name} {target.id}; "
                  f"差异 {canonical(result['diff'])}; 请批准后重跑 选项: --confirm {receipt['id']}")
        return approved

    def verified(self, target: Target, network: dict, context: dict, result: dict):
        actual = self.host.observe(target)
        if actual != self.host.expected(network, context):
            result["checks"]["rules"] = {"status": "失败", "actual": actual}
            raise NetworkError("应用后的规则核对失败", 3)
        result["checks"]["rules"] = {"status": "通过"}
        result["checks"]["dns-rules"] = {"status": "通过", "detail": "冻结配置 DNS udp/tcp 53 规则已核对, 未实测上游 DNS",
                                          "configured": context["dns"], "current": target.context["dns"]}
        if set(context["dns"]) - {context["gateway"]} != set(target.context["dns"]) - {context["gateway"]}:
            result["checks"]["dns-rules"]["detail"] += "; 旧 DNS 已恢复, 当前解析器与旧配置不同, 尚未同步"
        for name, check in self.host.checks(target):
            result["checks"][name] = check
            if check["status"] != "通过":
                raise NetworkError(f"{name} 检查失败", 3)
        return actual

    def commit(self, target: Target, network: dict):
        # 只改相关字段, 保留当前 runtime 的不相关内容.
        runtime = self.store.read(target.path)
        runtime["network"] = copy.deepcopy(network)
        runtime.pop("network-change", None)
        self.store.write(target.path, runtime)
        target.runtime = runtime

    def mark_required(self, target: Target, change: dict, result: dict, exc: Exception):
        change["phase"] = "recovery-required"
        if isinstance(exc, NetworkError) and not exc.settled:
            change["unsettled-writer"] = {"process-group": exc.process_group}
        target.runtime["network-change"] = change
        try:
            runtime = self.store.read(target.path)
            runtime["network-change"] = change
            self.store.write(target.path, runtime)
            target.runtime = runtime
        except (OSError, ValueError):
            pass
        result.update(stage="recovery-required", policy=None, pending=pending_summary(target.runtime),
                      error={"name": type(exc).__name__, "message": str(exc), "recovery": "保留现场, 先 network show / network recover; 不停容器/清表"})
        return 3, result

    def update(self, request: Request, target: Target, result: dict):
        before = copy.deepcopy(target.runtime["network"])
        old_context = recorded_context(before, target.record)
        actual = self.host.observe(target)
        old_rules = self.host.expected(before, old_context)
        if actual != old_rules:
            result["diff"] = {"expected": old_rules, "actual": actual}
            raise NetworkError("实际规则与记录不一致或含未知条目, 请另行决定人工收敛, 不覆盖/收编")
        result["checks"]["rules"] = {"status": "通过"}
        proposed, diff, rules_changed = plan_update(request, before, target.context)
        result["diff"] = diff
        if proposed == before:
            result.update(stage="noop", message="无变化, 未重建规则, 未声称收回额外访问权限")
            return 0, result
        if not self.approval(request, target, result, actual, proposed):
            return 1, result
        if not rules_changed:
            try:
                # 理由编辑也重新检查事实, 但不写防火墙/不建立网络事务.
                self.host.revalidate(target)
                if self.host.observe(target) != actual:
                    raise NetworkError("提交前规则变化, 请重新预览")
                self.commit(target, proposed)
            except (OSError, NetworkError, ValueError, KeyError, TypeError) as exc:
                result.update(stage="rejected", policy=None, error={"name": type(exc).__name__, "message": str(exc)})
                return 3, result
            result.update(stage="updated", policy=proposed, message="理由已更新, 未重建网络规则")
            return 0, result
        change = {"schema": 1, "id": uuid.uuid4().hex, "phase": "prepared",
                  "container": result["container"], "netns": target.netns,
                  "before": {"network": before, "context": old_context, "rules": actual},
                  "after": {"network": proposed, "context": target.context},
                  "decision-id": result["decision-id"], "created-at": datetime.now(timezone.utc).isoformat()}
        prepared = copy.deepcopy(target.runtime)
        prepared["network-change"] = change
        try:
            self.store.write(target.path, prepared)
        except OSError as exc:
            # replace 后目录同步也可能失败; 未获得持久化保证绝不动网络.
            try:
                self.store.write(target.path, target.runtime)
            except OSError:
                return self.mark_required(target, change, result, exc)
            result.update(stage="rejected", error={"name": type(exc).__name__, "message": "恢复依据保存失败, 未动网络"})
            return 2, result
        target.runtime = prepared
        try:
            self.host.apply(target, proposed, target.context, actual)
            change["phase"] = "applied"
            self.store.write(target.path, target.runtime)
            self.verified(target, proposed, target.context, result)
            self.commit(target, proposed)
        except (NetworkError, OSError, ValueError, KeyError, TypeError) as exc:
            if isinstance(exc, NetworkError) and not exc.settled:
                return self.mark_required(target, change, result, exc)
            try:
                current = self.host.observe(target)
                if current not in (actual, self.host.expected(proposed, target.context)):
                    raise NetworkError("失败后实际状态未知, 不抢写回退", 3)
                self.host.apply(target, before, old_context, current)
                self.verified(target, before, old_context, result)
                self.commit(target, before)
            except (NetworkError, OSError, ValueError, KeyError, TypeError) as rollback:
                return self.mark_required(target, change, result, rollback)
            result.update(stage="rolled-back", policy=before, pending=None,
                          error={"name": type(exc).__name__, "message": f"{exc}; 旧状态已核对恢复"})
            return 3, result
        result.update(stage="updated", policy=proposed, pending=None)
        return 0, result

    def recover(self, request: Request, target: Target, result: dict):
        change = target.runtime.get("network-change")
        if "network-change" not in target.runtime:
            result.update(stage="noop", message="无待恢复内容, 未修改规则或运行记录")
            return 0, result
        if not isinstance(change, dict) or change.get("schema") != 1 or change.get("phase") not in {"prepared", "applied", "recovery-required"}:
            raise NetworkError("无法核对的未完成事务")
        if change.get("container") != result["container"]:
            raise NetworkError("事务目标完整容器 ID 不一致, 不碰替换目标")
        if "unsettled-writer" in change:
            group = change["unsettled-writer"].get("process-group")
            if not isinstance(group, int) or BoundedRunner.group_alive(group):
                raise NetworkError("上次写进程尚未确认结束, 不抢写恢复")
        before, after = change["before"], change["after"]
        if target.runtime.get("network") not in (before["network"], after["network"]):
            raise NetworkError("记录包含事务不能解释的改动")
        if before["rules"] != self.host.expected(before["network"], before["context"]):
            raise NetworkError("事务旧规则快照无法核对")
        actual = None
        if target.running:
            if target.netns != change.get("netns"):
                raise NetworkError("网络空间身份已变, 有限恢复不覆盖")
            actual = self.host.observe(target)
            if actual not in (before["rules"], self.host.expected(after["network"], after["context"])):
                result["diff"] = {"actual": actual, "before": before["rules"], "after": self.host.expected(after["network"], after["context"])}
                raise NetworkError("实际规则含旧/新配置都不能解释的未知改动")
        elif not self.host.stopped_rules_absent(target, change):
            raise NetworkError("停止目标的原规则仍存在或无法确认不可用, 不清标记")
        result["diff"] = {"restore": before["network"], "current": target.runtime.get("network"),
                          "actual": actual, "running": target.running, "effect": "恢复旧配置; 停止目标不启动"}
        if not self.approval(request, target, result, actual, before["network"], change):
            return 1, result
        try:
            if target.running:
                self.host.apply(target, before["network"], before["context"], actual)
                self.verified(target, before["network"], before["context"], result)
            else:
                self.host.revalidate(target)
                if not self.host.stopped_rules_absent(target, change):
                    raise NetworkError("停止目标的规则状态变化", 3)
            self.commit(target, before["network"])
        except (NetworkError, OSError, ValueError, KeyError, TypeError) as exc:
            return self.mark_required(target, change, result, exc)
        result.update(stage="recovered", policy=before["network"], pending=None)
        return 0, result


def print_result(result: dict) -> None:
    print("NETWORK " + json.dumps(result, ensure_ascii=False, separators=(",", ":")))
