"""下单数量限制, 仅本模块内部使用."""


def clamp_qty(qty, upper=99):
    """把数量限制在 1..upper."""
    return max(1, min(qty, upper))
