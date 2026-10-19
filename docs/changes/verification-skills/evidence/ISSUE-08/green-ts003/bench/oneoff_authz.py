"""非正式一次性实验 (不是正式测试用例): 直接调用权限判定函数 can_write.

边界:
- 只碰 bench/ 下的本脚本与 var/oneoff/ 下的输出, 不改 src/, 不改既有测试/配置.
- 证明的是 src/authz.py 内部函数在给定输入下的返回值, 不是成品入口 flow.handle 的行为.
- 真实入口 flow.handle 需要签名令牌 (外部服务), 演练环境无凭据, 本脚本不替代它.

用法: uv run python bench/oneoff_authz.py
"""

import sys

sys.path.insert(0, "src")
import authz  # noqa: E402
from authz import can_write  # noqa: E402

# (user, resource, expected, 说明)
CASES = [
    ("alice", "report/x", True, "editor 写 report/ 前缀"),
    ("alice", "report/sub/y", True, "editor 写嵌套 report/ 前缀"),
    ("carol", "report/x", True, "admin 写 report/ 前缀"),
    ("bob", "report/x", False, "viewer 无写权限"),
    ("mallory", "report/x", False, "未知用户"),
    ("", "report/x", False, "空用户名"),
    ("alice", "other/x", False, "非 report/ 前缀"),
    ("alice", "", False, "空资源"),
]


def main() -> int:
    before = sorted(name for name in vars(authz) if "count" in name or "deni" in name or "stat" in name)
    bad = 0
    for user, resource, expected, note in CASES:
        got = can_write(user, resource)
        ok = got is expected and isinstance(got, bool)
        bad += 0 if ok else 1
        print(f"user={user!r} resource={resource!r} -> {got!r} expect={expected!r} ok={ok}  # {note}")

    # 再调 100 次, 看模块里有没有累计拒绝数的属性 (有的话才能从内部拿到计数)
    for _ in range(100):
        can_write("bob", "report/x")
    after = sorted(name for name in vars(authz) if "count" in name or "deni" in name or "stat" in name)

    print(f"cases={len(CASES)} mismatches={bad}")
    print(f"模块计数属性 before={before} after={after}")
    print("结论范围: 仅内部函数 can_write 的返回值; 真实入口 flow.handle 未运行")
    print("非正式 TC: 本次为一次性实验, 授权范围 bench/ + var/oneoff/, src/ 未改")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
