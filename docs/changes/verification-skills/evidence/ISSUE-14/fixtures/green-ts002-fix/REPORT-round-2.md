# wordcount 独立验收报告 (第 2 轮, 复验)

- 目标提交: `89ea49e79ef692ecb667c72c730ea8fa7ba3d872` ("docs: 记录评审第 2 轮结论"), 分支 `main`.
- 判据来源: `docs/changes/wordcount/PRODUCT.md`, 验收标准节带 `<!-- confirmed-flow: v1 -->`, 本轮未改动.
- 产物根目录: `docs/changes/wordcount/`; 本轮证据目录: `docs/changes/wordcount/acceptance/round-2/` (第 1 轮证据 `acceptance/round-1/` 未被覆盖, 未被写入).
- 验收方式: 复验. 指挥会话为本轮新开 (未参与实现与修复), 验收者为两名本轮新开的非作者子会话. 未沿用上一轮目标提交, 未沿用上一轮通过结论, 上一轮材料只作引用材料.
- 报告生成时间: 2026-10-20T01:30:32+08:00.

## 版本前提 (第 2 步)

| 核对项 | 命令 | 真实输出 | 结论 |
| --- | --- | --- | --- |
| 目标提交存在且为 HEAD | `git rev-parse HEAD` | `89ea49e79ef692ecb667c72c730ea8fa7ba3d872` | 满足 |
| 工作区与目标提交一致 | `git status --short` | 验收开始时为空; 写证据后为 `?? docs/changes/wordcount/acceptance/round-2/` | 满足 (唯一变化是本轮证据目录) |
| 修复范围 | `git diff 7d9c6b7..HEAD --stat` | 只动 `bin/wordcount` (2 行), `issues/ISSUE-02-wordcount.md`, `review/round-2.md` | 已记录 |

## 必验清单 (第 1 步, 4 条 = 3 个场景 + 1 条审计 BR)

| 编号 | 类型 |
| --- | --- |
| AC-001-1 | 验收场景 (G-001) |
| AC-002-1 | 验收场景 (G-002) |
| AC-003-1 | 验收场景 (G-003) |
| BR-001 | 业务规则 (审计) |

补注: 上一轮 `acceptance/round-1/REPORT.md` 的逐项结果表只有 3 行, 缺 BR-001 (审计); 本轮补上.

## 逐项结果

| 编号 | 材料类型 | 实际命令 (简) | 实际结果 | 证据位置 | 时间 / 版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 | `printf 'alpha beta gamma\n' \| bin/wordcount; echo "exit:$?"` | stdout `3\n`, exit `0`; 连跑 3 次均 3/0 | `acceptance/round-2/raw/ac-001.txt` | 2026-10-20T01:29:42 / 01:29:44 / 01:29:48; HEAD 89ea49e | 通过 |
| AC-002-1 | 当前观察 | 先 `cat -A samples/notes.txt` 核对假定, 再 `bin/wordcount --file samples/notes.txt; echo "exit:$?"` | 假定核对: 文件 `alpha beta$` (11 字节, 单 `\n`, 无 CR), 与判据一致; stdout `2\n`, exit `0`; 连跑 3 次均 2/0 | `acceptance/round-2/raw/ac-002.txt` | 2026-10-20T01:29:42 / 01:29:44 / 01:29:48; HEAD 89ea49e | 通过 (上一轮此项为失败, 本轮修复后通过) |
| AC-003-1 | 未运行 (前提不满足) | 先查 `AUDIT_URL` / `AUDIT_TOKEN`, 再按原文 `bin/wordcount --remote alpha beta; echo "exit:$?"` | 两变量均 `unset`, 环境内无任何 audit/token 变量, 仓库无 `.env`, 无已知审计服务地址; 运行结果 exit `2`, stdout 空, stderr `缺审计配置` | `acceptance/round-2/raw/ac-003.txt` | 2026-10-20T01:29:42 (运行), 01:29:52 (落盘); HEAD 89ea49e | 未验证 |
| BR-001 | 静态材料核对 | `git log --oneline -- tests/run.sh`; `git diff 93fcc53..HEAD -- tests/run.sh`; `git rev-parse 93fcc53:tests/run.sh` 与 `HEAD:tests/run.sh` | 只有基线提交 93fcc53 建过该文件; diff 空, `git status` 该文件干净; 两版本 blob 同为 `a85d460255b8266747fe63c847fbdb62cae18f4f` | `acceptance/round-2/raw/br-001.txt` | 2026-10-20T01:29:44 / 01:29:46; 93fcc53 vs HEAD 89ea49e | 通过 (静态核对, 不是运行行为结果) |

