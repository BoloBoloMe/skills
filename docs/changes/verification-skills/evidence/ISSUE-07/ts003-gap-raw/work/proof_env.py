"""断言: 跑的是仓库内 vendored amountlib 2.4.0, 不是别处装的那份."""
import sys, amountlib, importlib.util

assert sys.version_info >= (3, 11), sys.version
assert amountlib.VERSION == "2.4.0", amountlib.VERSION
assert "/ts003-gap-work/head/" in amountlib.__file__, amountlib.__file__
print("python", sys.version.split()[0])
print("amountlib.VERSION", amountlib.VERSION)
print("amountlib.__file__", amountlib.__file__)
print("parse_amount", amountlib.parse_amount)
