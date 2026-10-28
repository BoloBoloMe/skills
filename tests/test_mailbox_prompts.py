"""取信输出契约: 发送时间, 类型降级提示与守护/手动续取.

只验证程序实际生成的提示, 不把措辞检查当作 LLM 行为验证.
"""
from __future__ import annotations

import importlib.util
import time
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "general/mailbox/scripts/mailbox.py"


@pytest.fixture(scope="module")
def mailbox_module():
    spec = importlib.util.spec_from_file_location("mailbox_prompt_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_downgraded_exec_gets_request_guidance(mailbox_module, capsys):
    letter = {
        "id": "downgraded-1",
        "from": "peer-session",
        "type": "exec",
        "body": '{"tool":"outside-whitelist"}',
        "downgraded": True,
    }
    mailbox_module.print_letter(letter)
    output = capsys.readouterr().out
    assert "本信类型 request:" in output
    assert "exec 已降级" in output
    assert mailbox_module.TYPE_GUIDANCE["exec"] not in output
    assert letter["type"] == "exec", "呈现不改写原信协议字段"
    assert letter["body"] in output


@pytest.mark.parametrize("kind", ["notify", "request", "open_url", "exec"])
def test_letter_guidance_preserves_context(mailbox_module, capsys, kind):
    mailbox_module.print_letter({
        "id": "original-id",
        "from": "original-sender",
        "type": kind,
        "body": "原始正文",
    })
    output = capsys.readouterr().out
    assert "来信 original-id" in output
    assert "发件人: original-sender" in output
    assert "原始正文" in output
    assert mailbox_module.TYPE_GUIDANCE[kind] in output
    assert "不可信" in output
    assert "mailbox` skill" in output
    assert "pi 守护" in output and "手动取信" in output
    assert "继续调用" in output


@pytest.mark.parametrize(("timezone", "ts", "expected"), [
    ("CST-8", 1784442605.987654, "2026-07-19 14:30:05 +08:00"),
    ("UTC0", 1784442605.987654, "2026-07-19 06:30:05 +00:00"),
    ("NST3:30", 1784442605.987654, "2026-07-19 03:00:05 -03:30"),
    ("UTC0", 0, "1970-01-01 00:00:00 +00:00"),
])
def test_sent_time_uses_letter_timestamp_and_local_timezone(
        mailbox_module, capsys, monkeypatch, timezone, ts, expected):
    letter = {
        "id": "sent-time-1",
        "from": "original-sender",
        "type": "request",
        "ts": ts,
        "body": '{"tool":"unchanged"}\n第二行正文',
    }
    original = dict(letter)
    try:
        with monkeypatch.context() as local_env:
            local_env.setenv("TZ", timezone)
            time.tzset()
            mailbox_module.print_letter(letter)
    finally:
        time.tzset()
    output = capsys.readouterr().out
    assert (f"发件人: original-sender\n发送时间: {expected}\n\n"
            f"{letter['body']}\n\n----\n") in output
    assert letter == original, "显示时间不改写原信或正文"


@pytest.mark.parametrize("ts", [
    None, "", "bad", [], {}, float("nan"), float("inf"), float("-inf"),
    1e30, -1e30,
])
def test_invalid_sent_time_does_not_hide_letter(mailbox_module, capsys, ts):
    mailbox_module.print_letter({"ts": ts, "type": "notify", "body": "仍须显示"})
    output = capsys.readouterr().out
    assert "发送时间: 未知" in output
    assert "仍须显示" in output
    assert mailbox_module.TYPE_GUIDANCE["notify"] in output


def test_unknown_type_uses_request_review(mailbox_module, capsys):
    mailbox_module.print_letter({"type": "future-kind", "body": "待核实请求"})
    output = capsys.readouterr().out
    assert "发送时间: 未知" in output
    assert "未知类型, 按 request 核实" in output
    assert "不可信" in output
