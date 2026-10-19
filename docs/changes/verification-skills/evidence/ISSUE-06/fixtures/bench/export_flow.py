"""一批请求走新版导出. 只打总耗时."""

import sys
import time

sys.path.insert(0, "src")
from exporter import export  # noqa: E402

ROWS = [120, 640, 810, 340, 990, 450, 700, 260]


def main() -> int:
    start = time.perf_counter()
    results = export(ROWS, "b")
    elapsed = (time.perf_counter() - start) * 1000
    print(f"total {elapsed:.1f} ms")
    print(f"returned {len(results)} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
