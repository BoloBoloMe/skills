"""生成器路径: 构造导出流后立刻计时结束."""

import sys
import time

sys.path.insert(0, "src")
from exporter import export  # noqa: E402


def stream():
    for row in [1, 2, 3, 4]:
        yield export([row], "a")


def main() -> int:
    start = time.perf_counter()
    pending = stream()
    elapsed = (time.perf_counter() - start) * 1000
    print(f"total {elapsed:.1f} ms")
    print(f"built {pending}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
