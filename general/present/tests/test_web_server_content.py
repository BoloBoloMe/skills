"""web_server.py 内容访问测试 (ISSUE-06, TC-016..TC-021).

Seam 3 (真实 HTTP GET, 端到端): 扁平并集查找, 顶层 listing 并集去重,
子目录 listing, resolve+containment 路径防护.
"""

import http.client
import json
import os
import time
import unittest
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

from general.present.tests.test_web_server_lifecycle import (
    WebServerLifecycleTestCase,
)


class TestTC016FlatUnionLaterMount(WebServerLifecycleTestCase):
    """TC-016: 两挂载目录, 文件只在后挂载目录 -> GET 返回该文件 (AC-005)."""

    def test_file_only_in_later_mount_is_served(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("aaa", encoding="utf-8")
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "b.txt").write_text("bbb", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        add_obj, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(add_obj["success"])

        # 文件只存在于后挂载目录: 扁平并集查找须命中它
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/b.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "bbb")


class TestTC017FlatUnionShadowing(WebServerLifecycleTestCase):
    """TC-017: 两挂载目录含同名文件 -> 返回先挂载那份 (D008 静默遮蔽, AC-005)."""

    def test_duplicate_name_served_from_first_mount(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "dup.txt").write_text("from-root1", encoding="utf-8")
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "dup.txt").write_text("from-root2", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        add_obj, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(add_obj["success"])

        # 同名冲突: 先挂载者优先, 静默遮蔽
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/dup.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "from-root1")


class TestTC018TopLevelListingUnion(WebServerLifecycleTestCase):
    """TC-018: 两目录顶层有同名与异名条目 -> GET / 返回并集且去重 (D007/D008)."""

    def test_top_level_listing_is_deduplicated_union(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("from-root1", encoding="utf-8")
        (root1 / "dup.txt").write_text("from-root1", encoding="utf-8")
        (root1 / "r1dir").mkdir()
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "b.txt").write_text("from-root2", encoding="utf-8")
        (root2 / "dup.txt").write_text("from-root2", encoding="utf-8")
        (root2 / "r2dir").mkdir()
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        add_obj, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(add_obj["success"])

        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/")
        self.assertEqual(status, 200)
        # 并集: 各目录的异名条目全部出现, 目录条目带 / 后缀
        for name in ("a.txt", "b.txt", "r1dir/", "r2dir/"):
            self.assertIn(f'href="{name}"', body, f"missing entry {name}")
        # 去重: 同名条目只出现一次 (先挂载者优先, 无遮蔽提示)
        self.assertEqual(body.count('href="dup.txt"'), 1)


class TestTC019DotDotEscape(WebServerLifecycleTestCase):
    """TC-019: 含 ../ 的逃逸路径 -> 404, 不暴露挂载目录外内容 (D022)."""

    def test_dotdot_escape_outside_mount_returns_404(self):
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "a.txt").write_text("aaa", encoding="utf-8")
        # 逃逸目标: 挂载目录外、运行时同级的秘密文件
        outside = Path(self._tmpdir.name) / "escape.txt"
        outside.write_text("secret", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        # 先确认服务就绪 (正向内容可达)
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/a.txt")
        self.assertEqual(status, 200)

        # http.client 发原始路径, 客户端不做规范化, 确保服务端收到 ../
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            conn.request("GET", "/../escape.txt")
            resp = conn.getresponse()
            resp.read()
            self.assertEqual(resp.status, 404)
        finally:
            conn.close()


class TestTC020SymlinkOutside(WebServerLifecycleTestCase):
    """TC-020: 命中文件是指向挂载目录外的 symlink -> 404 (D022)."""

    def test_symlink_pointing_outside_mount_returns_404(self):
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "a.txt").write_text("aaa", encoding="utf-8")
        outside = Path(self._tmpdir.name) / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        link = root / "link.txt"
        link.symlink_to(outside)
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/a.txt")
        self.assertEqual(status, 200)

        with self.assertRaises(HTTPError) as ctx:
            request.urlopen(f"http://127.0.0.1:{port}/link.txt", timeout=2)
        self.assertEqual(ctx.exception.code, 404)


