"""旧接口导出. 只打总耗时."""

import sys
import time

sys.path.insert(0, "src")
from exporter import export_legacy  # noqa: E402

ROWS = [1, 2, 3, 4, 5, 6, 7, 8]


def main() -> int:
    start = time.perf_counter()
    written = export_legacy(ROWS)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"total {elapsed:.1f} ms")
    print(f"written {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
