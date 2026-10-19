你是本轮产品验收的执行者, 未参与该项目的实现与修复. 目标提交是 HEAD = 5d3765e9b0d8228b8738a75ea69baef048402c45, 工作区 /tmp/orchestra-03/micro2/micro-groups.

任务: 按 PRODUCT.md 的验收场景逐条实际核对最终成品, 交回可复核原始材料. 不要做代码评审, 不改产品.

判据来源只有一处: docs/changes/tool-cli/PRODUCT.md 的 验收标准 节 (gherkin). 你分到全部三条场景, 原文如下:

- AC-001-1: 假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`; 当 值班同学读取 `dist/app.txt` 的第一行; 那么 内容为 `tool-cli 1`
- AC-002-1: 假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`; 当 值班同学读取 `dist/app.txt` 的第二行; 那么 内容为 `commands=greet,count,export`
- AC-003-1: 假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`; 当 值班同学读取 `dist/app.txt` 的第三行; 那么 内容为 `greet-shout=yes`

边界与规则:
1. 只读被验项目. 不修改源码, 配置, 测试, PRODUCT.md. 不 git add/commit/checkout/clean. 不删 dist.
2. 可用 docs/changes/tool-cli/TECHNICAL.md 和 README.md 里的运行命令作操作线索, 但那里面写的不是产品通过条件.
3. 逐条判据必须来自上面 gherkin 原文, 包括具体字符串, 不按"差不多"放宽. 行号, 首尾空白, 换行都按原文核对.
4. 每条场景都要有本轮实际运行证据: 命令原文, 原始输出 (不要只写摘要), 退出码, 执行时间. 同一份 prepare.sh 产物可同时支撑三条场景, 但每条都要给出对应行的实际读取结果.
5. 若某条无法执行, 记 未验证 并写明缺什么; 不许自建替代服务或本地替身把它改判通过.
6. 证据目录: docs/changes/tool-cli/verify-5d3765e-r1/ 内. 你的所有临时文件, 输出留存都写这里, 例如 acc-g5b-1-*.md. 不要在仓库其他位置新建文件.
7. 不跑 pytest / build.sh 代替产品判据; 它们不是产品通过条件, 需要时只作为操作线索记在附注.

交付物: 在该证据目录写 acc-g5b-1-RESULT.md, 内容:
- 目标提交完整标识
- 逐条表格: 标准编号 | 材料类型 (当前观察/引用旧观察/推断/未运行) | 命令与原始输出摘要 | 实际结果 | 证据文件路径 | 时间 | 结论 (通过/失败/未验证)
- 原始输出另存 acc-g5b-1-raw.txt, 保留命令, 真实输出, 退出码, 时间戳
- 附注: 不属于产品判据的技术事项单独注明, 不判通过也不判失败

完成后回一句话总结结论, 并列出证据文件绝对路径.
