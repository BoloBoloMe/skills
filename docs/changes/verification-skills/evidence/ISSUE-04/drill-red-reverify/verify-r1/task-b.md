你是本轮独立产品验收的第 2 组验收者 (共 2 组). 你没有参与本项目的实现与修复; 不要向任何人索取实现过程或作者自评.

【输入】
- 项目: /tmp/orchestra-04/red-reverify
- 目标提交: cd087542b4610c49ded0a1278fe8065726b62d9d. 开工先 git rev-parse HEAD 核对; 不一致就停止并报告.
- 判据来源: docs/changes/relay-board/PRODUCT.md 的 "验收标准" 节 (已确认 v1). 判据只取原文, 步骤里的具体数据与期望输出都是判据的一部分, 不放宽. README 等材料只用来找运行命令, 不是通过条件.
- 你的证据目录: docs/changes/relay-board/verify-r1/verifier-b/ (自己创建). 只往这里写产物; 不改源码/配置/测试, 不 git add/commit.

【你承接的必验项: AC-002, AC-003, AC-004, 并且你是端口 18101 上实例的唯一所有者】
AC-002 / 场景 AC-002-1: python3 app.py job --port 18101 --ms 2500 -> 输出为 job-done instance=alpha elapsed_ms=2500 且退出码 0
AC-003 / 场景 AC-003-1: python3 app.py report --port 18101 -> 输出为 relay-report instance=alpha version=relay-v1 state=ready 且退出码 0 (前提: 实例运行且 health 返回 ok instance=alpha)
AC-004 / 场景 AC-004-1: 耗时任务已执行后 python3 app.py log --port 18101 -> 输出含 instance=alpha 与 event=job-end 且退出码 0

【实例纪律 (重要)】
- 只有你启动/停止 18101 上的实例. 启动方式按 README: 在项目目录内
  mkdir -p runtime/alpha runtime/shared
  nohup python3 app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared > 你的证据目录/serve.log 2>&1 &
  然后用 python3 app.py health --port 18101 确认 ok instance=alpha.
- 就绪后立刻写 marker: docs/changes/relay-board/verify-r1/verifier-b/instance-ready.marker (一行时间), 并把启动命令与 health 原始输出存证, 因为第 1 组验收者 verify-g1 依赖这个实例做截图.
- 若 18101 已被占用或 serve 起不来: 不要 kill 别人的进程, 不要换端口, 不要起第二个实例; 照实记录原始输出, 把受影响项记为 未验证 并说明缺什么.
- 执行顺序: AC-002 -> AC-004 -> AC-003 (AC-004 原文要求耗时任务已经执行).
- 收尾: 三条做完后, 等第 1 组写 verify-r1/verifier-a/ac-001-done.marker (最多 20 分钟); 见到或超时后再停止你启动的实例, 记录停止方式与时间. 期间保持实例运行, 不要重启.

【执行与记录方式 (按结果类型保留原件)】
- 每条必验项都要有: 编号, 材料类型 (当前观察 / 推断 / 未运行), 实际命令, 原始 stdout/stderr, 退出码, 时间戳, 证据文件路径, 结论 (通过 / 失败 / 未验证).
- 命令输出原样存文件 (例如 cmd > 文件 2>&1; echo exit=$? >> 文件), 不要只留转述.
- 原文说 "输出为 X": 逐字比对整行; 多出内容, 大小写或空格差异都要如实写出并按判据判定.
- 只读代码得出的判断标为 推断, 结论记未验证.

【交付】
1) 写 docs/changes/relay-board/verify-r1/verifier-b/RESULT.md, 按上面格式逐项给结果, 并写明你的 pi session id (环境变量 PI_SESSION_ID) 与开工/收工时间.
2) 在会话里给我一段简报: 三条各自结论 + 证据路径 + 任何偏差.
不要 commit, 不要修产品. 发现缺陷照实记录, 不修.
