"""web_server.py 控制面安全测试 (ISSUE-07, TC-022/TC-023).

Seam 4 (真实 HTTP, 经本机 LAN IP 模拟非 loopback 来源, 端到端):
/__control__/* 全命名空间仅 loopback 来源放行; 静态内容面不受来源限制 (D001).
探测不到非 loopback IPv4 接口时 skip 不 fail.
"""

import ipaddress
import json
import socket
import unittest
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

from general.present.tests.test_web_server_lifecycle import (
    WebServerLifecycleTestCase,
)


def _probe_lan_ipv4():
    """探测本机非 loopback IPv4 (UDP connect 惯用法, 不发包); 探测不到返回 None."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
    except OSError:
        return None
    if ipaddress.ip_address(ip).is_loopback:
        return None
    return ip


class ControlPlaneTestCase(WebServerLifecycleTestCase):
    """TC-022/TC-023 公共: skip 探测 + 裸 HTTP 请求助手 + 0.0.0.0 启动."""

    def _skip_if_no_lan(self):
        if _probe_lan_ipv4() is None:
            self.skipTest("本机探测不到非 loopback IPv4 接口, 无法模拟非 loopback 来源")

    def _request(self, url, method="GET", data=None):
        """发请求, 返回 (status, body); 4xx/5xx 不抛异常."""
        req = request.Request(url, data=data, method=method)
        try:
            with request.urlopen(req, timeout=2) as resp:
                return resp.getcode(), resp.read().decode("utf-8")
        except HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def _start_bind_any(self, root, port):
        """以 bind 0.0.0.0 起服务并等 loopback ping 就绪."""
        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "0.0.0.0"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])
        # 就绪等待走 loopback (控制面对 loopback 放行)
        self._wait_for_url(f"http://127.0.0.1:{port}/__control__/ping")
        return sj


class TestTC022ControlPlaneLoopbackOnly(ControlPlaneTestCase):
    """TC-022: bind 0.0.0.0, 经本机 LAN IP 请求 /__control__/* 一律拒绝 (AC-004, BR-006)."""

    def test_ping_and_add_dir_via_lan_ip_rejected(self):
        self._skip_if_no_lan()
        lan_ip = _probe_lan_ipv4()
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "a.txt").write_text("aaa", encoding="utf-8")
        private_root = Path(self._tmpdir.name) / "private"
        private_root.mkdir()
        (private_root / "secret.txt").write_text("secret", encoding="utf-8")
        port = self._free_port("0.0.0.0")
        self._start_bind_any(root, port)

        # GET ping 经 LAN IP -> 拒绝
        status, _ = self._request(f"http://{lan_ip}:{port}/__control__/ping")
        self.assertEqual(status, 403)

        # GET 未知控制路径经 LAN IP -> 拒绝 (/__control__/ 全命名空间)
        status, _ = self._request(f"http://{lan_ip}:{port}/__control__/anything")
        self.assertEqual(status, 403)

        # POST add-dir 经 LAN IP -> 拒绝
        body = json.dumps({"dir": str(private_root.resolve())}).encode("utf-8")
        status, _ = self._request(
            f"http://{lan_ip}:{port}/__control__/add-dir", method="POST", data=body
        )
        self.assertEqual(status, 403)

        # 拒绝不得执行控制语义: ping 仍存活, roots 未变, private 内容不可达
        with request.urlopen(
            f"http://127.0.0.1:{port}/__control__/ping", timeout=2
        ) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(payload["service"], "pi-present-web")
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self.assertEqual(sj["roots"], [str(root.resolve())])
        status, _ = self._request(f"http://127.0.0.1:{port}/secret.txt")
        self.assertEqual(status, 404)

    def test_shadow_file_via_lan_ip_rejected_with_json_body(self):
        """R2/S1(a): 挂载内真实 __control__/shadow.txt, LAN GET -> 403 JSON body.

        保留命名空间优先于静态查找: 同路径文件不被经 LAN 提供.
        """
        self._skip_if_no_lan()
        lan_ip = _probe_lan_ipv4()
        root = Path(self._tmpdir.name) / "root"
        shadow_dir = root / "__control__"
        shadow_dir.mkdir(parents=True)
        (shadow_dir / "shadow.txt").write_text("shadowed", encoding="utf-8")
        port = self._free_port("0.0.0.0")
        self._start_bind_any(root, port)

        status, body = self._request(f"http://{lan_ip}:{port}/__control__/shadow.txt")
        self.assertEqual(status, 403)
        payload = json.loads(body)
        self.assertFalse(payload["success"])
        self.assertTrue(payload.get("error"))

    def test_exact_control_path_via_lan_ip_rejected(self):
        """R2/S1(b): GET /__control__ (精确无尾斜线) LAN -> 403."""
        self._skip_if_no_lan()
        lan_ip = _probe_lan_ipv4()
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "a.txt").write_text("aaa", encoding="utf-8")
        port = self._free_port("0.0.0.0")
        self._start_bind_any(root, port)

        status, body = self._request(f"http://{lan_ip}:{port}/__control__")
        self.assertEqual(status, 403)
        self.assertFalse(json.loads(body)["success"])


class TestU010ReservedNamespaceLoopback(ControlPlaneTestCase):
    """U-010/R3: /__control__/* 保留命名空间, loopback 下不回落静态查找."""

    def test_unknown_control_path_via_loopback_returns_404(self):
        # 挂载内真实 __control__/shadow.txt, loopback GET -> 404 (现状 200 回落静态, 红)
        root = Path(self._tmpdir.name) / "root"
        shadow_dir = root / "__control__"
        shadow_dir.mkdir(parents=True)
        (shadow_dir / "shadow.txt").write_text("shadowed", encoding="utf-8")
        port = self._free_port("0.0.0.0")
        self._start_bind_any(root, port)

        status, _ = self._request(f"http://127.0.0.1:{port}/__control__/shadow.txt")
        self.assertEqual(status, 404)

        # 已定义端点路由不变: ping 仍 200
        status, body = self._request(f"http://127.0.0.1:{port}/__control__/ping")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["service"], "pi-present-web")

    def test_exact_and_nested_unknown_control_paths_via_loopback_404(self):
        # 精确 /__control__ 与未知深层路径 loopback -> 一律 404, 不暴露静态面
        root = Path(self._tmpdir.name) / "root"
        shadow_dir = root / "__control__"
        shadow_dir.mkdir(parents=True)
        (shadow_dir / "shadow.txt").write_text("shadowed", encoding="utf-8")
        (root / "a.txt").write_text("aaa", encoding="utf-8")
        port = self._free_port("0.0.0.0")
        self._start_bind_any(root, port)

        status, _ = self._request(f"http://127.0.0.1:{port}/__control__")
        self.assertEqual(status, 404)
        status, _ = self._request(f"http://127.0.0.1:{port}/__control__/no/such/thing")
        self.assertEqual(status, 404)
        # 静态面不受影响
        status, body = self._request(f"http://127.0.0.1:{port}/a.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "aaa")


class TestTC023StaticContentViaLanIp(ControlPlaneTestCase):
    """TC-023: bind 0.0.0.0, 经本机 LAN IP 请求静态内容/顶层 listing 正常 (D001 兑现)."""

    def test_static_content_via_lan_ip_served(self):
        self._skip_if_no_lan()
        lan_ip = _probe_lan_ipv4()
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "a.txt").write_text("aaa", encoding="utf-8")
        (root / "sub").mkdir()
        (root / "sub" / "b.txt").write_text("bbb", encoding="utf-8")
        port = self._free_port("0.0.0.0")
        self._start_bind_any(root, port)

        # 静态文件经 LAN IP -> 200 且内容正确
        status, body = self._request(f"http://{lan_ip}:{port}/a.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "aaa")

        # 子目录文件经 LAN IP -> 200
        status, body = self._request(f"http://{lan_ip}:{port}/sub/b.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "bbb")

        # 顶层 listing 经 LAN IP -> 200
        status, _ = self._request(f"http://{lan_ip}:{port}/")
        self.assertEqual(status, 200)


class TestU009BindSpecificIpControlPlane(ControlPlaneTestCase):
    """U-009/R1: bind 本机 LAN IP 时, 源==bind 的本机控制流放行.

    start 就绪 ping / status 探活 / add-dir 端点 (源 IP == bind 地址)
    不被守卫拒绝; bind 0.0.0.0/127.0.0.1 行为不变 (TC-022 不回归).
    """

    def test_bind_lan_ip_start_status_add_dir_usable(self):
        lan_ip = _probe_lan_ipv4()
        if lan_ip is None:
            self.skipTest("本机探测不到非 loopback IPv4 接口, 无法构造源==bind 场景")
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "a.txt").write_text("aaa", encoding="utf-8")
        extra = Path(self._tmpdir.name) / "extra"
        extra.mkdir()
        (extra / "b.txt").write_text("bbb", encoding="utf-8")
        port = self._free_port(lan_ip)

        # start (bind 具体 IP): 守卫须放行源==bind 的就绪 ping
        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", lan_ip
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"], f"stdout={proc.stdout}")
        self.assertEqual(start_obj["bind"], lan_ip)
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        # status: 探活 ping 源==bind -> alive=true
        status_obj, code, proc = self._run_subprocess("status")
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(status_obj.get("alive"), f"stdout={proc.stdout}")

        # add-dir 经控制端点 (POST 源==bind) -> success 且 roots 更新
        add_obj, code, proc = self._run_subprocess("add-dir", str(extra))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(add_obj["success"], f"stdout={proc.stdout}")
        self.assertIn(str(extra.resolve()), add_obj["roots"])

        # add-dir 后新挂载内容经 LAN IP 立即可访问 (静态面不限来源)
        status, body = self._request(f"http://{lan_ip}:{port}/b.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "bbb")

        # 控制面 ping: 源==bind 放行
        status, body = self._request(f"http://{lan_ip}:{port}/__control__/ping")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["service"], "pi-present-web")


if __name__ == "__main__":
    unittest.main()
