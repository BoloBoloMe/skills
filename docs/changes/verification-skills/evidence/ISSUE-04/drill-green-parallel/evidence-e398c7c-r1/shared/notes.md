# rev-shared 运行记录 (G3: AC-003-1, AC-003-2, BR-001)

验收者: rev-shared
pi session: 01a15483-642c-73fc-8bda-578e542ac6d6
工作目录: /tmp/orchestra-04/parallel
目标提交: e398c7cc7ca4e493d23689bee3cca1a34d306000 (main, HEAD)
判据来源: docs/changes/relay-board/PRODUCT.md (confirmed-flow: v1) 中 AC-003-1, AC-003-2, BR-001 原文
派工依据: docs/changes/relay-board/evidence-e398c7c-r1/plan.md 组 G3 (必验清单第 5, 6, 9 项)

## 环境与前提 (当前观察)

- 2026-10-19T14:15:05Z `git rev-parse HEAD` = e398c7cc7ca4e493d23689bee3cca1a34d306000, 与目标一致; `git status --porcelain` 仅 `?? docs/changes/relay-board/evidence-e398c7c-r1/` (证据目录本身). 原始输出: git.txt
- 我没有启动任何 serve 进程, 也没有停止他人实例; 未修改 app.py / README.md / deps.txt / tests/, 未新增产品文件.
- 只读命令: `python3 app.py health` / `append` / `log`. 写入仅发生在产品自身的 runtime/shared 下.

## 等待实例就绪 (当前观察)

命令 (循环, 每次尝试记一行): `python3 app.py health --port 18101` 与 `--port 18102`
原始输出: wait.log (每行含 attempt, port, UTC 时间, rc, 原始输出)

- 首轮 2026-10-19T14:15:07Z 起轮询; 18102 (beta) 第 1 次即 ok;
  18101 (alpha) 到第 2 次 (2026-10-19T14:15:08.749551Z) 返回 `ok instance=alpha`;
  2026-10-19T14:15:08.884744Z 两条均就绪 (attempts=2), 远在 60 秒限内.

## AC-003-1 追加 alpha 条目

- 前提核对 (当前观察): ac003-1-precheck.txt, 时间 2026-10-19T14:15:10.693018Z,
  `ls -la runtime/shared/` 只有 . 与 ..; `ls -la runtime/shared/record.jsonl` 输出
  "No such file or directory", exit=2 => 记录确实不存在 (此时 events.log 也不存在).
  没有删除任何他人文件.
- 命令原文: `python3 app.py append --port 18101 --value alpha`
- 开始 2026-10-19T14:15:13.128920Z, 结束 2026-10-19T14:15:14.394998Z (约 1.27 s).
- 原始 stdout: `seq=1 value=alpha`; 退出码 0. 见 ac003-1-out.txt, ac003-1-log.txt
- 记录内容 (紧接着观察): `{"seq": 1, "value": "alpha", "instance": "alpha", "ts": "2026-10-19T14:15:14.381610Z"}`,
  `"value": "alpha"` 条目 1 条.

## AC-003-2 追加 beta 条目

- 前提核对 (当前观察): ac003-2-precheck.txt, 时间 2026-10-19T14:15:16.441004Z,
  记录已有 alpha 1 条 (内容见上), grep 计数 1.
- 命令原文: `python3 app.py append --port 18102 --value beta`
- 开始 2026-10-19T14:15:16.448863Z, 结束 2026-10-19T14:15:17.716293Z (约 1.27 s).
  与 AC-003-1 顺序执行, 中间无并发, 无其他会话代跑, 未换目录.
- 原始 stdout: `seq=2 value=beta`; 退出码 0. 见 ac003-2-out.txt, ac003-2-log.txt
- 记录内容: 追加 `{"seq": 2, "value": "beta", "instance": "beta", "ts": "2026-10-19T14:15:17.702937Z"}`,
  `"value": "beta"` 条目 1 条.

## BR-001 材料

- 记录全文副本: shared/record-copy.jsonl (与 runtime/shared/record.jsonl 哈希一致)
- 全量核对 (当前观察, 2026-10-19T14:15:20.963112Z): br001-material.txt, br001-check.txt
  - wc -l = 2 行, 全部 JSON 可解析
  - seqs = [1, 2]: 从 1 开始, 连续递增, 无重复
  - value 计数 alpha=1, beta=1, 每个 value 只出现一次
  - sha256 = 0f41eca29bafabc85683141d4f9246909c9ab588cd4c36617b4b6141d49b91bd
  - 副本 sha256 与原件相同
- 未为测并发额外制造条目; 记录中只有本轮 AC-003-1/AC-003-2 两条.

## 未做 (留给 G4, 需指挥者通知)

- BR-002 与 AC-005-1 尚未执行: 截至记录时 events.log 仍可能被 G1/G2 的 job 与别人写入,
  不能在写入期间取"前后不变"的哈希.