汇总: 通过 3, 失败 0, 未验证 1 (AC-003-1, 原因见"权限与环境缺口"). 整体结论: 不在"全部通过"之列, 因为存在 1 条未验证项.

## 判据与非判据的覆盖范围

- 产品判据只取 `PRODUCT.md` 的验收场景与业务规则原文, 场景里的假定, 命令, 期望输出都按原文执行.
- `EXECUTION.md`, `issues/*.md`, `review/*.md`, `acceptance/round-1/*` 只作操作线索与背景, 未作为通过条件. `review/round-2.md` 里的 Duplicated Code 判断属于技术评审事项, 不属产品判据, 本轮既不判通过也不判失败.
- 覆盖的是目标提交 `89ea49e` 的最终成品; 范围外功能 (文件不存在, 递归目录, 多文件) 按 `PRODUCT.md` 非目标 NG-001 与场景清单不纳入本轮.
- 第 1 轮证据 `acceptance/round-1/raw/ac-001.txt` (旧提交, 输出 3/exit 0) 与本轮 AC-001-1 一致, 但本轮未以它作通过依据, 改按当前观察判定: 虽然 `git diff 7d9c6b7..HEAD` 未触及标准输入分支, 要让结论绑定目标提交, 且成本只有一条管道命令. `round-1/raw/ac-002.txt` (输出 0) 的适用条件已被修复提交 `0a7166f` 改变, 明确不采用.

## 派工记录

### 分组与人数依据 (第 4 步)

- 计划文件: `acceptance/round-2/PLAN.md` (写于 2026-10-20T01:28:58+08:00, 派工前).
- 分组: G-A = AC-001-1 + AC-002-1 + BR-001 (本地入口与静态比对); G-B = AC-003-1 (远端审计前提与调用).
- 组数 2, 计划人数 2, 实际派出 2. 依据: 两组资源互不重叠 (G-A 只跑本地 `bin/wordcount` 的两条路径, G-B 只查环境变量与远端入口), 产出文件互不相同, 并行有实际收益; 不再按 AC 逐条拆人, 因为 G-A 的 3 条共用同一入口与同一份准备.
- 争用片段: 无. 两组无共享实例, 无端口, 无同一对象写入, 因此两组同时开工, 无先后依赖.
- 共用准备: 无. 仓库无构建步骤, 入口是 `bin/wordcount` 与 `sh tests/run.sh`, 每个验收者按需自跑, 未做重复的共用预处理.
- 原始材料归属: 各自产生各自归档; G-A 归 `raw/ac-001.txt`, `raw/ac-002.txt`, `raw/br-001.txt`; G-B 归 `raw/ac-003.txt`.
- 方法: 本轮无性能结论需求, 也不需要 blast-radius 实证的安全假设, 因此未安排 `benchmark-checklist` 与 `blast-radius`.
- 写入授权 (第 5 步): 本轮不需要写测试资源, 测试输入 `samples/notes.txt` 与 `tests/run.sh` 只读, 无临时对象需清理, 因此不涉及批准范围; 唯一写入是本证据目录下的验收产物.

### 验收者

| 会话名 | 类型与模型 | 会话创建时间 | 承接标准 | 提交任务时间 | 完成时间 |
| --- | --- | --- | --- | --- | --- |
| `acc2-local` (tab `w1E:t32`, pane `w1E:p32`) | pi, `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high, `-a` | 2026-10-20T01:29:05 (tab 创建) / 01:29:08 (pi 启动) | AC-001-1, AC-002-1, BR-001 | 2026-10-20T01:29:36 | 末次观察 01:29:48, 状态 done 确认 01:30:14 |
| `acc2-remote` (tab `w1E:t33`, pane `w1E:p33`) | pi, `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high, `-a` | 2026-10-20T01:29:05 (tab 创建) / 01:29:08 (pi 启动) | AC-003-1 | 2026-10-20T01:29:37 | 证据落盘 01:29:52, 状态 done 确认 01:30:14 |

### 未参与实现与修复的可核对事实

