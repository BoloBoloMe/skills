#!/usr/bin/env -S uv run python
"""sandbox-worktree M04: rootless 桥 netns 内 nft 双模式网络访问控制.

机制 (见 docs/changes/use-sandbox-worktree/milestone-04/MILESTONE-04-findings.md):
经 `podman unshare nsenter --net=<rootless-netns>` 无 root 进入桥 netns, 在自有表
`inet swt` 中按容器源地址注入过滤规则. 规则物理位于容器 netns 之外, 容器内任意
uid (含 root) 均不可达不可删 (调研 §4.1 实测结论, 本脚本承接).

用法:
  apply --mode whitelist --container-ip <IP> --gateway <IP> [--allow <IP/CIDR>]... [--netns <PATH>]
  apply --mode blacklist --container-ip <IP> --gateway <IP> [--deny <IP/CIDR>]...  [--netns <PATH>]
  show  [--netns <PATH>]
  clear [--netns <PATH>]

语义 (MILESTONE-04 + 调研 §4.1):
- whitelist = 默认拒: 仅放行 网关 DNS(tcp/udp 53) + --allow 条目 + 已建连接回程
  (保 host 发起连接如 ssh 发布端口的回程); 其余容器流出全断.
- blacklist = 默认放行: 仅断 --deny 条目 (护特定环境数据库/redis 场景).
- 两模式共通: IPv6 兜底 DROP (调研 §4.1).
- 条目只收 IP/CIDR; 域名须在盘点确认环节解析为 IP 后传入 (nft 无域名语义).
- 运行期不切换: apply 为表级全量替换, 无增量放行通道; 换模式/换清单 = 整体重建.

退出码: 0 = 成功; 1 = 注入/校验失败 (stderr 首行 <失败名>); 2 = 环境/参数错误.
"""
from __future__ import annotations

import argparse
import ipaddress
import os
import subprocess
import sys

TABLE = "swt"
DNS_PORTS = ("udp", "tcp")


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
    mode: str, container_ip: str, gateway: str, entries: list[str]
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

    # 多容器同 netns 守卫 (D010 允许多容器共存): 表按容器源地址过滤, 表级替换会把
    # 其它容器的规则一并清掉 (对它 fail-open). 发现异己 saddr 即拒绝, 不猜.
    existing = run_nft(netns, ["list", "table", "inet", TABLE])
    if existing.returncode == 0:
        foreign = {
            part[len("ip saddr "):].split()[0]
            for line in existing.stdout.splitlines()
            for part in [line.strip()]
            if part.startswith("ip saddr ")
        } - {container_ip}
        if foreign:
            die(
                1, "APPLY-CONFLICT",
                f"表 inet {TABLE} 已含其它容器源地址 {sorted(foreign)} 的规则; "
                "先 clear 或换专用 netns, 不做覆盖",
            )

    ruleset = build_ruleset(args.mode, container_ip, gateway, entries)

    # 幂等: 旧表有无皆可 (rc 不看), 重复表名会在下一步 add 报错被逮住.
    run_nft(netns, ["delete", "table", "inet", TABLE])

    add = run_nft(netns, ["-f", "-"], input_text=ruleset)
    if add.returncode != 0:
        die(1, "APPLY-FAIL", f"注入规则集失败: {add.stderr.strip()}")

    verify = run_nft(netns, ["list", "table", "inet", TABLE])
    marker = "meta nfproto ipv6 drop"
    if (
        verify.returncode != 0
        or marker not in verify.stdout
        or f"ip saddr {container_ip}" not in verify.stdout
    ):
        die(1, "APPLY-VERIFY-FAIL", "注入后校验失败 (表缺失或缺关键规则)")

    print(
        f"[SWT-NET] ok apply mode={args.mode} container_ip={container_ip} "
        f"entries={len(entries)} chain=forward+input table=inet {TABLE}"
    )
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
    apply_parser.add_argument("--netns", default=default_netns())

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
    return cmd_clear(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
