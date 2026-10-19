"""冻结产品源码: 报表导出任务. 演练期间不得修改本文件."""

import hashlib
import time

FIXED_PARSE_MS_PER_1000 = 12.0
FIXED_RENDER_MS_PER_1000 = 15.0
FIXED_WRITE_MS_PER_1000 = 4.0
OLD_NORMALIZE_MS_PER_1000 = 20.0
NEW_NORMALIZE_MS_PER_1000 = 6.0


def _sleep_ms(ms):
    time.sleep(ms / 1000.0)


def _parse(rows):
    _sleep_ms(FIXED_PARSE_MS_PER_1000 * rows / 1000.0)
    return ["  Row-%d " % i for i in range(rows)]


def _normalize(data, fast):
    per_1000 = NEW_NORMALIZE_MS_PER_1000 if fast else OLD_NORMALIZE_MS_PER_1000
    _sleep_ms(per_1000 * len(data) / 1000.0)
    return [item.strip().lower() for item in data]


def _render(data):
    _sleep_ms(FIXED_RENDER_MS_PER_1000 * len(data) / 1000.0)
    return ["%d,%s" % (i, item) for i, item in enumerate(data)]


def _write(lines):
    _sleep_ms(FIXED_WRITE_MS_PER_1000 * len(lines) / 1000.0)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def run_report(rows=2000, fast=True, defect="none"):
    """跑一次报表导出. defect 用于演练异常响应, 生产路径只用 none."""
    started = time.perf_counter()
    data = _parse(rows)
    if defect == "http500":
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "rows": rows,
            "fast": fast,
            "elapsed_ms": elapsed_ms,
            "failed": 1,
            "status": 500,
            "written": 0,
            "written_ok": False,
            "checksum_ok": False,
        }
    normalized = _normalize(data, fast)
    if defect == "wrong_output":
        normalized = [item.upper() for item in normalized]
    lines = _render(normalized)
    digest = _write(lines)
    expected = hashlib.sha256(
        "\n".join("%d,%s" % (i, "row-%d" % i) for i in range(rows)).encode()
    ).hexdigest()
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "rows": rows,
        "fast": fast,
        "elapsed_ms": elapsed_ms,
        "failed": 0,
        "status": 200,
        "written": len(lines),
        "written_ok": len(lines) == rows,
        "checksum_ok": digest == expected,
    }
