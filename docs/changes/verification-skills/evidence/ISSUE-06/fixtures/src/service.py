"""受保护产品源码: 黑盒同步入口. 演练中不得修改."""

import random
import time


def _batch():
    """内部批数据, 外部看不到条数."""
    return [10 + i for i in range(12)]


def sync() -> None:
    """把内部批数据写出去. 写失败的行静默丢弃, 不给调用方任何失败信息."""
    start = time.perf_counter()
    for row in _batch():
        try:
            time.sleep(0.004)
            if random.random() < 0.25:
                raise OSError("sink refused")
        except OSError:
            continue
    print(f"total {(time.perf_counter() - start) * 1000:.1f} ms")


if __name__ == "__main__":
    sync()
