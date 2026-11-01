"""TC-04-09: HTTP 面只读静态服务 (BR-029, m13 D023, m14 D007).

根外路径 (../), 根外软链 .cc.json, 目录路径 (无 index.html) 都 404 且不列
目录; POST/PUT 不被接受; 根 index.html 正常 200.

隔离纪律: 独立运行时目录与独立高位端口; 收尾 fixture stop 加强杀.
"""
from __future__ import annotations

import pytest

from codemap_service_helpers import CodemapSrv, http_status


@pytest.fixture
def srv(tmp_path):
    controller = CodemapSrv(tmp_path)
    yield controller
    controller.cleanup()


def test_tc_04_09_http_surface_boundaries(srv):
    """TC-04-09: 越界防护与只读边界."""
    # 假 serve-root: index.html + 伪 .cc.json + 无 index 的子目录 + 指向根外的软链
    srv.prime()
    plain_dir = srv.serve_root / "plain"
    plain_dir.mkdir()
    (plain_dir / "note.txt").write_text("inside root, no index", encoding="utf-8")
    outside = srv.base.parent / "outside-secret.cc.json"
    outside.write_text('{"secret": true}', encoding="utf-8")  # 根外文件
    link = srv.serve_root / "outside.cc.json"
    link.symlink_to(outside)

    srv.serve()

    # 根 index.html 200
    status, body = http_status(srv.port)
    assert status == 200
    assert b"codemap fake frontend" in body

    # 登记数据副本 200 (副本在根内)
    key = srv.read_state()["data_keys"][0]["key"]
    status, _ = http_status(srv.port, f"/{key}")
    assert status == 200

    # 根外路径 (..) 404
    for path in ("/../outside-secret.cc.json", "/../../etc/passwd"):
        status, _ = http_status(srv.port, path)
        assert status == 404, f"{path} 应 404"

    # 根外软链 404 (resolve 后 relative_to 判归属)
    status, _ = http_status(srv.port, "/outside.cc.json")
    assert status == 404

    # 目录路径 (无 index.html) 404 且不列目录
    status, body = http_status(srv.port, "/plain/")
    assert status == 404, "无 index 的目录应 404"
    assert b"note.txt" not in body, "不得列出目录内容"
    status, _ = http_status(srv.port, "/plain")
    assert status == 404

    # 写接口不被接受
    for method in ("POST", "PUT"):
        status, _ = http_status(srv.port, "/", method=method)
        assert status is not None and status >= 400, f"{method} 应被拒绝 (实际 {status})"
