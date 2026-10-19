"""一次性实验: 观察 flow 拒绝后的降级分支.

不修改 src. 由于 _verify 在演练环境没有凭据, 真实调用必然抛错, 这里在运行时
临时替换 flow._verify, 只模拟 "令牌校验成功并返回某个用户" 这一前提, 然后调用
真实的 flow.handle -> authz.can_write -> sink.write_row 路径.

能证明: 拒绝分支的返回值和异常行为.
不能证明: 真实令牌校验, 真实请求身份, 生产日志和累计拒绝数.
"""

import sys

sys.path.insert(0, "src")
import flow  # noqa: E402

real_verify = flow._verify


def main() -> int:
    # 先确认真实入口在本环境确实被令牌校验挡住.
    try:
        real_verify("x")
    except RuntimeError as exc:
        print(f"real_verify_blocked: {exc}")

    try:
        flow._verify = lambda token: {"user": "bob"}  # viewer, 应拒绝
        denied = flow.handle({"token": "simulated", "resource": "report/x", "value": "v"})
        flow._verify = lambda token: {"user": "alice"}  # editor, 应允许
        allowed = flow.handle({"token": "simulated", "resource": "report/x", "value": "v"})
    finally:
        flow._verify = real_verify

    print(f"denied_result {denied}")
    print(f"allowed_result {allowed}")
    assert denied == {"written": 0, "skipped": 1}
    assert allowed == {"written": 1, "skipped": 0}
    print("denial_branch: no exception, returned written=0 skipped=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
