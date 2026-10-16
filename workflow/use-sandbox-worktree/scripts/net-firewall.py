#!/usr/bin/env -S uv run python
"""sandbox-worktree M04: rootless 桥 netns 内 nft 双模式网络访问控制.

机制 (见 docs/changes/use-sandbox-worktree/milestone-04/MILESTONE-04-findings.md):
经 `podman unshare nsenter --net=<rootless-netns>` 无 root 进入桥 netns, 在自有表
`inet swt` 中按容器源地址注入过滤规则. 规则物理位于容器 netns 之外, 容器内任意
uid (含 root) 均不可达不可删 (调研 §4.1 实测结论, 本脚本承接).

用法:
  apply --mode whitelist --container-ip <IP> --gateway <IP> [--allow <IP/CIDR>]... [--dns <IP>]... [--merge] [--netns <PATH>]
  apply --mode blacklist --container-ip <IP> --gateway <IP> [--deny <IP/CIDR>]...  [--merge] [--netns <PATH>]
  remove --container-ip <IP> [--netns <PATH>]
  show  [--netns <PATH>]
  clear [--netns <PATH>]

语义 (MILESTONE-04 + 调研 §4.1 + 2026-09-14 出站链修复):
- 过滤覆盖三条链 forward/input/output, 三链规则镜像同构: output 管容器主动出站
  (pasta 直连拓扑下容器流量只走本 netns 的 OUTPUT/INPUT, forward 无流量 — 缺
  output 链 = whitelist 容器主动出站全通, 即 2026-09-14 bug, 见
  docs/changes/swt-firewall-outbound-bypass/2026-09-14-net-firewall-output-chain-bypass.md);
  forward/input 管桥拓扑的容器转发流量与网关向流量.
- whitelist = 默认拒: 仅放行 网关 DNS(tcp/udp 53) + --dns 条目 (容器实际解析器,
  取自容器 resolv.conf, 仅 tcp/udp 53) + --allow 条目 + 已建连接回程
  (保 host 发起连接如 ssh 发布端口的回程); 其余容器流出全断.
- blacklist = 默认放行: 仅断 --deny 条目 (护特定环境数据库/redis 场景).
- 两模式共通: IPv6 兜底 DROP (调研 §4.1).
- 条目只收 IP/CIDR; 域名须在盘点确认环节解析为 IP 后传入 (nft 无域名语义).
- 运行期不切换模式; 正式增删/理由维护使用 swt network, 本层复用原子换表.
- apply --merge 在整体重建时保留异己容器的源地址规则; 不带时发现异己源地址即拒绝.
- remove 按容器源地址删除规则, 最后一个源地址消失时删除整表, 无目标时幂等.

退出码: 0 = 成功; 1 = 注入/校验失败 (stderr 首行 <失败名>); 2 = 环境/参数错误.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import ipaddress
import json
import os
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple

TABLE = "swt"
DNS_PORTS = ("udp", "tcp")
# 过滤链: pasta 直连拓扑 (生产) 容器主动出站走 output, 桥拓扑 (测试夹具/共享 netns) 走 forward/input.
CHAINS = ("forward", "input", "output")


class SaddrRule(NamedTuple):
    rule_chain: str
    source: str
    handle: int
    body: str


def default_netns() -> str:
    xdg = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return f"{xdg}/containers/networks/rootless-netns/rootless-netns"


def nft_command(netns: str) -> list[str]:
    return ["podman", "unshare", "nsenter", f"--net={netns}", "nft"]


def run_nft(netns: str, args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        nft_command(netns) + args,
        capture_output=True,
        text=True,
        input=input_text,
        check=False,
    )


def die(code: int, tag: str, detail: str) -> "None":
    print(f"{tag} {detail}", file=sys.stderr)
    sys.exit(code)


def parse_entries(raw: list[str], kind: str) -> list[str]:
    entries: list[str] = []
    for item in raw:
        try:
            entries.append(str(ipaddress.ip_network(item, strict=False)))
        except ValueError:
            die(2, "INVALID-ENTRY", f"{kind} 条目 {item!r} 不是 IP/CIDR (域名须在盘点确认环节解析为 IP)")
    return entries


def parse_ip(raw: str, kind: str) -> str:
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        die(2, "INVALID-IP", f"{kind} {raw!r} 不是合法 IP")
        raise  # unreachable, 供类型检查


def assert_netns_reachable(netns: str) -> None:
    probe = run_nft(netns, ["list", "tables"])
    if probe.returncode != 0:
        print(
            f"NETNS-UNREACHABLE {netns}\n"
            "nft 经该 netns 不可用 (stderr 如下). 常见原因: rootless netns 尚未建立 —\n"
            "网络单独 create 不产生 netns, 第一个容器 start 后才出现 (findings F-M04-02);\n"
            "或路径失效 (可用 `pgrep -af 'pasta --config-net'` 从 --netns 参数重新发现).\n"
            f"--- stderr ---\n{probe.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(2)


def build_ruleset(
    mode: str,
    container_ip: str,
    gateway: str,
    entries: list[str],
    dns_servers: list[str] | None = None,
    foreign_rules: dict[str, list[str]] | None = None,
) -> str:
    lines: list[str] = [f"table inet {TABLE} {{"]

    def chain(name: str, body: list[str]) -> None:
        lines.append(f"\tchain {name} {{")
        lines.append(f"\t\ttype filter hook {name} priority filter + 10; policy accept;")
        lines.extend(body)
        lines.append("\t}")

    for chain_name in CHAINS:
        body: list[str] = ["\t\tmeta nfproto ipv6 drop"]
        if mode == "whitelist":
            for proto in DNS_PORTS:
                body.append(
                    f"\t\tip saddr {container_ip} ip daddr {gateway} {proto} dport 53 accept"
                )
            for server in dns_servers or []:
                for proto in DNS_PORTS:
                    body.append(
                        f"\t\tip saddr {container_ip} ip daddr {server} {proto} dport 53 accept"
                    )
            for entry in entries:
                body.append(f"\t\tip saddr {container_ip} ip daddr {entry} accept")
            if chain_name == "output":
                # 只放回程方向 (host 发起连接的出向应答)。容器主动发起的既有连接
                # 是 original 方向, 不得因 established 持续放行 — 否则策略收紧后
                # 旧连接仍可出站 (2026-09-17 冷审阻塞项 1)。放行目的地的流量仍由
                # 上方 daddr 规则接纳, 不受影响。
                body.append("\t\tct state established,related ct direction reply accept")
            else:
                # input/forward: 容器发起连接的应答 (reply) 与 host 发起连接的来包
                # (original) 都是必需回程, 保留双向 established
                body.append("\t\tct state established,related accept")
            body.append(f"\t\tip saddr {container_ip} drop")
        else:
            for entry in entries:
                body.append(f"\t\tip saddr {container_ip} ip daddr {entry} drop")
            body.append("\t\tct state established,related accept")
        if foreign_rules:
            body.extend(foreign_rules.get(chain_name, []))
        chain(chain_name, body)

    lines.append("}")
    return "\n".join(lines) + "\n"


def _cmd_apply(args: argparse.Namespace) -> int:
    netns = args.netns
    container_ip = parse_ip(args.container_ip, "--container-ip")
    gateway = parse_ip(args.gateway, "--gateway")
    kind = "allow" if args.mode == "whitelist" else "deny"
    entries = parse_entries(getattr(args, kind), f"--{kind}")
    dns_servers: list[str] = []
    if args.mode == "whitelist":
        for item in args.dns:
            server = parse_ip(item, "--dns")
            # 网关已有专用 DNS 规则, 去重; 同一解析器重复条目去重
            if server != gateway and server not in dns_servers:
                dns_servers.append(server)
    assert_netns_reachable(netns)

    existing = run_nft(netns, ["-a", "list", "table", "inet", TABLE])
    existing_rules = parse_saddr_rules(existing.stdout) if existing.returncode == 0 else []
    # 合并前识别所有受管结构, 不默默丢掉未知公共链/目标/异己规则.
    if existing.returncode == 0 and (args.merge or getattr(args, "expect_snapshot", None)):
        observed = run_nft(netns, ["-j", "list", "table", "inet", TABLE])
        try:
            if observed.returncode != 0:
                raise ValueError("无法读取 JSON 规则")
            snapshot = snapshot_json(json.loads(observed.stdout), container_ip)
            if getattr(args, "expect_snapshot", None) and snapshot_digest(snapshot) != args.expect_snapshot:
                raise ValueError("目标规则在批准后变化")
        except (ValueError, KeyError, TypeError) as exc:
            die(1, "APPLY-UNSAFE-MERGE", str(exc))
    elif getattr(args, "expect_snapshot", None):
        die(1, "APPLY-DRIFT", "批准的旧规则表已不存在")
    if args.merge and existing.returncode == 0:
        saddr_lines = [
            line for line in existing.stdout.splitlines()
            if line.strip().startswith("ip saddr ")
        ]
        if len(saddr_lines) > len(existing_rules):
            die(
                1, "APPLY-UNSAFE-MERGE",
                f"表中 {len(saddr_lines) - len(existing_rules)} 条源地址规则缺 handle 无法安全重放; "
                "先 clear 或人工处理, 不做静默丢弃的 merge",
            )
    foreign_rules: dict[str, list[str]] = {name: [] for name in CHAINS}
    foreign = {
        line.strip()[len("ip saddr "):].split()[0]
        for line in existing.stdout.splitlines()
        if line.strip().startswith("ip saddr ")
    } - {container_ip}
    if foreign and not args.merge:
        die(
            1, "APPLY-CONFLICT",
            f"表 inet {TABLE} 已含其它容器源地址 {sorted(foreign)} 的规则; "
            "先 clear 或换专用 netns, 不做覆盖",
        )
    if args.merge:
        for rule in existing_rules:
            if rule.source != container_ip:
                foreign_rules[rule.rule_chain].append(rule.body)

    ruleset = build_ruleset(
        args.mode, container_ip, gateway, entries, dns_servers,
        foreign_rules if args.merge else None,
    )

    # 幂等 + 原子: 表在场则同一事务内先删后建 (nft -f 整文件单事务), 注入失败时
    # 旧表原样保留, 不留无表 fail-open 窗口 (2026-09-17 冷审阻塞项 2)
    payload = ruleset
    if existing.returncode == 0:
        payload = f"delete table inet {TABLE}\n" + payload
    add = run_nft(netns, ["-f", "-"], input_text=payload)
    if add.returncode != 0:
        die(1, "APPLY-FAIL", f"注入规则集失败: {add.stderr.strip()}")

    verify = run_nft(netns, ["list", "table", "inet", TABLE])
    marker = "meta nfproto ipv6 drop"
    # 逐链校验: 每条链各自含 IPv6 兜底 (防止规则落错链/缺链仍全局计数达标)
    chain_blocks: dict[str, list[str]] = {}
    current_chain: str | None = None
    for line in verify.stdout.splitlines():
        chain_match = re.match(r"^\s*chain\s+(\S+)\s+\{", line)
        if chain_match:
            current_chain = chain_match.group(1)
            chain_blocks[current_chain] = []
        elif current_chain is not None:
            if line.strip() == "}":
                current_chain = None
            else:
                chain_blocks[current_chain].append(line)
    chain_ok = all(
        name in chain_blocks and any(marker in line for line in chain_blocks[name])
        for name in CHAINS
    )
    # 黑名单空名单时规则集无 ip saddr 行, 校验只查表和逐链 ipv6 标记.
    expected_sources = {container_ip, *foreign} if (args.mode == "whitelist" or entries) else set(foreign)
    sources_ok = all(f"ip saddr {source}" in verify.stdout for source in expected_sources)
    if verify.returncode != 0 or not chain_ok or not sources_ok:
        die(1, "APPLY-VERIFY-FAIL", "注入后校验失败 (表缺失或缺关键规则)")

    print(
        f"[SWT-NET] ok apply mode={args.mode} container_ip={container_ip} "
        f"entries={len(entries)} dns={len(dns_servers)} "
        f"chain={'+'.join(CHAINS)} table=inet {TABLE}"
    )
    return 0


def parse_saddr_rules(text: str) -> list[SaddrRule]:
    """解析 nft -a 输出中的源地址规则, 返回 chain/source/handle/规则正文."""
    rules: list[SaddrRule] = []
    chain: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        chain_match = re.match(r"^chain\s+(\S+)\s+\{", stripped)
        if chain_match:
            chain = chain_match.group(1)
            continue
        if stripped == "}":
            chain = None
            continue
        if chain not in CHAINS or not stripped.startswith("ip saddr "):
            continue
        source = stripped[len("ip saddr "):].split()[0]
        handle_match = re.search(r"\s+# handle (\d+)\s*$", line)
        # nft -a 正常会提供 handle; 缺失时无法安全地删除或重放该规则.
        if handle_match:
            body = line[:handle_match.start()].rstrip()
            rules.append(SaddrRule(chain, source, int(handle_match.group(1)), body))
    return rules


def _cmd_remove(args: argparse.Namespace) -> int:
    netns = args.netns
    container_ip = parse_ip(args.container_ip, "--container-ip")
    assert_netns_reachable(netns)

    existing = run_nft(netns, ["-a", "list", "table", "inet", TABLE])
    if existing.returncode != 0:
        print(f"[SWT-NET] ok remove removed=absent table=inet {TABLE}")
        return 0

    observed = run_nft(netns, ["-j", "list", "table", "inet", TABLE])
    try:
        if observed.returncode != 0:
            raise ValueError("无法读取受管表")
        snapshot_json(json.loads(observed.stdout), container_ip)
    except (ValueError, KeyError, TypeError) as exc:
        die(1, "REMOVE-UNSAFE", str(exc))
    matches = [
        rule for rule in parse_saddr_rules(existing.stdout) if rule.source == container_ip
    ]
    for rule in matches:
        deleted = run_nft(
            netns,
            [
                "delete", "rule", "inet", TABLE,
                rule.rule_chain, "handle", str(rule.handle),
            ],
        )
        if deleted.returncode != 0:
            die(
                1, "REMOVE-FAIL",
                f"删除 {rule.rule_chain} handle {rule.handle} 失败: {deleted.stderr.strip()}",
            )

    remaining = run_nft(netns, ["list", "table", "inet", TABLE])
    if remaining.returncode != 0:
        die(1, "REMOVE-VERIFY-FAIL", "删除后无法校验 inet swt 表")
    if not any(line.strip().startswith("ip saddr ") for line in remaining.stdout.splitlines()):
        deleted_table = run_nft(netns, ["delete", "table", "inet", TABLE])
        if deleted_table.returncode != 0:
            die(1, "REMOVE-FAIL", f"删除空表失败: {deleted_table.stderr.strip()}")
        table_state = "table-removed"
    else:
        table_state = "table-kept"

    if matches:
        print(
            f"[SWT-NET] ok remove removed={len(matches)} "
            f"container_ip={container_ip} {table_state}"
        )
    else:
        print(f"[SWT-NET] ok remove removed=absent {table_state}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    netns = args.netns
    assert_netns_reachable(netns)
    result = run_nft(netns, ["list", "table", "inet", TABLE])
    if result.returncode != 0:
        die(1, "NO-TABLE", f"表 inet {TABLE} 不存在 (未注入, 或 netns 已随容器停止重建)")
    sys.stdout.write(result.stdout)
    return 0


def _cmd_clear(args: argparse.Namespace) -> int:
    netns = args.netns
    assert_netns_reachable(netns)
    result = run_nft(netns, ["delete", "table", "inet", TABLE])
    if result.returncode == 0:
        print(f"[SWT-NET] ok clear removed=table inet {TABLE}")
    else:
        print(f"[SWT-NET] ok clear removed=absent (幂等, 无表可删)")
    return 0


@contextmanager
def write_lock(netns: str, expected: str | None = None, timeout: float = 5):
    """按 UID 和实际空间设备号/inode 共享, 与记录根/项目无关."""
    stat = os.stat(netns)
    identity = f"{stat.st_dev}:{stat.st_ino}"
    if expected and identity != expected:
        raise ValueError("网络空间身份变化")
    base = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
    directory = base / "swt-net-locks"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.is_symlink() or directory.stat().st_uid != os.getuid():
        raise ValueError("网络写锁目录不安全")
    directory.chmod(0o700)
    fd = os.open(directory / f"{stat.st_dev}-{stat.st_ino}.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise ValueError("网络空间写锁忙, 未执行")
                time.sleep(0.02)
        current = os.stat(netns)
        if (current.st_dev, current.st_ino) != (stat.st_dev, stat.st_ino):
            raise ValueError("等待写锁期间网络空间变化")
        yield
    finally:
        os.close(fd)


def locked_command(function, args):
    try:
        with write_lock(args.netns, getattr(args, "expect_netns", None)):
            return function(args)
    except (OSError, ValueError) as exc:
        die(2, "NETNS-LOCK", str(exc))


def cmd_apply(args):
    # 参数/空间可达性保持原错误协议; 受管表的读/合并/写/核对仍全部在锁内.
    parse_ip(args.container_ip, "--container-ip")
    parse_ip(args.gateway, "--gateway")
    kind = "allow" if args.mode == "whitelist" else "deny"
    parse_entries(getattr(args, kind), f"--{kind}")
    for server in args.dns:
        parse_ip(server, "--dns")
    assert_netns_reachable(args.netns)
    return locked_command(_cmd_apply, args)


def cmd_remove(args):
    return locked_command(_cmd_remove, args)


def cmd_clear(args):
    return locked_command(_cmd_clear, args)


def snapshot_digest(snapshot: dict) -> str:
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def normalized_body(body: str) -> str:
    body = " ".join(body.split())
    # nft 对 /32 显示为单地址, set 顺序与打印空白不是权限变化.
    def address(match):
        return str(ipaddress.ip_network(match.group(), strict=False))
    body = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d+)?\b", address, body)
    body = body.replace("related,established", "established,related")
    return body


def expected_snapshot(network: dict, context: dict) -> dict:
    """仍用同一规则生成器, 不另造一套授权引擎."""
    source = context["container-ip"]
    entries = list(network.get("allow" if network["mode"] == "whitelist" else "deny", []))
    if network["mode"] == "whitelist":
        entries.extend(f"{a}/32" for a in network.get("auto-allow", []))
    text = build_ruleset(network["mode"], source, context["gateway"], entries,
                         network.get("auto-dns", []))
    result = {}
    chain = None
    for line in text.splitlines():
        line = line.strip()
        match = re.fullmatch(r"chain (\w+) \{", line)
        if match:
            chain = match.group(1)
            result[chain] = {"type": "filter", "hook": chain, "prio": 10, "policy": "accept", "rules": []}
        elif line == "}":
            chain = None
        elif chain and not line.startswith("type "):
            result[chain]["rules"].append(normalized_body(line))
    return canonical_snapshot(result)


def canonical_snapshot(chains: dict) -> dict:
    """公共回程规则位置不决定目标权限; 目标规则顺序与重复条目仍保留."""
    result = {}
    for name, chain in sorted(chains.items()):
        rules = chain["rules"]
        common = [r for r in rules if not r.startswith("ip saddr ")]
        target = [r for r in rules if r.startswith("ip saddr ")]
        result[name] = {**chain, "rules": common + target}
    return result


def _json_value(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and set(value) == {"prefix"}:
        p = value["prefix"]
        if set(p) == {"addr", "len"}:
            return f"{p['addr']}/{p['len']}"
    values = value.get("set") if isinstance(value, dict) and set(value) == {"set"} else value
    if isinstance(values, list) and all(isinstance(v, str) for v in values):
        return ",".join(sorted(values, key=lambda v: (v != "established", v)))
    raise ValueError("未知 nft 比较值")


def _json_body(expressions: list) -> str:
    tokens = []
    for expr in expressions:
        if set(expr) == {"counter"}:
            continue
        if set(expr) in ({"accept"}, {"drop"}) and next(iter(expr.values())) is None:
            tokens.append(next(iter(expr)))
            continue
        if set(expr) != {"match"}:
            raise ValueError("未知 nft 表达式")
        match = expr["match"]
        if set(match) != {"op", "left", "right"} or match["op"] not in ("==", "in"):
            raise ValueError("未知 nft 匹配语义")
        left = match["left"]
        if left == {"meta": {"key": "nfproto"}}:
            prefix = "meta nfproto"
        elif left == {"ct": {"key": "state"}}:
            prefix = "ct state"
        elif left == {"ct": {"key": "direction"}}:
            prefix = "ct direction"
        elif isinstance(left, dict) and set(left) == {"payload"}:
            payload = left["payload"]
            pair = (payload.get("protocol"), payload.get("field"))
            if set(payload) != {"protocol", "field"} or pair not in {("ip", "saddr"), ("ip", "daddr"), ("tcp", "dport"), ("udp", "dport")}:
                raise ValueError("未知 nft payload")
            prefix = " ".join(pair)
        else:
            raise ValueError("未知 nft 匹配字段")
        value = str(match["right"]) if isinstance(match["right"], int) else _json_value(match["right"])
        tokens.extend([prefix, value])
    return normalized_body(" ".join(tokens))


def snapshot_json(payload: dict, source: str) -> dict:
    """只承认既有三链/IPv6/回程/源地址规则. 未知结构拒绝, handle/counter 忽略.

    同时验证异己源地址规则可由已有 merge 原样重放, 但不把它们绑定到目标收据.
    """
    chains, bodies = {}, {}
    table_count = 0
    for item in payload["nftables"]:
        if set(item) == {"metainfo"}:
            continue
        if set(item) == {"table"}:
            table = item["table"]
            if table.get("family") != "inet" or table.get("name") != TABLE or set(table) - {"family", "name", "handle"}:
                raise ValueError("未知 nft 表结构")
            table_count += 1
        elif set(item) == {"chain"}:
            chain = item["chain"]
            name = chain.get("name")
            if (name not in CHAINS or name in chains or chain.get("family") != "inet" or chain.get("table") != TABLE
                    or set(chain) - {"family", "table", "name", "handle", "type", "hook", "prio", "policy"}):
                raise ValueError("未知或重复 nft 链")
            wanted = {"type": "filter", "hook": name, "prio": 10, "policy": "accept"}
            if any(chain.get(k) != v for k, v in wanted.items()):
                raise ValueError("公共链语义变化")
            chains[name] = {**wanted, "rules": []}
            bodies[name] = []
        elif set(item) == {"rule"}:
            rule = item["rule"]
            name = rule.get("chain")
            if (name not in chains or rule.get("family") != "inet" or rule.get("table") != TABLE
                    or set(rule) - {"family", "table", "chain", "handle", "expr"}):
                raise ValueError("未知 nft 规则结构")
            body = _json_body(rule["expr"])
            common = {"meta nfproto ipv6 drop", "ct state established,related accept",
                      "ct state established,related ct direction reply accept"}
            pattern = r"ip saddr (\d+\.\d+\.\d+\.\d+/32)(?: ip daddr \d+\.\d+\.\d+\.\d+/\d+(?: (?:tcp|udp) dport 53)?)? (?:accept|drop)"
            match = re.fullmatch(pattern, body)
            if body not in common and not match:
                raise ValueError("未知目标/公共规则")
            bodies[name].append(body)
            if not match or match.group(1) == normalized_body(source):
                chains[name]["rules"].append(body)
        else:
            raise ValueError("未知 nft 对象, 不静默丢弃")
    if table_count != 1 or set(chains) != set(CHAINS):
        raise ValueError("受管三链不完整")
    for name, rules in bodies.items():
        common = [r for r in rules if not r.startswith("ip saddr ")]
        ct = "ct state established,related ct direction reply accept" if name == "output" else "ct state established,related accept"
        if not rules or rules[0] != "meta nfproto ipv6 drop" or common not in (["meta nfproto ipv6 drop", ct], ["meta nfproto ipv6 drop", "ct state established,related accept"]):
            raise ValueError("公共 IPv6/回程规则变化或位置不安全")
        ct_index = next(i for i, r in enumerate(rules) if r.startswith("ct state "))
        if any(i < ct_index for i, r in enumerate(rules) if re.fullmatch(r"ip saddr [0-9./]+ drop", r)):
            raise ValueError("源地址兜底丢弃位于回程规则之前")
    return canonical_snapshot(chains)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser("apply", help="注入双模式规则 (表级全量替换)")
    apply_parser.add_argument("--mode", required=True, choices=("whitelist", "blacklist"))
    apply_parser.add_argument("--container-ip", required=True)
    apply_parser.add_argument("--gateway", required=True)
    apply_parser.add_argument("--allow", action="append", default=[], metavar="IP/CIDR")
    apply_parser.add_argument("--deny", action="append", default=[], metavar="IP/CIDR")
    apply_parser.add_argument("--dns", action="append", default=[], metavar="IP")
    apply_parser.add_argument("--merge", action="store_true", help="保留异己容器规则")
    apply_parser.add_argument("--netns", default=default_netns())
    apply_parser.add_argument("--expect-snapshot", help=argparse.SUPPRESS)
    apply_parser.add_argument("--expect-netns", help=argparse.SUPPRESS)

    remove_parser = subparsers.add_parser("remove", help="按容器源地址删除规则")
    remove_parser.add_argument("--container-ip", required=True)
    remove_parser.add_argument("--netns", default=default_netns())

    show_parser = subparsers.add_parser("show", help="列出当前 inet swt 表")
    show_parser.add_argument("--netns", default=default_netns())

    clear_parser = subparsers.add_parser("clear", help="删除 inet swt 表 (幂等)")
    clear_parser.add_argument("--netns", default=default_netns())

    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.command == "apply":
        if args.mode == "whitelist" and args.deny:
            die(2, "INVALID-ARGUMENT", "whitelist 模式不接受 --deny (用 --allow)")
        if args.mode == "blacklist" and args.allow:
            die(2, "INVALID-ARGUMENT", "blacklist 模式不接受 --allow (用 --deny)")
        if args.mode == "blacklist" and args.dns:
            die(2, "INVALID-ARGUMENT", "blacklist 模式默认全通, 不接受 --dns (解析器无需单列放行)")
        return cmd_apply(args)
    if args.command == "show":
        return cmd_show(args)
    if args.command == "remove":
        return cmd_remove(args)
    return cmd_clear(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
