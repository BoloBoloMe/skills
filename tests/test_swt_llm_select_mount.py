"""llm-select host 数据目录只读挂载 (2026-10-07 方案 A) 的快层接缝.

接缝 = assert_llm_select_mountable 的权限/缺失判据 (软跳过不抛), 常量, 以及
create 命令组装处的条件挂载调用点; 真容器路径归 e2e (本容器无 podman).
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"


def _load():
    spec = importlib.util.spec_from_file_location("swt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt"] = module
    spec.loader.exec_module(module)
    return module


class TestLlmSelectMountable(unittest.TestCase):
    """守卫语义: 可挂返回 True; 缺失/权限不足打到 stderr 并返回 False, 不抛."""

    def setUp(self):
        self.m = _load()
        self.root = Path(tempfile.mkdtemp(prefix="swt-llm-select-"))

    def _guard(self, path: Path) -> tuple[bool, str]:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ok = self.m.assert_llm_select_mountable(path)
        return ok, err.getvalue()

    def _data_dir(self) -> Path:
        data = self.root / "llm-select"
        data.mkdir()
        (data / "llm-scores.json").write_text("{}", encoding="utf-8")
        (data / "model-catalog.json").write_text("{}", encoding="utf-8")
        return data

    def test_readable_dir_passes_without_message(self):
        ok, err = self._guard(self._data_dir())
        self.assertTrue(ok)
        self.assertEqual(err, "")

    def test_missing_dir_soft_skips_with_message(self):
        ok, err = self._guard(self.root / "absent")
        self.assertFalse(ok)
        self.assertIn("无 llm-select 数据目录", err)
        self.assertIn("不挂载", err)

    def test_file_without_other_read_soft_skips_and_names_file(self):
        data = self._data_dir()
        (data / "llm-scores.json").chmod(0o600)
        ok, err = self._guard(data)
        self.assertFalse(ok)
        self.assertIn("非全局可读", err)
        self.assertIn("llm-scores.json", err)

    def test_dir_without_other_search_soft_skips(self):
        data = self._data_dir()
        data.chmod(0o700)
        try:
            ok, err = self._guard(data)
        finally:
            data.chmod(0o755)
        self.assertFalse(ok)
        self.assertIn("非全局可读", err)

    def test_guard_never_raises(self):
        for path in (self.root / "absent", self._data_dir()):
            try:
                self.m.assert_llm_select_mountable(path)
            except Exception as exc:  # noqa: BLE001 - 断言用
                self.fail(f"守卫不应抛异常: {exc!r}")


class TestCreateCallSite(unittest.TestCase):
    """create 命令组装: 条件式只读挂载, 常量指向容器 llm-select 路径."""

    def setUp(self):
        self.m = _load()
        self.source = SCRIPT.read_text(encoding="utf-8")

    def test_constants(self):
        self.assertEqual(self.m.LLM_SELECT_CONTAINER_DIR, "/home/bolo/.agents/llm-select")
        self.assertEqual(self.m.LLM_SELECT_HOST_DIR, Path.home() / ".agents" / "llm-select")

    def test_conditional_readonly_mount(self):
        create = self.source[
            self.source.index("def create_and_start_container("):self.source.index("def inject_ssh_key(")]
        self.assertIn("if assert_llm_select_mountable(LLM_SELECT_HOST_DIR):", create)
        self.assertIn('f"{LLM_SELECT_HOST_DIR}:{LLM_SELECT_CONTAINER_DIR}:ro"', create)


if __name__ == "__main__":
    unittest.main()