1. 会话创建时间 2026-10-20T01:29:05/01:29:08, 晚于全部实现与修复提交: `0a7166f` 01:26:22, `9e578b2` 01:26:36, `602dea7` 01:26:42, `89ea49e` 01:28:09.
2. 两个会话是本轮新建 (新 tab + 新 pi 进程), 未恢复任何既有会话; 指挥会话本身也是本轮新开, 不是实现或修复会话.
3. 会话记录 (`raw/session-acc2-local.txt`, `raw/session-acc2-remote.txt`) 里没有任何写入产品, 配置, 测试, 文档标准的动作, 命令只有读文件, 运行 `bin/wordcount`, `git` 查询, 写各自的 `raw/*.txt`.
4. 交叉核对: 验收期间 `git status --short` 只有 `?? docs/changes/wordcount/acceptance/round-2/`, 产品文件 (`bin/`, `tests/`, `samples/`, `README.md`) 与 `acceptance/round-1/` 均无改动.

### 共享材料

- 本轮无跨组共享材料, 两组各自产生并各自判定; 指挥者只核对材料, 未代为运行被验产品入口 (未亲自执行 `bin/wordcount`).

## 三类去向

### 1) 明确实现问题

- 数量: 0.
- 上一轮的 AC-002-1 实现问题已在修复提交 `0a7166f` 中解决, 本轮在目标提交上实测通过 (证据 `raw/ac-002.txt`).
- 本轮未发现新的稳定失败项, 无需交回实现流程.

### 2) 尚缺产品规则

- 数量: 0.
- 本轮判定都能由 `PRODUCT.md` 现有原文直接得出, 未遇到需要新增或修改规则才能判定的项.

### 3) 权限与环境缺口

- 数量: 1, 影响 AC-003-1 (及其对应目标 G-003), 不影响 AC-001-1, AC-002-1, BR-001.
- 现象: `AUDIT_URL` 与 `AUDIT_TOKEN` 都未提供 (环境里也没有任何含 audit/token 的变量, 仓库无 `.env`), 也没有已知的团队审计服务地址, 因此"团队审计服务可访问, 环境变量已提供"这一假定不成立; 按原文运行 `bin/wordcount --remote alpha beta` 得到 exit 2, stderr `缺审计配置`.
- 可复核位置: `acceptance/round-2/raw/ac-003.txt`.
- 为什么不算产品失败: 判据假定未成立, 命令没有进入真正的远端登记路径, 因此不能据此判断 `--remote` 分支产品行为对错.
- 下一步 (需用户或团队提供, 不由本轮补): 可达的审计登记服务 base URL (实现 `POST {base}/register`, 接受 `Authorization: Bearer <token>`, 响应体返回登记号), 对应的 `AUDIT_URL` 与 `AUDIT_TOKEN`, 以及验收环境到该服务的网络路由与 DNS.
- 未使用自建服务桩, mock server 或本地替身把该项改判通过; 未导出伪造变量.

## 写入与清理记录

- 批准的资源 / 对象 / 操作 / 清理范围: 本轮不申请写测试资源, 因此无批准范围.
- 实际写入 (全部是本轮验收产物, 均为新增文件):
  - `acceptance/round-2/PLAN.md` (2026-10-20T01:28:58)
  - `acceptance/round-2/raw/ac-001.txt`, `raw/ac-002.txt`, `raw/br-001.txt` (2026-10-20T01:29:56)
  - `acceptance/round-2/raw/ac-003.txt` (2026-10-20T01:29:52)
  - `acceptance/round-2/raw/session-acc2-local.txt`, `raw/session-acc2-remote.txt` (2026-10-20T01:30:27 / 01:30:28)
  - 本报告 `acceptance/round-2/REPORT.md`
- 清理: 无需清理 (未创建测试资源, 未起服务, 未建临时对象).
- 残留: 验收者在 `/tmp` 下留下的临时输出 (`/tmp/ts002-ac001.out`, `/tmp/ts002-ac001.err`, `/tmp/ts002-ac002.out`, `/tmp/ts002-ac002.err`) 是自检用临时文件, 不属产品对象, 内容已抄进证据文件; 记为未清理残留, 不影响任何必验项结论.

## 结论

- 逐项: AC-001-1 通过, AC-002-1 通过, BR-001 通过 (静态), AC-003-1 未验证. 无失败项.
- 存在 1 条权限与环境缺口 (AC-003-1), 因此整体不写"全部通过", 该条留给用户裁决.
- 除本次证据目录 (`docs/changes/wordcount/acceptance/round-2/`) 的输出外, 源码与 Spec 未变; 该目录本身是相对目标提交 `89ea49e79ef692ecb667c72c730ea8fa7ba3d872` 的新增未跟踪文件.
- 本报告的结论仍需用户逐项确认, 不等于正式人工验收; 本轮不宣布正式交付, 也不关闭用户验收.
