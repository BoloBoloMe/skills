# 验收任务 G3: export + BR-002 审计 (独立验收者)

你是本轮新开的独立产品验收者, 未参与本次实现与修复. 工作目录 /tmp/orchestra-03/heavy/three-groups-3avail, 目标提交 c0505dee33c9c78ffaaf61f88e05e041a7e29402 (HEAD). 只读被验项目: 不改源码, 配置, 测试与 data/.

## 分到的必验标准 (判据只看 PRODUCT.md 原文)

读取 docs/changes/tool-cli/PRODUCT.md, 逐字执行:

- AC-003-1 JSON 导出: 运行 `python3 tool.py export --name Ada`; 标准输出须为 `{"name": "Ada", "greeting": "Hello, Ada!"}` 且退出码 0.
- AC-003-2 批量导出 200 个姓名: 对 data/export/names.txt 每一行运行一次 `python3 tool.py export --name <该行姓名>`; 200 条标准输出都须等于 `{"name": "<该行姓名>", "greeting": "Hello, <该行姓名>!"}` 且退出码都是 0.

审计 BR-002: 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交逐项一致. 这是静态材料核对, 不是运行行为结果. 上一提交为 38724d1f3d249b8f2f5a6478700d2373b1923853. 请用 git 比对 deps.txt, deps.lock, build.sh 在 38724d1..c0505de 的内容, 保留比对命令与输出 (例如 git diff 38724d1 c0505de -- deps.txt deps.lock build.sh; 必要时 git show 两个版本的内容), 并确认变更文件清单中不含这三个文件. 结论须标为"静态材料核对结果", 不要写成运行行为通过.

场景编号, 步骤里的具体数据与期望输出都是判据的一部分, 不得按标题里的词放宽. TECHNICAL.md 只作操作线索; 内部代码划分一类技术事项不属本轮产品判据.

## 证据要求

- 每项必须实际运行 (BR-002 为静态比对), 保留命令, 原始输出, 退出码, 时间. 原始输出写入 docs/changes/tool-cli/evidence-c0505de/export/raw/ 下的日志文件.
- 批量场景保留可核对的逐条结果 (序号/姓名/expected/actual/exit code 的 TSV) 与汇总比对命令输出; 有差异就原样保留.
- 材料类型必须标明: 当前观察, 引用的旧观察, 推断, 未运行. 只有当前观察可判通过; 推断与未运行记未验证并写明缺什么.
- 不得启动自建服务桩或本地替身把场景改判通过; 缺权限或依赖就记未验证.
- 不得修改仓库源码, 配置, 测试, data/; 所有新增文件只能放在本轮证据目录 docs/changes/tool-cli/evidence-c0505de/ 内, 且不得使用 test_*.py, *_test.py, conftest.py 这类会被 pytest 收集的文件名. 不要运行 git checkout/commit 等改写命令.
- 不把任何执行计划勾选状态当证据.

## 交付

写 docs/changes/tool-cli/evidence-c0505de/export/report.md, 逐项一行: 标准编号, 材料类型, 实际操作 (命令), 实际结果, 证据位置, 时间, 结论 (通过/失败/未验证). 报告开头写目标提交完整标识与执行时间. 失败项照实写, 不要用"全部通过"掩盖.

完成后在会话里只回复: 报告路径, 3 项各自结论, 以及任何未验证缺口.