class TestTC021SubdirListing(WebServerLifecycleTestCase):
    """TC-021: 挂载目录内存有子目录 -> GET 目录路径返回该目录自身 listing (D007/BR-004)."""

    def test_subdir_path_returns_own_listing_not_union(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "top.txt").write_text("top", encoding="utf-8")
        sub = root1 / "sub"
        sub.mkdir()
        (sub / "inner.txt").write_text("inner", encoding="utf-8")
        (sub / "nested").mkdir()
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "other.txt").write_text("other", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        add_obj, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(add_obj["success"])

        # 子目录 listing: 该目录自身条目, 目录条目带 / 后缀
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/sub/")
        self.assertEqual(status, 200)
        self.assertIn('href="inner.txt"', body)
        self.assertIn('href="nested/"', body)
        # 非并集: 挂载顶层与另一目录的条目不出现
        self.assertNotIn("top.txt", body)
        self.assertNotIn("other.txt", body)


def _raw_get(port, path, timeout=2):
    """http.client 发原始路径 (客户端不做规范化), 返回 (status, body_str)."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        return resp.status, resp.read().decode("utf-8")
    finally:
        conn.close()


class TestR1UnreadableTopListing(WebServerLifecycleTestCase):
    """U-008/R1: 顶层 listing 不可读语义收口.

    部分挂载目录不可读 -> 可读子集 200; 全部不可读 -> 404
    (恢复单目录时代 "不可读不泄露存在性" 语义).
    """

    def test_all_mounts_unreadable_returns_404(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("aaa", encoding="utf-8")
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "b.txt").write_text("bbb", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        add_obj, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(add_obj["success"])

        # 全部挂载目录不可读 (chmod 000, 同 uid 属主 listdir 抛 OSError):
        # 顶层 listing 须 404, 不以空 listing 泄露/混淆存在性
        try:
            os.chmod(root1, 0)
            os.chmod(root2, 0)
            status, body = _raw_get(port, "/")
            self.assertEqual(status, 404)
        finally:
            os.chmod(root1, 0o755)
            os.chmod(root2, 0o755)

    def test_partial_unreadable_returns_readable_subset(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("aaa", encoding="utf-8")
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "b.txt").write_text("bbb", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        add_obj, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(add_obj["success"])

        # 部分挂载目录不可读: 顶层 listing = 可读目录条目子集, 200
        try:
            os.chmod(root1, 0)
            status, body = _raw_get(port, "/")
            self.assertEqual(status, 200)
            self.assertIn('href="b.txt"', body)
            self.assertNotIn("a.txt", body)
        finally:
            os.chmod(root1, 0o755)


class TestR2NonCanonicalTopPathUnionListing(WebServerLifecycleTestCase):
    """审核 R2: resolve 后等于挂载根的非规范顶层路径 (/. , /a/../ 等)
    与 / 同义, 走各挂载目录条目并集 listing 分支 (D007/D008).
    """

    def test_dot_and_dotdot_to_root_return_union_listing(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("aaa", encoding="utf-8")
        (root1 / "sub").mkdir()
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "b.txt").write_text("bbb", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        add_obj, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(add_obj["success"])

        # 原始路径经 http.client 直发, 客户端不规范化
        for raw_path in ("/.", "/sub/../"):
            status, body = _raw_get(port, raw_path)
            self.assertEqual(status, 200, f"path={raw_path}")
            # 并集: 各挂载目录的条目全部出现, 而非首目录单列
            self.assertIn('href="a.txt"', body, f"path={raw_path}")
            self.assertIn('href="b.txt"', body, f"path={raw_path}")
            self.assertIn('href="sub/"', body, f"path={raw_path}")


if __name__ == "__main__":
    unittest.main()
