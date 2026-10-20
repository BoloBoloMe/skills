"""D022 每会话独立信箱 — 取信守护生命周期与 mailbox_listen 工具回归.

经 node 原生 TS type stripping 加载 pi-extension/index.ts 导出的扩展
工厂, 假取信脚本 (tests/pi/mailbox/fake-mailbox-python) + 假事件对象
(sessionManager.getSessionId 提供会话身份) 模拟 session_start / 命令 /
工具调用 / session_shutdown 生命周期, 断言各会话独立 config/cli-state/
listen 标记与子进程行为.

场景实现: tests/pi/mailbox/listen-smoke.mjs. 取代 D008/D021 的全局单标记
+ 多会话软提示: 不同 id 用独立文件, 同 id 多窗口各自自启/关闭, 不加单窗口限制.
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
FIXTURES = Path(__file__).parent / "pi" / "mailbox"
SMOKE_MJS = FIXTURES / "listen-smoke.mjs"
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

CONTAINER_ENV = {
	"SWT_MAILBOX_URL": "http://127.0.0.1:1",
	"SWT_SESSION_ID": "container-deadbeef",
	"SWT_SESSION_SIGNING_KEY": "fake-signing",
	"SWT_SESSION_RESPONSE_KEY": "fake-response",
}

SCENARIOS = [
	("no-mark-autostart", "新会话无记录: 自动取信, 关闭即停止", {}),
	("same-session-two-windows", "同 id 多窗口均自启, 关闭只停自己的客户端", {}),
	("same-session-two-windows", "容器内同 id 多窗口各自取信", CONTAINER_ENV),
	("auto-start-shutdown-pending", "自启过程中关闭会话: 取消取信启动", {"FAKE_ENSURE_SLEEP": "1"}),
	("same-session-resume", "本会话独立标记: 自动恢复 + shutdown 杀子留标记", {}),
	("legacy-mark-migrate", "旧版全局标记属本会话: 迁移到本会话路径", {}),
	("legacy-stale-autostart", "旧版陈旧记录不影响当前会话自启", {}),
	("tool-start-status-stop", "mailbox_listen 工具 start/status/stop 返回双 id", {}),
	("multi-session-isolation", "两会话进程独立: 标记/子进程/stop 互不覆盖不串信", {}),
	("ensure-failure-no-autostart", "ensure-session 失败: 不启动, isError 明确报错", {"FAKE_FAIL": "1"}),
	("container-independent-pi", "容器: pi 独立身份, 接线仅用于注册", CONTAINER_ENV),
	("no-mark-autostart", "容器新 pi 自动取信/关闭", CONTAINER_ENV),
	("multi-session-isolation", "同容器两个 pi 独立收信", CONTAINER_ENV),
	("same-session-resume", "容器同一 pi 会话恢复身份不变", CONTAINER_ENV),
	("ensure-failure-no-autostart", "容器旧服务不可注册时不回退", {**CONTAINER_ENV, "FAKE_FAIL": "1"}),
	("ensure-failure-no-autostart", "注册返回错误 id 时不启动或回退", {**CONTAINER_ENV, "FAKE_WRONG_ID": "1"}),
	("session-switch-restart", "同进程会话替换 A→B 都有标记: 先停 A 再恢复 B", {}),
	("stop-then-start-no-stale-stop", "stop 后立即 start: 旧 close 不停新守护", {}),
	("concurrent-start-single-poll", "同会话并发 start: 复用 Promise 只起一个 poll", {}),
	("pending-start-cancelled", "启动进行中 stop: 取消在启, 不起 poll 不写标记", {"FAKE_ENSURE_SLEEP": "1"}),
	("switch-clears-old-env", "会话切换 A(已启)→B(无标记): 停 A 并清 env 不复用凭据", {}),
	("pending-A-then-marked-B", "启动中 A→已标记 B: 取消 A 旧尝试, B 能恢复", {"FAKE_ENSURE_SLEEP": "1"}),
	("pending-stop-then-start-same-sid", "启动中 stop 后立即同 sid start: 新尝试不被误清", {"FAKE_ENSURE_SLEEP": "1"}),
]


@pytest.fixture(scope="module", autouse=True)
def _fake_py_exec():
	"""exec 位随 git 走, 这里兜底 (MAILBOX_PYTHON 须可直接 spawn)."""
	FAKE_PY.chmod(0o755)


@pytest.mark.parametrize(
	"scenario,doc,extra_env", SCENARIOS, ids=[s[0] for s in SCENARIOS]
)
def test_listen_mark_scenario(scenario: str, doc: str, extra_env: dict, tmp_path):
	"""每个场景一个隔离 node 进程: 独立 HOME (会话文件落地) 与取信调用日志,
	断言场景内全部 PASS (退出码 0)."""
	env = {
		**{k: v for k, v in os.environ.items() if k not in CONTAINER_ENV},
		"HOME": str(tmp_path / "home"),
		"SPAWN_LOG": str(tmp_path / "spawn.log"),
		"MAILBOX_PYTHON": str(FAKE_PY),
		"LISTEN_EXT": str(EXT),
		**(extra_env or {}),
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


TOOL_SCHEMA_MJS = FIXTURES / "tool-schema-smoke.mjs"


def _pi_shim() -> str | None:
	"""定位 pi 可执行 shim (用其 cmd-shim-target 找 pi 包目录下的 typebox)."""
	return shutil.which("pi")


@pytest.mark.skipif(
	not _pi_shim(), reason="需 pi 可执行 (定位其自带 typebox/compile 校验器)"
)
def test_mailbox_listen_tool_schema_smoke(tmp_path):
	"""真实校验器冒烟: 用 pi 自带 typebox/compile 编译 mailbox_listen 的
	parameters (普通 JSON Schema), 验证合法参数通过/非法被拒. 不调模型,
	不连真实 mailbox."""
	proc = subprocess.run(
		["node", str(TOOL_SCHEMA_MJS)],
		capture_output=True,
		text=True,
		timeout=60,
		env={**os.environ, "PI_SHIM": _pi_shim(), "LISTEN_EXT": str(EXT)},
	)
	assert proc.returncode == 0, (
		f"工具 schema 冒烟失败:\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
	)
