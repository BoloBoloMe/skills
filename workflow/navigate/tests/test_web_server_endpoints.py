"""web_server.py HTTP 端点测试 (ISSUE-04: TC-016, TC-015, 占位页)."""

import json
import urllib.parse

from conftest import http_get


def _api_url(server, port, path):
    return server.base_url(port) + "/api/roadmap?path=" + urllib.parse.quote(path)


def test_index_served(server):
    """TC-008 扩展 (ISSUE-04): GET / 与 /index.html 返回 200 text/html 占位页."""
    obj = server.start()
    base = server.base_url(obj["port"])
    for path in ("/", "/index.html"):
        status, headers, body = http_get(base + path)
        assert status == 200, f"{path} -> {status}"
        ctype = headers.get("Content-Type", "")
        assert "text/html" in ctype, f"{path} Content-Type={ctype}"
        assert len(body) > 0
        # 两处返回同一占位页内容
        if path == "/":
            index_body = body
        else:
            assert body == index_body


def test_api_roadmap_rejects_non_json_and_missing(server):
    """TC-016 (AC-016): /etc/passwd 被拒不返回内容; 不存在 .json 得错误响应."""
    obj = server.start()
    base = server.base_url(obj["port"])

    # 非 .json 路径: 拒绝, 且不泄露文件内容
    status, headers, body = http_get(_api_url(server, obj["port"], "/etc/passwd"))
    assert status == 403, f"/etc/passwd -> {status}"
    payload = json.loads(body.decode("utf-8"))
    assert payload["success"] is False
    assert b"root:" not in body, "响应泄露了 /etc/passwd 内容"

    # 不存在的 .json: 错误响应
    missing = str(server.runtime_base.parent / "no-such-roadmap.json")
    status, _, body = http_get(_api_url(server, obj["port"], missing))
    assert status == 404, f"missing .json -> {status}"
    payload = json.loads(body.decode("utf-8"))
    assert payload["success"] is False


def test_api_roadmap_error_shape_for_frontend(server):
    """TC-015 (AC-015 数据侧): 不存在路径返回确定形态的结构化错误."""
    obj = server.start()
    missing = str(server.runtime_base.parent / "absent.json")
    status, headers, body = http_get(_api_url(server, obj["port"], missing))
    # 非 2xx + JSON error 双重信号, 前端可据此渲染友好提示
    assert status == 404
    assert "application/json" in headers.get("Content-Type", "")
    payload = json.loads(body.decode("utf-8"))
    assert payload["success"] is False
    assert payload["code"] == "not_found"
    assert isinstance(payload["error"], str) and payload["error"]
    assert missing in payload["error"]


def test_api_roadmap_returns_json_content(server):
    """存在的 .json 返回其 JSON 内容 (端点放行路径, 冒烟亦覆盖)."""
    roadmap = server.runtime_base.parent / "ROADMAP.json"
    data = {"schema_version": "0.0.1", "title": "测试路线图", "milestones": {}}
    roadmap.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    obj = server.start()
    status, headers, body = http_get(_api_url(server, obj["port"], str(roadmap)))
    assert status == 200
    assert "application/json" in headers.get("Content-Type", "")
    assert json.loads(body.decode("utf-8")) == data
