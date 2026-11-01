"""TC-01-01: 数据键命名与清洗 (BR-011/BR-032, m25 D005; PRODUCT AC-005 键场景).

纯函数接缝 (内部): 直接 import codemap_common, 不经 CLI.

口径: 键 = <清洗库名>-<realpath sha256 前 8 位>.cc.json; 空白与
[^A-Za-z0-9._-] 逐个换 -, 连续 - 折叠, 首尾 - 去掉, 空则 repo;
同一 realpath 恒同键 (含软链), 不同 realpath 键不同, 键只含
[A-Za-z0-9._-].
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from codemap_helpers import codemap_common as cmc

_STEM_SUFFIX = ".cc.json"


def _name_part(key: str) -> str:
    """从键里取清洗后的库名部分 (末尾固定是 -<8 位哈希>)."""
    return key[: -len(_STEM_SUFFIX)].rsplit("-", 1)[0]


def test_demo_app_key_shape_and_hash(tmp_path):
    """AC-005: 'Demo App' -> 'Demo-App-<8 位十六进制>.cc.json', 空格换成 -."""
    target = tmp_path / "Demo App"
    target.mkdir()
    key = cmc.data_key(target)
    expected_hash = hashlib.sha256(
        str(target.resolve()).encode("utf-8")).hexdigest()[:8]
    assert key == f"Demo-App-{expected_hash}.cc.json"
    assert key.startswith("Demo-App-") and key.endswith(_STEM_SUFFIX)


def test_illegal_chars_replaced_one_by_one_and_collapsed(tmp_path):
    """非法字符逐个换 -, 连续 - 折叠 (点与下划线属合法保留)."""
    target = tmp_path / "a b--c++d.e"
    target.mkdir()
    assert _name_part(cmc.data_key(target)) == "a-b-c-d.e"


def test_leading_and_trailing_dashes_stripped(tmp_path):
    """清洗结果的首尾 - 去掉."""
    target = tmp_path / "-weird-name-"
    target.mkdir()
    assert _name_part(cmc.data_key(target)) == "weird-name"


def test_empty_cleaned_name_falls_back_to_repo(tmp_path):
    """清洗后为空 (如纯中文名) 回退 repo; realpath '/' 的 basename 为空同理."""
    target = tmp_path / "中文"
    target.mkdir()
    assert cmc.data_key(target).startswith("repo-")
    assert cmc.data_key("/").startswith("repo-")


def test_same_realpath_same_key_including_symlink(tmp_path):
    """同一 realpath 恒同键; 软链进同一目录必须得到同一键 (取 realpath)."""
    real = tmp_path / "real-lib"
    real.mkdir()
    link = tmp_path / "link-to-lib"
    link.symlink_to(real, target_is_directory=True)
    assert cmc.data_key(real) == cmc.data_key(real)
    assert cmc.data_key(real) == cmc.data_key(link)


def test_different_realpath_different_key_even_same_basename(tmp_path):
    """同名不同库不互相覆盖: basename 相同, realpath 不同, 键不同."""
    one = tmp_path / "one" / "demo"
    two = tmp_path / "two" / "demo"
    one.mkdir(parents=True)
    two.mkdir(parents=True)
    key_one, key_two = cmc.data_key(one), cmc.data_key(two)
    assert key_one != key_two
    assert _name_part(key_one) == "demo" and _name_part(key_two) == "demo"


def test_key_charset_restricted(tmp_path):
    """键只含 [A-Za-z0-9._-], 无论目标目录名多离谱."""
    target = tmp_path / "s p a c e + & # 中文 . ."
    target.mkdir()
    key = cmc.data_key(target)
    allowed = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789._-"
    )
    assert set(key) <= allowed


def test_hash_is_sha256_of_realpath_utf8_first8(tmp_path):
    """哈希取 realpath 字节 (utf-8) 的 sha256 前 8 位, 独立复算核对."""
    target = tmp_path / "hashy"
    target.mkdir()
    key = cmc.data_key(target)
    expected = hashlib.sha256(
        str(Path(target).resolve()).encode("utf-8")).hexdigest()[:8]
    assert key.endswith(f"-{expected}{_STEM_SUFFIX}")
