"""ISSUE-07 TS-001 / TC-102: BR-006 依赖审计 (静态检查).

接缝: workflow/navigate 的脚本文件内容与 SPA 文件内容.
用例:
  - scripts/*.py 全部 import 的顶层模块名属 Python 标准库 (零第三方依赖).
  - web/index.html 无任何外部 http(s) src/href 引用 (零 CDN, 零构建).

不得测试文档文字内容.
"""
from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

NAVIGATE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = NAVIGATE_DIR / "scripts"
INDEX_HTML = NAVIGATE_DIR / "web" / "index.html"

# 匹配外部引用: src/href 指向 http(s):// 或协议相对 //.
EXTERNAL_REF_RE = re.compile(
    r"""(?ix)\b(?:src|href)\s*=\s*["']?\s*(?:https?:)?//""")


def imported_top_level_modules(py_path):
    """解析单文件全部 import 语句, 返回顶层模块名集合 (相对 import 不计)."""
    tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules.add(node.module.split(".")[0])
    return modules


class StdlibOnlyAndNoExternalRefsTests(unittest.TestCase):
    def test_scripts_import_only_stdlib(self):
        scripts = sorted(SCRIPTS_DIR.glob("*.py"))
        self.assertTrue(scripts, f"未找到脚本: {SCRIPTS_DIR}")
        for script in scripts:
            with self.subTest(script=script.name):
                non_stdlib = sorted(
                    m for m in imported_top_level_modules(script)
                    if m not in sys.stdlib_module_names
                )
                self.assertEqual(
                    non_stdlib, [],
                    f"{script.name} 引入非标准库模块: {non_stdlib}")

    def test_index_html_has_no_external_src_or_href(self):
        self.assertTrue(INDEX_HTML.is_file(), f"未找到页面: {INDEX_HTML}")
        hits = EXTERNAL_REF_RE.findall(INDEX_HTML.read_text(encoding="utf-8"))
        self.assertEqual(hits, [], f"index.html 存在外部引用: {hits}")


if __name__ == "__main__":
    unittest.main()
