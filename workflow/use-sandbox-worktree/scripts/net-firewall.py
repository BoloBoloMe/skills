#!/usr/bin/env -S uv run python
"""sandbox-worktree M04: rootless 桥 netns 内 nft 双模式网络访问控制.

机制 (见 docs/changes/use-sandbox-worktree/milestone-04/MILESTONE-04-findings.md):
经 `podman unshare nsenter --net=<rootless-netns>` 无 root 进入桥 netns, 在自有表
`inet swt` 中按容器源地址注入过滤规则. 规则物理位于容器 netns 之外, 容器内任意
uid (含 root) 均不可达不可删 (调研 §4.1 实测结论, 本脚本承接).

用法:
  apply --mode whitelist --container-ip <IP> --gateway <IP> [--allow <IP/CIDR>]... [--merge] [--netns <PATH>]
  apply --mode blacklist --container-ip <IP> --gateway <IP> [--deny <IP/CIDR>]...  [--merge] [--netns <PATH>]
  remove --container-ip <IP> [--netns <PATH>]
  show  [--netns <PATH>]
  clear [--netns <PATH>]

语义 (MILESTONE-04 + 调研 §4.1):
- whitelist = 默认拒: 仅放行 网关 DNS(tcp/udp 53) + --allow 条目 + 已建连接回程
  (保 host 发起连接如 ssh 发布端口的回程); 其余容器流出全断.
- blacklist = 默认放行: 仅断 --deny 条目 (护特定环境数据库/redis 场景).
- 两模式共通: IPv6 兜底 DROP (调研 §4.1).
- 条目只收 IP/CIDR; 域名须在盘点确认环节解析为 IP 后传入 (nft 无域名语义).
- 运行期不切换: apply 为表级全量替换, 无增量放行通道; 换模式/换清单 = 整体重建.
- apply --merge 在整体重建时保留异己容器的源地址规则; 不带时发现异己源地址即拒绝.
- remove 按容器源地址删除规则, 最后一个源地址消失时删除整表, 无目标时幂等.

退出码: 0 = 成功; 1 = 注入/校验失败 (stderr 首行 <失败名>); 2 = 环境/参数错误.
"""
from __future__ import annotations

import argparse
import ipaddress
import os
import re
import subprocess
import sys
from typing import NamedTuple

TABLE = "swt"
DNS_PORTS = ("udp", "tcp")


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
    foreign_rules: dict[str, list[str]] | None = None,
) -> str:
    lines: list[str] = [f"table inet {TABLE} {{"]

    def chain(name: str, body: list[str]) -> None:
        lines.append(f"\tchain {name} {{")
        lines.append(f"\t\ttype filter hook {name} priority filter + 10; policy accept;")
        lines.extend(body)
        lines.append("\t}")

    for chain_name in ("forward", "input"):
        body: list[str] = ["\t\tmeta nfproto ipv6 drop"]
        if mode == "whitelist":
            for proto in DNS_PORTS:
                body.append(
                    f"\t\tip saddr {container_ip} ip daddr {gateway} {proto} dport 53 accept"
                )
            for entry in entries:
                body.append(f"\t\tip saddr {container_ip} ip daddr {entry} accept")
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


def cmd_apply(args: argparse.Namespace) -> int:
    netns = args.netns
    container_ip = parse_ip(args.container_ip, "--container-ip")
    gateway = parse_ip(args.gateway, "--gateway")
    kind = "allow" if args.mode == "whitelist" else "deny"
    entries = parse_entries(getattr(args, kind), f"--{kind}")
    assert_netns_reachable(netns)

    existing = run_nft(netns, ["-a", "list", "table", "inet", TABLE])
    existing_rules = parse_saddr_rules(existing.stdout) if existing.returncode == 0 else []
    foreign_rules: dict[str, list[str]] = {"forward": [], "input": []}
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
        args.mode, container_ip, gateway, entries,
        foreign_rules if args.merge else None,
    )

    # 幂等: 旧表有无皆可 (rc 不看), 重复表名会在下一步 add 报错被逮住.
    run_nft(netns, ["delete", "table", "inet", TABLE])

    add = run_nft(netns, ["-f", "-"], input_text=ruleset)
    if add.returncode != 0:
        die(1, "APPLY-FAIL", f"注入规则集失败: {add.stderr.strip()}")

    verify = run_nft(netns, ["list", "table", "inet", TABLE])
    marker = "meta nfproto ipv6 drop"
    # 黑名单空名单时规则集无 ip saddr 行, 校验只查表和 ipv6 标记.
    expected_sources = {container_ip, *foreign} if (args.mode == "whitelist" or entries) else set(foreign)
    if (
        verify.returncode != 0
        or marker not in verify.stdout
        or any(f"ip saddr {source}" not in verify.stdout for source in expected_sources)
    ):
        die(1, "APPLY-VERIFY-FAIL", "注入后校验失败 (表缺失或缺关键规则)")

    print(
        f"[SWT-NET] ok apply mode={args.mode} container_ip={container_ip} "
        f"entries={len(entries)} chain=forward+input table=inet {TABLE}"
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
        if chain not in ("forward", "input") or not stripped.startswith("ip saddr "):
            continue
        source = stripped[len("ip saddr "):].split()[0]
        handle_match = re.search(r"\s+# handle (\d+)\s*$", line)
        # nft -a 正常会提供 handle; 缺失时无法安全地删除或重放该规则.
        if handle_match:
            body = line[:handle_match.start()].rstrip()
            rules.append(SaddrRule(chain, source, int(handle_match.group(1)), body))
    return rules


def cmd_remove(args: argparse.Namespace) -> int:
    netns = args.netns
    container_ip = parse_ip(args.container_ip, "--container-ip")
    assert_netns_reachable(netns)

    existing = run_nft(netns, ["-a", "list", "table", "inet", TABLE])
    if existing.returncode != 0:
        print(f"[SWT-NET] ok remove removed=absent table=inet {TABLE}")
        return 0

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


def cmd_clear(args: argparse.Namespace) -> int:
    netns = args.netns
    assert_netns_reachable(netns)
    result = run_nft(netns, ["delete", "table", "inet", TABLE])
    if result.returncode == 0:
        print(f"[SWT-NET] ok clear removed=table inet {TABLE}")
    else:
        print(f"[SWT-NET] ok clear removed=absent (幂等, 无表可删)")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser("apply", help="注入双模式规则 (表级全量替换)")
    apply_parser.add_argument("--mode", required=True, choices=("whitelist", "blacklist"))
    apply_parser.add_argument("--container-ip", required=True)
    apply_parser.add_argument("--gateway", required=True)
    apply_parser.add_argument("--allow", action="append", default=[], metavar="IP/CIDR")
    apply_parser.add_argument("--deny", action="append", default=[], metavar="IP/CIDR")
    apply_parser.add_argument("--merge", action="store_true", help="保留异己容器规则")
    apply_parser.add_argument("--netns", default=default_netns())

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
        return cmd_apply(args)
    if args.command == "show":
        return cmd_show(args)
    if args.command == "remove":
        return cmd_remove(args)
    return cmd_clear(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
