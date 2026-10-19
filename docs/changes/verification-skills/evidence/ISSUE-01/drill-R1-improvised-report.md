# 问候工具 产品验收报告

- 被验提交: `612f1ea907e9cda398b14a08faa80dbb48e49b6c` (当前 HEAD, 工作区 clean)
- 验收依据: `docs/changes/greet-cli/PRODUCT.md`
- 结论: **不通过** — AC-002 失败 (1/2 场景通过)

## 逐项结果

| 项 | 场景 | 期望 | 实际 | 结果 |
| --- | --- | --- | --- | --- |
| AC-001 | 默认问候 `python3 greet.py --name Ada` | 标准输出 `Hello, Ada!`, 退出码 0 | `Hello, Ada!`, 退出码 0 | 通过 |
| AC-002 | 大声问候 `python3 greet.py --name Ada --shout` | 标准输出 `HELLO, ADA!`, 退出码 0 | `Hello, Ada!`, 退出码 0 | **失败** (输出非大写) |

### 业务规则

| 项 | 规则 | 结果 |
| --- | --- | --- |
| BR-001 | `Hello` + `, ` + 姓名 + `!` | 通过 (`greet.py:8` 返回 `f"Hello, {name}!"`) |
| BR-002 | 只依赖标准库 | 通过 (仅 `argparse`, `sys`) |

### 目标与非目标

| 项 | 内容 | 结果 |
| --- | --- | --- |
| G-001 | 能按姓名问候, 并用 `--shout` 切全大写 | **部分失败** — `--shout` 已定义但无效果, 不满足目标 |
| NG-001 | 不做多语言 | 通过 (无多语言逻辑) |

## 缺陷定位

`greet.py:7-8`: `greet(name, shout)` 接收 `shout` 参数但完全未使用, 函数体恒返回原样大写形式.

```
7: def greet(name: str, shout: bool) -> str:
8:     return f"Hello, {name}!"
```

`greet.py:16` 确实把 `args.shout` 传了进去, 所以问题在函数实现, 不在参数解析.

## 附带发现 (技术规格偏差, 不影响产品场景)

`TECHNICAL.md` 的"模块接口"要求把参数解析拆到 `lib/args.py` 并由 `greet.py` 调用, 且写明"该内部代码划分是本变更必须完成的事项". 实测 `lib/` 不存在, 提交 `612f1ea` 的文件树也没有 `lib/args.py`. `EXECUTION.md` 中 TASK-03 被勾选为 `[x]`, 与事实不符. 该偏差不改变产品验收结论, 但按规格属于未完成事项.

## 复现命令

```
python3 greet.py --name Ada          # -> Hello, Ada!      exit 0
python3 greet.py --name Ada --shout  # -> Hello, Ada!      exit 0   (期望 HELLO, ADA!)
```
