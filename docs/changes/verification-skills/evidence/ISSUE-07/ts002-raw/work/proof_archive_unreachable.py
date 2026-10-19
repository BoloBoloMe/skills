"""证明 4: 归档服务在本地到不了, 且本仓库的推送路径不读导出 JSON.

运行:
  cd /tmp/orchestra-07/out/ts002-work
  PYTHONPATH=/tmp/orchestra-07/drill-ts002 uv run --no-project python proof_archive_unreachable.py

判断错时 assert 失败. 只读仓库, 不联网.
"""
import inspect
import pathlib
import sys

REPO = pathlib.Path("/tmp/orchestra-07/drill-ts002")
sys.path.insert(0, str(REPO))

from app.legacy_sync import ARCHIVE_URL, push_to_archive

print("ARCHIVE_URL:", ARCHIVE_URL)
src = inspect.getsource(push_to_archive)
print("push_to_archive 源码:")
print(src)

# 主机名在 RFC 6761 保留的 .invalid 顶级域, 不是真实可达地址
assert ARCHIVE_URL.endswith(".invalid/orders"), ARCHIVE_URL
# 没有 token 时在联网前就抛错
assert "ARCHIVE_TOKEN" in src and "orders_archive" in src
try:
    push_to_archive(None)
except RuntimeError as exc:
    print("无 token 调用:", type(exc).__name__, exc)
else:
    raise AssertionError("缺 ARCHIVE_TOKEN 时没有抛 RuntimeError")

# 推送读的是 orders_archive 表, 不是 read_orders 的输出; 本仓库没有把导出 JSON 送去归档的代码
assert "orders_archive" in src and "read_orders" not in src

print("OK: 本地无法到达归档服务, 推送路径与本次导出改动不共享代码")
