"""TC-01-03: 默认排除集, --exclude 追加, glob -> ccsh -e 正则转义, 单一数据源
(BR-015, m25 D019, m13 D017).

口径: 默认集 node_modules/.git/dist/build/target/vendor/.codebase-map;
--exclude 是 glob 语义, 由脚本转成正则且元字符逐字转义, 不把 glob 原样当
正则交给 ccsh; 分析侧与扫描侧取同一份集合 (collect_excludes/excluded_regexes
是唯一来源).
"""
from __future__ import annotations

import re

from codemap_helpers import codemap_common as cmc


def test_default_exclude_set_verbatim_and_ordered():
    """默认排除集与 BR-015 逐字一致, 顺序稳定 (顺序进 ccsh 参数与统计归因)."""
    assert cmc.DEFAULT_EXCLUDES == (
        "node_modules", ".git", "dist", "build", "target", "vendor",
        ".codebase-map",
    )


def test_user_excludes_append_after_defaults_and_dedupe():
    """--exclude 追加在默认集之后, 重复项保序去重."""
    assert cmc.collect_excludes(["docs/generated", "vendor"]) == (
        "node_modules", ".git", "dist", "build", "target", "vendor",
        ".codebase-map", "docs/generated",
    )


def test_glob_metacharacters_escaped_verbatim():
    """元字符逐字转义: * ? + . 等都不再是正则元字符 (m25 D019)."""
    assert cmc.glob_to_ccsh_regex("test*") == r"test\*"
    assert cmc.glob_to_ccsh_regex("a.b?") == r"a\.b\?"
    assert cmc.glob_to_ccsh_regex("plus+") == r"plus\+"


def test_escaped_regex_matches_literal_not_glob_expansion():
    """转义后按字面匹配: glob 的 * 不展开为正则任意串."""
    rx = re.compile(cmc.glob_to_ccsh_regex("build*"))
    assert rx.search("xbuild*") is not None
    assert rx.search("buildfoo") is None


def test_excluded_regexes_derive_from_single_source():
    """正则形态完全由 collect_excludes 推导, 两次取值一致 (无状态), 默认集
    在前用户项在后 -- 分析侧与扫描侧都从这里取同一份 (BR-015)."""
    user = ["gen"]
    globs = cmc.collect_excludes(user)
    regexes = cmc.excluded_regexes(user)
    assert regexes == tuple(cmc.glob_to_ccsh_regex(g) for g in globs)
    assert cmc.excluded_regexes(user) == regexes
    head = len(cmc.DEFAULT_EXCLUDES)
    assert regexes[:head] == tuple(
        cmc.glob_to_ccsh_regex(g) for g in cmc.DEFAULT_EXCLUDES)
    assert regexes[head:] == (r"gen",)
