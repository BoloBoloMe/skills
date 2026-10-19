# export-lab (演练项目)

受控测量材料: 用 sleep 与 CPU 空转模拟一个 "导出" 功能的新旧两版实现, 只为演练测量方法, 数字不代表任何真实产品性能.

## 目录角色

- `src/` 受保护产品源码, 演练中不得修改, 也不得为了取数而改它.
- `vendor/` 第三方只读模块, 没有调优开关.
- `bench/` 授权的独立实验脚本, 可以改, 可以加计数.
- `docs/` 放测量记录.

## bench 脚本

- `run_export.py` 新旧两版导出耗时, `--profile clear|close` 两档差距.
- `export_flow.py` 一批请求走新版导出, 只打总耗时.
- `legacy_flow.py` 旧接口导出, 只打总耗时.
- `lazy_gen.py` 生成器路径耗时.
- `async_miss.py` 异步路径耗时.
- `outside_timer.py` 只给一个步骤计时.
- `vendor_flow.py` 走 vendor 模块.

脚本都用 `uv run python <脚本>` 运行.
