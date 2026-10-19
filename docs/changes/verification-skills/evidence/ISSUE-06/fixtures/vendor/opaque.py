"""第三方只读模块: debug 构建, 内部固定延时, 没有调优开关."""

import time


def run(payload):
    time.sleep(0.030)
    return payload * 2
