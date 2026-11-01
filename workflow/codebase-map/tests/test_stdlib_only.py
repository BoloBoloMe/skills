"""TC-01-05: 静态守卫 -- workflow/codebase-map/scripts/*.py 只 import 标准库
(BR-033, m25 D012/D014).

口径: 按 import 行 ast 解析, 不执行脚本. 禁止的是第三方依赖; TECHNICAL
"接缝与依赖" 定义的内部接缝允许 CLI 调同目录共享模块, 故白名单恰好三个:
codemap_common / codemap_analyze / codemap_service (后两者由后续 issue 落地,
被实际 import 时必须已存在于同目录). 其余非标准库导入一律判失败.
先例: workflow/navigate/tests/test_stdlib_only_and_no_external_refs.py.
"""
from __future__ import annotations

import ast
import sys

from codemap_helpers import SCRIPTS_DIR

IN_TREE_ALLOWED = {"codemap_common", "codemap_analyze", "codemap_service"}


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


def test_scripts_import_only_stdlib_or_in_tree_modules():
    scripts = sorted(SCRIPTS_DIR.glob("*.py"))
    assert scripts, f"未找到脚本: {SCRIPTS_DIR}"
    for script in scripts:
        modules = imported_top_level_modules(script)
        bad = sorted(
            m for m in modules
            if m not in sys.stdlib_module_names and m not in IN_TREE_ALLOWED
        )
        assert bad == [], f"{script.name} 引入非标准库且不在白名单的模块: {bad}"
        for name in modules & IN_TREE_ALLOWED:
            assert (SCRIPTS_DIR / f"{name}.py").is_file(), (
                f"{script.name} import 的 {name} 不在同目录 scripts/ 下")
