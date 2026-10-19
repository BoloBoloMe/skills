#!/usr/bin/env python3
"""记录板: 状态页, report 单行与向外部 relay 服务同步一次事件."""
import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
from relaylib import VERSION as DEP_VERSION  # noqa: E402

VERSION = "relay-v2"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class Board:
    def __init__(self, instance: str, data_dir: str) -> None:
        self.instance = instance
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state = "ready"

    def status_page(self) -> str:
        return (
            "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"><title>relay board</title></head>\n"
            "<body><h1>relay board</h1>\n"
            f"<p>instance={self.instance}</p>\n<p>state={self.state}</p>\n"
            f"<p>version={VERSION}</p></body></html>\n"
        )

    def report_line(self) -> str:
        return f"relay-report instance={self.instance} version={VERSION} dep={DEP_VERSION}"

    def sync(self, relay_port: int) -> str:
        payload = json.dumps(
            {"instance": self.instance, "dep": DEP_VERSION, "ts": now_iso()}
        ).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{relay_port}/ingest",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8").strip()
        return f"sync-ok instance={self.instance} dep={DEP_VERSION} {body}"


def handler_factory(board: Board):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _text(self, body: str, status: int = 200, ctype: str = "text/plain; charset=utf-8") -> None:
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            if parsed.path == "/health":
                self._text(f"ok instance={board.instance}\n")
                return
            if parsed.path == "/status-page":
                self._text(board.status_page(), ctype="text/html; charset=utf-8")
                return
            if parsed.path == "/report":
                self._text(board.report_line() + "\n")
                return
            if parsed.path == "/sync":
                port = int(query.get("relay", ["0"])[0])
                try:
                    body = board.sync(port)
                except OSError as exc:
                    self._text(f"relay-unreachable: {exc}\n", status=503)
                    return
                self._text(body + "\n")
                return
            self._text("not found\n", status=404)

    return Handler


def client_get(port: int, path: str) -> int:
    url = f"http://127.0.0.1:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            body = response.read().decode("utf-8")
            status = response.status
    except OSError as exc:
        print(f"request failed: {exc}", file=sys.stderr)
        return 1
    if status != 200:
        print(f"status {status}: {body}", file=sys.stderr)
        return 1
    sys.stdout.write(body)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="app.py")
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, required=True)
    serve.add_argument("--instance", required=True)
    serve.add_argument("--data-dir", required=True)

    for name in ("health", "status", "report"):
        sub = commands.add_parser(name)
        sub.add_argument("--port", type=int, required=True)

    sync = commands.add_parser("sync")
    sync.add_argument("--port", type=int, required=True)
    sync.add_argument("--relay-port", type=int, required=True)

    args = parser.parse_args(argv)

    if args.command == "serve":
        board = Board(args.instance, args.data_dir)
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_factory(board))
        print(f"listening on 127.0.0.1:{args.port} instance={board.instance}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0
    if args.command == "health":
        return client_get(args.port, "/health")
    if args.command == "status":
        return client_get(args.port, "/status-page")
    if args.command == "report":
        return client_get(args.port, "/report")
    if args.command == "sync":
        return client_get(args.port, f"/sync?relay={args.relay_port}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
