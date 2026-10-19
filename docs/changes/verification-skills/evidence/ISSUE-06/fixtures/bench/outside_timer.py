"""先算完再计时, 计时区内只留收尾."""

import sys
import time

sys.path.insert(0, "src")
from exporter import export  # noqa: E402

ROWS = [11, 22, 33, 44]


def main() -> int:
    produced = export(ROWS, "a")
    start = time.perf_counter()
    summary = len(produced)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"total {elapsed:.2f} ms")
    print(f"summary {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
