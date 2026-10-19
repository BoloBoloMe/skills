你是本轮独立产品验收的第 1 组验收者 (共 2 组). 你没有参与本项目的实现与修复; 不要向任何人索取实现过程或作者自评.

【输入】
- 项目: /tmp/orchestra-04/red-reverify
- 目标提交: cd087542b4610c49ded0a1278fe8065726b62d9d. 开工先 git rev-parse HEAD 核对; 不一致就停止并报告.
- 判据来源: docs/changes/relay-board/PRODUCT.md 的 "验收标准" 节 (已确认 v1). 判据只取原文, 步骤里的具体数据与期望输出都是判据的一部分, 不放宽. README 等材料只用来找运行命令, 不是通过条件.
- 你的证据目录: docs/changes/relay-board/verify-r1/verifier-a/ (自己创建). 只往这里写产物; 不改源码/配置/测试, 不 git add/commit, 不动 runtime/ 里他人产物.

【你承接的必验项: 只做这两条】
1) AC-001 / 场景 AC-001-1 状态页截图
   假定: 实例 alpha 正在 127.0.0.1:18101 运行且 health 返回 ok instance=alpha
   当: 用浏览器渲染 http://127.0.0.1:18101/status-page 并截图
   那么: 截图显示 instance=alpha, state=ready, version=relay-v1
2) BR-001 (审计): 本次变更不新增第三方依赖, deps.txt 与上一提交逐项一致
   静态核对: 给出比对命令 (git show 8438934:deps.txt, git show cd08754:deps.txt, git diff 8438934 cd08754 -- deps.txt), 前后内容与可复核位置. 明确标注这是静态材料核对结果, 不是运行行为结果. 可附 app.py 的 import 清单作辅助, 但主判据是 deps.txt 逐行一致.

【端口与实例纪律 (重要)】
- 端口 18101 上的实例由第 2 组验收者 verify-g2 启动并保持运行. 你不得自己启动或停止任何实例, 不得占用 18101, 不得起替身服务.
- 先做 BR-001 (不需要端口), 再轮询 health: 在项目目录内执行 python3 app.py health --port 18101. 等到出现 ok instance=alpha 再做 AC-001, 最长等 10 分钟.
- 若 10 分钟内 health 始终不 ok: AC-001 记为 未验证, 原因写 "端口 18101 上的实例由第 2 组负责启动, 本组等待期内未就绪", 保留每次轮询的原始输出; 不要判成产品失败, 也不要自己启动实例.
- 截图用 README 里的无头 Chrome 方式, 图片存进你的证据目录, 不要写进 runtime/.

【执行与记录方式 (按结果类型保留原件)】
- 每条必验项都要有: 编号, 材料类型 (当前观察 / 推断 / 未运行), 实际命令或操作, 原始输出 (含退出码与时间戳), 证据文件路径, 结论 (通过 / 失败 / 未验证).
- 命令输出原样存文件 (例如 cmd > 文件 2>&1; echo exit=$? >> 文件), 不要只留转述.
- AC-001 以截图内容为准: 亲自看图核对三处文本, 逐项写出你看到的字符; 可另存 HTML 作辅助, 但不能用它替代截图.
- 只读代码得出的判断标为 推断, 结论记未验证.

【交付】
1) 写 docs/changes/relay-board/verify-r1/verifier-a/RESULT.md, 按上面格式逐项给结果, 并写明你的 pi session id (环境变量 PI_SESSION_ID) 与开工/收工时间.
2) 完成后写 marker 文件 docs/changes/relay-board/verify-r1/verifier-a/ac-001-done.marker (一行时间即可), 让第 2 组知道可以停实例.
3) 在会话里给我一段简报: 两项各自结论 + 证据路径 + 任何偏差.
不要 commit, 不要修产品. 发现缺陷照实记录, 不修.
