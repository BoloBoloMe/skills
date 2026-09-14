"""swt-base-server 测试 fixture: 临时 db + 随机端口起真服务, 供 node 测试驱动.

用法: uv run python swt_server_fixture.py
启动后 stdout 打一行 JSON: {"port", "admin_port", "admin_token", "db"},
然后常驻直到被杀. 环境变量:
  SWT_FIXTURE_PORT  信箱端口 (缺省 0 = 随机; 断线重试测试要固定端口)
  SWT_FIXTURE_HOLD  长轮询 hold 秒数 (缺省 1.0, 加速测试)
"""
import importlib.util
import json
import os
import sys
import threading
from pathlib import Path
from tempfile import mkdtemp

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt-base-server.py"

spec = importlib.util.spec_from_file_location("swt_base_server", SCRIPT)
swt = importlib.util.module_from_spec(spec)
sys.modules["swt_base_server"] = swt
spec.loader.exec_module(swt)

db = str(Path(mkdtemp()) / "mailbox.db")
mb = swt.Mailbox(db)
relay = swt.RelayStore(db)
port = int(os.environ.get("SWT_FIXTURE_PORT", "0"))
server = swt.MailboxHttpServer(mb, "127.0.0.1", port, relay=relay)
server.hold_seconds = float(os.environ.get("SWT_FIXTURE_HOLD", "1"))
admin = swt.AdminHttpServer(mb, relay, "test-admin-token", port=0)
server.start()
admin.start()
print(json.dumps({"port": server.port, "admin_port": admin.port,
                  "admin_token": "test-admin-token", "db": db}), flush=True)
threading.Event().wait()
