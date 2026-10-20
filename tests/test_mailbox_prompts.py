"""取信输出契约: 类型提示尊重服务端降级, 区分守护与手动续取.

只验证程序实际生成的提示, 不把措辞检查当作 LLM 行为验证.
"""
from __future__ import annotations

import importlib.util
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


def test_unknown_type_uses_request_review(mailbox_module, capsys):
    mailbox_module.print_letter({"type": "future-kind", "body": "待核实请求"})
    output = capsys.readouterr().out
    assert "未知类型, 按 request 核实" in output
    assert "不可信" in output
