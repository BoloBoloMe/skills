"""mailbox post HTTP 状态码测试 (ISSUE-03, 投信校验).

TC-016 test_body_over_1mb_413: 正文超 1MB 拒收 413 (AC-021/BR-006).
TC-017 test_from_mismatch_403: letter.from 与签名 session 不符拒收 403 (AC-022/D013).
TC-017 test_from_mismatch_403: letter.from 与签名 session 不符拒收 403 (AC-022/D013).

真实子进程 serve + 回环 HTTP, handler 级请求构造;
共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

from conftest import make_letter, post_letter, register_session

MB = 1024 * 1024


def test_body_over_1mb_413(serves):
    """TC-016 (AC-021): 正文超 1MB 拒收 413; 恰 1MB 边界仍收下."""
    srv = serves()
    creds = register_session(srv, "s1")
    key = creds["signing_key"]

    code, resp = post_letter(srv, "s1", key,
                             make_letter(letter_id="B-1", to="s1",
                                         body="x" * (MB + 1)))
    assert code == 413, f"超限正文应 413: {resp}"

    code, resp = post_letter(srv, "s1", key,
                             make_letter(letter_id="B-2", to="s1",
                                         body="y" * MB))
    assert code == 200, f"恰 1MB 不超限应收下: {resp}"


def test_from_mismatch_403(serves):
    """TC-017 (AC-022): 发件人字段与签名所用 session 不符 → 403 拒收;
    from 与签名 session 一致 → 正常收下."""
    srv = serves()
    creds = register_session(srv, "s1")
    key = creds["signing_key"]

    code, resp = post_letter(srv, "s1", key,
                             make_letter(letter_id="F-1", to="s1",
                                         from_="attacker"))
    assert code == 403, f"伪造发件人应 403: {resp}"

    code, resp = post_letter(srv, "s1", key,
                             make_letter(letter_id="F-2", to="s1", from_="s1"))
    assert code == 200, f"from 与签名一致应收下: {resp}"
