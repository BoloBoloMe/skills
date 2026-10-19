"""候选库 B: 批量预取索引. 默认配置是逐条模式, 需批处理设置才按生产方式运行."""

import os
import time

MS_PER_1000_DEFAULT = 30.0
MS_PER_1000_BATCHED = 8.0


def build_index(rows):
    batch = int(os.environ.get("FASTIDX_BATCH", "1"))
    ms_per_1000 = MS_PER_1000_BATCHED if batch > 1 else MS_PER_1000_DEFAULT
    time.sleep(ms_per_1000 * rows / 1_000_000.0)
    return {"mode": "batched" if batch > 1 else "per-row", "batch": batch, "rows": rows}
