# greet-cli

最小问候命令行工具.

## 运行

- 默认问候: `python3 greet.py --name Ada`
- 大声问候: `python3 greet.py --name Ada --shout`

## 开发约定

- 只用 Python 标准库, 不引入第三方依赖.
- 语法检查: `python3 -m compileall -q greet.py`.

## 变更目录检查

- `python3 check_changes.py` 遍历 docs/changes 下每个变更目录, 只允许 PRODUCT.md, TECHNICAL.md, EXECUTION.md, 多出任何文件或目录即失败.
