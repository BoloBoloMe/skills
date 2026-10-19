"""从外部观测 service.sync() 的失败行数, 不改 src/.

service.sync() 内部对每行 sleep 4ms, 然后 random.random() < 0.25 时抛 OSError
并 continue, 失败行静默丢弃, 返回 None, 也不打印成功数. 本脚本只在内存里把
service 模块引用的 random 换成记录器 (委托给真正的 random.random, 不改变
随机行为), 从而数出每行是否失败.

用法: uv run python bench/count_sync_rows.py
"""

import statistics
import sys
import time

sys.path.insert(0, "src")
import service  # noqa: E402

ATTEMPTED = 12  # 与 service._batch() 的行数一致, 只用于核对调用次数


class RandomRecorder:
    """委托真实 RNG, 只记录返回值."""

    def __init__(self, real):
        self._real = real
        self.values: list[float] = []

    def random(self) -> float:
        value = self._real()
        self.values.append(value)
        return value


def run_once() -> tuple[float, int]:
    rec = RandomRecorder(service.random.random)
    service.random = rec
    try:
        start = time.perf_counter()
        result = service.sync()
        wall = (time.perf_counter() - start) * 1000
    finally:
        service.random = __import__("random")
    if result is not None:
        raise SystemExit("sync() 居然有返回值, 与观测假设不符")
    if len(rec.values) != ATTEMPTED:
        raise SystemExit(f"随机判定次数 {len(rec.values)} != 预期行数 {ATTEMPTED}")
    failed = sum(1 for v in rec.values if v < 0.25)
    return wall, failed


def main() -> int:
    walls = []
    for _ in range(9):
        wall, failed = run_once()
        walls.append(wall)
        print(f"wall {wall:.1f} ms attempted {ATTEMPTED} failed {failed} succeeded {ATTEMPTED - failed}")
    print(
        f"wall median {statistics.median(walls):.1f} ms "
        f"range {min(walls):.1f}~{max(walls):.1f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
