"""D021 (ISSUE-15) 取信守护标记绑定会话身份 — 生命周期回归.

经 node 原生 TS type stripping 加载 pi-extension/index.ts 导出的扩展
工厂, 假取信脚本 (tests/fixtures/fake-mailbox-python) + 假事件对象
(sessionManager.getSessionId 提供会话身份) 模拟 session_start / 命令 /
session_shutdown 生命周期, 断言 listen.json 标记与子进程行为.
场景实现: tests/fixtures/listen-mark-smoke.mjs (沿 ISSUE-07 的 jiti
人工冒烟模式, 按 ISSUE-15 评审裁决落库为可重复回归).

已知限制 (评审裁决记录, 不动): "守护进程已死" 只查内存标志, 不验
listen.json 里 pid 存活 — 跨进程残留标记由 pi_session_id 不匹配兜住.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import SCRIPT

EXT = SCRIPT.parent.parent / "pi-extension" / "index.ts"
FIXTURES = Path(__file__).parent / "fixtures"
SMOKE_MJS = FIXTURES / "listen-mark-smoke.mjs"
FAKE_PY = FIXTURES / "fake-mailbox-python"


def _node_supports_ts() -> bool:
	"""node >= 23.6 (含 22.18+) 默认启用 TS type stripping."""
	node = shutil.which("node")
	if not node:
		return False
	try:
		out = subprocess.run(
			[node, "--version"], capture_output=True, text=True, timeout=10
		).stdout.strip()
	except (OSError, subprocess.TimeoutExpired):
		return False
	m = re.match(r"v(\d+)\.(\d+)", out)
	if not m:
		return False
	major, minor = int(m.group(1)), int(m.group(2))
	return major >= 23 or (major == 22 and minor >= 18)


pytestmark = pytest.mark.skipif(
	not _node_supports_ts(), reason="需 node >= 23.6 (原生 TS type stripping) 运行扩展场景"
)

SCENARIOS = [
	("foreign-mark-no-autostart", "新会话遇他人标记: 不自动监听, 标记原样"),
	("same-session-resume", "同会话续接: 自动恢复 + shutdown 杀子留标记 (AC-003)"),
	("legacy-mark-no-autostart", "旧版无 pi_session_id: 陈旧标记不自动恢复"),
	("start-binding-stop-own", "start 写入会话绑定; stop 清自己的标记"),
	("soft-warn-takeover", "start 遇他会话标记: 软提示后接管 (D008)"),
	("takeover-legacy", "start 接管旧版陈旧标记"),
	("replacement-stop-ownership", "会话替换停遗留守护; stop 所有权 (只清自己的)"),
]


@pytest.fixture(scope="module", autouse=True)
def _fake_py_exec():
	"""exec 位随 git 走, 这里兜底 (MAILBOX_PYTHON 须可直接 spawn)."""
	FAKE_PY.chmod(0o755)


@pytest.mark.parametrize("scenario,doc", SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_listen_mark_scenario(scenario: str, doc: str, tmp_path):
	"""每个场景一个隔离 node 进程: 独立 HOME (listen.json 落地) 与取信
	调用日志, 断言场景内全部 PASS (退出码 0)."""
	env = {
		**os.environ,
		"HOME": str(tmp_path / "home"),
		"SPAWN_LOG": str(tmp_path / "spawn.log"),
		"MAILBOX_PYTHON": str(FAKE_PY),
		"LISTEN_EXT": str(EXT),
	}
	proc = subprocess.run(
		["node", str(SMOKE_MJS), scenario],
		capture_output=True,
		text=True,
		timeout=60,
		env=env,
	)
	assert proc.returncode == 0, (
		f"场景 {scenario} ({doc}) 失败:\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
	)
