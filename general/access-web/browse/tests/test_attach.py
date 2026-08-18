"""attach 模块测试: 只读会话视图 (probe / attached_context).

conftest 夹具把每个测试的 cwd 切到独立临时目录并在结束后清理,
因此 probe() / attached_context() 均走默认 cwd 绑定即可.
单元测试部分用假 metadata + 模拟探测/连接, 不启动浏览器.
"""

from unittest import mock

import pytest

from browser_agent import attached_context
from browser_agent import probe
from browser_agent import SessionProbe
from browser_agent.config import BrowserConfig
from browser_agent.session import get_session


def _write_meta(data) -> BrowserConfig:
    config = BrowserConfig()
    config.session_root.mkdir(parents=True, exist_ok=True)
    config.write_metadata(data)
    return config


# ── probe (无浏览器) ─────────────────────────────────────────


def test_probe_no_metadata_is_dead_and_side_effect_free():
    """无 browser.json: 不存活, 字段为 None, 且不创建任何目录."""
    config = BrowserConfig()
    assert not config.browser_json.exists()

    p = probe()

    assert isinstance(p, SessionProbe)
    assert p.alive is False
    assert p.pid is None
    assert p.cdp_port is None
    assert p.profile_dir is None
    assert not config.session_root.exists()


def test_probe_non_dict_metadata_is_dead():
    """metadata 不是 dict: 视为不存活."""
    _write_meta([1, 2, 3])
    assert probe().alive is False


def test_probe_corrupt_pid_port_values():
    """畸形 pid/端口一律视为不存活 (含 bool, 它是 int 子类)."""
    corrupt = [
        {"pid": "not-a-pid", "cdp_port": 9222},
        {"pid": -1, "cdp_port": 9222},
        {"pid": 1234, "cdp_port": 0},
        {"pid": 1234, "cdp_port": 70000},
        {"pid": True, "cdp_port": 9222},
        {"pid": 1234, "cdp_port": True},
        {"pid": 1234},
        {"cdp_port": 9222},
    ]
    for meta in corrupt:
        _write_meta(meta)
        p = probe()
        assert p.alive is False, meta
        # metadata 摘录仍回传, 供调用方诊断
        assert p.pid == meta.get("pid")
        assert p.cdp_port == meta.get("cdp_port")


def test_probe_dead_pid_and_closed_port():
    """pid 不存在且端口关闭: 不存活."""
    _write_meta({"pid": 999999, "cdp_port": 59999})
    assert probe().alive is False


def test_probe_double_check_both_required():
    """双检语义: pid 与端口任一不活即为不存活."""
    _write_meta({"pid": 1234, "cdp_port": 9222})
    with mock.patch(
        "browser_agent.attach.is_pid_alive", return_value=True
    ), mock.patch("browser_agent.attach.is_port_open", return_value=False):
        assert probe().alive is False
    with mock.patch(
        "browser_agent.attach.is_pid_alive", return_value=False
    ), mock.patch("browser_agent.attach.is_port_open", return_value=True):
        assert probe().alive is False
    with mock.patch(
        "browser_agent.attach.is_pid_alive", return_value=True
    ), mock.patch("browser_agent.attach.is_port_open", return_value=True):
        p = probe()
        assert p.alive is True
        assert p.pid == 1234
        assert p.cdp_port == 9222


# ── attached_context (playwright 打模拟) ─────────────────────


def _mock_playwright(contexts):
    mock_browser = mock.MagicMock()
    mock_browser.contexts = contexts
    mock_pw = mock.MagicMock()
    mock_pw.chromium.connect_over_cdp.return_value = mock_browser
    # sync_playwright() 作上下文管理器使用, __enter__ 返回自身
    mock_pw.__enter__.return_value = mock_pw
    mock_pw.__exit__.return_value = False
    return mock_pw, mock_browser


def _patch_alive(mock_pw):
    return [
        mock.patch("browser_agent.attach.is_pid_alive", return_value=True),
        mock.patch("browser_agent.attach.is_port_open", return_value=True),
        mock.patch("playwright.sync_api.sync_playwright", return_value=mock_pw),
    ]


def test_attached_context_not_alive_yields_none():
    """会话未存活: yield None, 不尝试连接."""
    with attached_context() as context:
        assert context is None


def test_attached_context_connects_and_never_closes():
    """存活会话: 经 CDP 附加并 yield 默认 context; 绝不调用 browser.close()."""
    _write_meta({"pid": 1234, "cdp_port": 9222})
    mock_context = mock.MagicMock()
    mock_pw, mock_browser = _mock_playwright([mock_context])

    patches = _patch_alive(mock_pw)
    for p in patches:
        p.start()
    try:
        with attached_context() as context:
            assert context is mock_context
    finally:
        for p in patches:
            p.stop()

    mock_pw.chromium.connect_over_cdp.assert_called_once_with(
        "http://127.0.0.1:9222"
    )
    mock_browser.close.assert_not_called()


def test_attached_context_no_contexts_yields_none():
    """存活但无 context: yield None (区别于连接失败, 不抛异常)."""
    _write_meta({"pid": 1234, "cdp_port": 9222})
    mock_pw, mock_browser = _mock_playwright([])

    patches = _patch_alive(mock_pw)
    for p in patches:
        p.start()
    try:
        with attached_context() as context:
            assert context is None
    finally:
        for p in patches:
            p.stop()
    mock_browser.close.assert_not_called()


def test_attached_context_connect_failure_propagates():
    """CDP 连接失败: 异常透传, 由调用方决定语义."""
    _write_meta({"pid": 1234, "cdp_port": 9222})
    mock_pw, _mock_browser = _mock_playwright([])
    mock_pw.chromium.connect_over_cdp.side_effect = Exception("refused")

    patches = _patch_alive(mock_pw)
    for p in patches:
        p.start()
    try:
        with pytest.raises(Exception, match="refused"):
            with attached_context():
                pass
    finally:
        for p in patches:
            p.stop()


# ── 真实浏览器集成 (conftest 夹具隔离 session) ───────────────


def test_attach_real_session_readonly():
    """附加真实存活会话: 可读页面状态, 附加结束后远端浏览器仍存活."""
    page = get_session().page
    page.set_content(
        "<html><head><title>Attach Page</title></head>"
        "<body><script>window.__X__ = {v: 1};</script></body></html>"
    )
    meta = BrowserConfig().read_metadata()

    p = probe()
    assert p.alive is True
    assert p.pid == meta["pid"]
    assert p.cdp_port == meta["cdp_port"]

    # 释放进程内句柄, 模拟外部观察进程视角 (避免嵌套 sync_playwright 事件循环)
    get_session().stop()

    with attached_context() as context:
        assert context is not None
        assert context.pages
        assert context.pages[0].evaluate("window.__X__") == {"v": 1}

    # 附加结束后远端浏览器仍存活
    assert probe().alive is True
