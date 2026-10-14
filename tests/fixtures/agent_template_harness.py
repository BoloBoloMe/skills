"""本机自足的 agent 模板测试夹具: 临时模板根 + 假模板 + 假 Key + 本机模拟网关.

只用标准库, 不读用户真实凭据/家目录配置, 不起真实网关, 不请求上游生成.
供 pytest 夹具 (tests/conftest.py 的 fake_agent_template) 与 unittest 用例
(真实子进程 swt.py birth) 共用. 假模板复用仓库版本化模型清单 (cliproxyapi),
只把名称/版本/网关入口/凭据路径换成本次临时资源, 保证公开校验接口通过.
"""
from __future__ import annotations

import http.client
import json
import os
import secrets
import shutil
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
REPO_TEMPLATES = REPO / "workflow" / "use-sandbox-worktree" / "agent-templates"
SOURCE_NAME = "cliproxyapi"
TEMPLATES_ENV = "SWT_AGENT_TEMPLATES_DIR"
# 容器内可达宿主 (podman 注入 /etc/hosts); 宿主侧本方法按同端口回环访问同一网关.
GATEWAY_HOST = "host.containers.internal"


def _handler(models: list[dict], key: str):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def _send(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if urlsplit(self.path).path != "/v1/models":
                self._send(404, {"error": "not found"})
                return
            if self.headers.get("Authorization") != "Bearer " + key:
                self._send(401, {"error": "unauthorized"})
                return
            self._send(200, {"object": "list",
                             "data": [{"id": model["id"], "object": "model"} for model in models]})

        def do_POST(self) -> None:
            # 其余路径的合理应答: 假网关不产生真实上游生成.
            self._send(200, {"object": "response", "status": "completed"})

        def log_message(self, *args) -> None:
            pass

    return Handler


class FakeAgentTemplate:
    """临时模板根 + 本机假网关 + 假 Key. 用 with 或 start()/stop()."""

    def __init__(self, source: str = SOURCE_NAME, name: str = "fixture-gateway"):
        self.source_name = source
        self.name = name
        self.root: Path | None = None
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.template: dict | None = None
        self.catalog: dict | None = None
        self.key_path: Path | None = None
        self.base_url: str | None = None
        self.port: int | None = None
        self._key: str | None = None
        self._env_backup: str | None = None
        self._env_present = False

    def start(self) -> "FakeAgentTemplate":
        source = REPO_TEMPLATES / self.source_name
        self.template = json.loads((source / "template.json").read_text(encoding="utf-8"))
        self.catalog = json.loads((source / "models.json").read_text(encoding="utf-8"))
        self._key = "fixture-" + secrets.token_hex(16)
        self.root = Path(tempfile.mkdtemp(prefix="swt-agent-fixture-"))
        directory = self.root / self.name
        directory.mkdir()
        self.key_path = self.root / "fake-key.json"
        self.key_path.write_text(
            json.dumps({"client_api_key": self._key}), encoding="utf-8"
        )
        os.chmod(self.key_path, 0o600)
        self.server = ThreadingHTTPServer(
            ("0.0.0.0", 0), _handler(self.catalog["models"], self._key)
        )
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://{GATEWAY_HOST}:{self.port}/v1"
        self.template["name"] = self.name
        self.template["version"] = "test.1"
        self.template["base_url"] = self.base_url
        self.template["credential"] = {
            "kind": "json-field",
            "path": str(self.key_path),
            "field": "client_api_key",
        }
        (directory / "template.json").write_text(
            json.dumps(self.template), encoding="utf-8"
        )
        shutil.copy(source / "models.json", directory / "models.json")
        self._env_present = TEMPLATES_ENV in os.environ
        self._env_backup = os.environ.get(TEMPLATES_ENV)
        os.environ[TEMPLATES_ENV] = str(self.root)
        return self

    def stop(self) -> None:
        if self._env_present:
            assert self._env_backup is not None
            os.environ[TEMPLATES_ENV] = self._env_backup
        else:
            os.environ.pop(TEMPLATES_ENV, None)
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread is not None:
            self.thread.join(timeout=5)
            self.thread = None
        if self.root is not None:
            shutil.rmtree(self.root, ignore_errors=True)
            self.root = None

    def __enter__(self) -> "FakeAgentTemplate":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()

    def get(self, path: str) -> tuple[int, dict]:
        """对 base_url + path 发 GET.

        base_url 主机 host.containers.internal 只在容器内可解析, 宿主侧按同端口
        回环连同一网关, 仍带模板声明的 Host 与本次假 Key.
        """
        assert self.base_url is not None and self.port is not None and self._key
        target = urlsplit(self.base_url + path)
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            connection.request("GET", target.path,
                               headers={"Host": GATEWAY_HOST,
                                        "Authorization": "Bearer " + self._key})
            response = connection.getresponse()
            return response.status, json.loads(response.read() or b"{}")
        finally:
            connection.close()


def pytest_fixture_source() -> type:
    """供 tests/conftest.py 直接复用本夹具实现的稳定入口."""
    return FakeAgentTemplate
