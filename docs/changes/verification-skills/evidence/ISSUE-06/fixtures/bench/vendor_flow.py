"""走第三方只读模块."""

import sys
import time

sys.path.insert(0, "vendor")
from opaque import run  # noqa: E402


def main() -> int:
    start = time.perf_counter()
    values = [run(i) for i in range(3)]
    elapsed = (time.perf_counter() - start) * 1000
    print(f"total {elapsed:.1f} ms")
    print(f"values {values}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
