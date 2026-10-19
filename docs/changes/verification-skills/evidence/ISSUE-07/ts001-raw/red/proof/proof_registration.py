"""证明被删符号的副作用: 导入 app.orders 是否仍向 amountlib 注册 amount_str 格式化函数.

用法: uv run --no-project python proof_registration.py <repo-root>
"""
import sys

REPO = sys.argv[1]
sys.path.insert(0, REPO)

import amountlib.legacy as legacy  # noqa: E402
import app.orders  # noqa: E402,F401 - 只为触发导入期副作用

print(f"repo = {REPO}")
print(f"app.orders file = {app.orders.__file__}")
print(f"amountlib._FORMATTERS keys = {sorted(legacy._FORMATTERS)}")
print(f"hasattr(app.orders, 'format_amount_str') = {hasattr(app.orders, 'format_amount_str')}")
print(f"hasattr(app.orders, 'LEGACY_AMOUNT_KEY') = {hasattr(app.orders, 'LEGACY_AMOUNT_KEY')}")
print(
    "resolve_amount(v1 9.99) =",
    repr(legacy.resolve_amount({"schema": "v1", "amount_str": "9.99"})),
)
print(
    "resolve_amount(v1 空串) =",
    repr(legacy.resolve_amount({"schema": "v1", "amount_str": ""})),
)
