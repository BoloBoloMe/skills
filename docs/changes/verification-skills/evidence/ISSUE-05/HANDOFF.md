# ISSUE-05 交接报告

## 交付了什么

在既有 `workflow/verify-change/SKILL.md` 上增量补齐两个切片, 没有推翻 ISSUE-01..04 已实现部分, 没有新建或修改任何项目级配方:

- AC-009 旧证据适用性:
  - 第 3 步: 输入中途变宽时, 旧报告只覆盖旧 PRODUCT.md 版本与旧起始提交, 不追认新场景; 新场景要等调用方指定包含它的已提交干净目标再派发, 目标没重新指定就不拿新输入悄悄验收.
  - 第 4 步: 派工计划给每条必验项定材料来源, 条件仍适用的旧观察标为引用旧观察并带上原检查时间, 提交版本, 可复核位置与适用条件, 不叫验收者重跑; 条件变了或本来没有观察的才本轮实跑.
  - 第 7 步: 适用性逐项核对覆盖范围与代码, 依赖, 配置, 环境, 不能因为同一台机器就当作没变; 只改说明材料时说明这一点, 直接引用且不为无关改动重跑; 条件变化按影响重跑, 旧结论不当本次通过依据; 条件失效且缺依赖服务时标受阻并写明缺什么.
  - 第 8 步: 引用旧观察的行内写原检查时间, 提交版本, 位置与适用条件, 并说明本轮哪处改动不影响它.
- AC-010 项目配方选择与过时配方处理:
  - 第 5 步: 派工前定位项目验证配方的实际文件与本次可用加载入口, 写进派工单; 用户点名调用过不等于进了自动触发列表, 入口必须是项目里当前这份文件; 没有配方就如实写没有.
  - 第 6 步: 没配方时按 PRODUCT.md 与项目已有可靠入口操作, 缺 TECHNICAL.md / EXECUTION.md 不是受阻理由, 也不是自动生成配方的借口; 按配方得不到可用实例时先核健康, 版本与实例归属, 确认是配方步骤对不上就报操作缺口, 写明已试路径, 卡点与现象; 操作缺口与产品缺陷分开记, 配方不由验收方改.
  - 边界一节: 明确不生成或修改项目级验证配方.
- 新增 `docs/changes/verification-skills/evidence/ISSUE-05/`: 夹具脚本, 3 个技能版本原件与差异, 3 次红演练, 4 次有效绿演练 (含复验与输入变化), 夹具快照, 会话 jsonl 原件, 说明与清理记录.
- 未改 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` 与既有 Spec; 未改其他既有技能与 `general/`; 未写全局部署副本; 未运行 `sync-to-pi.py`; 未在 ISSUE 文件或 EXECUTION.md 勾选复选框; 演练目标项目没有改产品代码, 配置或测试 (只有证据目录新增与 gitignore 内运行产物).

## 每个验收标准对应证据

| 验收标准 | 证据文件 |
| --- | --- |
| 旧证据复用带原时间/版本/位置和适用条件 | `drill-green-009-r1/REPORT.md` 第 2 节 (旧观察 `board-dep-1.2-run`, 原检查时间 `2026-10-19T15:19:48Z`, 提交 `1dbbbe1`, 逐文件 blob 比对, 说明只改 2 行交接说明); 逐项表 BR-001 行; `drill-green-009-r3/REPORT.md` AC-003 行引用上一轮原输出 |
| 条件变化时重跑受影响场景, 失效且不可运行时受阻 | `drill-green-009-r2/REPORT.md` "旧观察的适用性 (未引用为通过依据)" 与逐项表 AC-002 (dep 1.3), AC-003 (未验证, 缺 18290 relay); `drill-green-009-r3/REPORT.md` AC-003 行; 原件 `drill-green-009-r2/06-ac003-sync.txt`, `drill-green-009-r3/07-ac003-relay-precondition.txt` |
| 无配方时按 Product 和项目可靠入口继续 | `drill-green-010-norecipe/90-report.md` (无 TECHNICAL/EXECUTION/配方, 按 README 跑完 3 项); 项目 `.agents/skills/` 里没有新生成的配方 |
| 过时配方报告为操作缺口, 不记为产品缺陷, 不私自修改 | `drill-green-010-stale/VERIFICATION-REPORT.md` "操作缺口 (不产生判据)"; 原件 `drill-green-010-stale/recipe-attempt-18001.txt`; 配方 md5 演练前后同为 `d7bb9590b4358f9695f87a39ac9ba50e` |
| AC-009-4 输入变化 (附带) | 负半: `sessions/board-r2/2026-10-19T15-46-47-123Z_01a154d8-0ad3-775e-...jsonl` 与 `drill-green-009-r2/REPORT.md` "验收后输入变更(不追认)"; 正半: `drill-green-009-r3/REPORT.md` (新目标 `5f9544d`, 新证据目录, 新开非作者验收者, AC-004 实跑) |

红演练与作废轮次的说明见 `README.md` 的"红演练"与"环境干扰与作废轮次"两节.

## 跑了哪些命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` | 0 | `workflow/verify-change/SKILL.md: OK` |
| 全角标点扫描 (grep -P 全角逗号句号顿号分号冒号叹号问号括号引号书名号一类的字符类), 对 SKILL.md 与 6 个自写证据文件 | 0 | 全部 0 命中; 会话原始记录与工具自动生成的夹具产物保留原样, 未做改写 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | 7 passed, 18 subtests passed |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed in 274.92s`; 失败集合与 `evidence/BASELINE.md` 完全一致 (present 5 条 + mailbox pending_cap 1 条), 未新增失败 |
| `bash setup-drills.sh init / rebuild-board / new-min / install-skill / install-recipe / remove-relay / status` | 0 | 建 8 个临时项目, 各带起始与目标提交; 部署方 relay 文件在造完旧证据后删除 |
| `uv run workflow/to-spec/ac-draft.py preview / promote`, `uv run workflow/to-spec/check-ac.py` | 0 | 每个夹具的 PRODUCT.md 都是真实转正 (带 `<!-- confirmed-flow -->`), `check-ac` 通过; AC-004 新增后为 4 个场景 |
| `herdr tab create` / `agent start` / `pane send-text` / `agent send-keys` / `agent read` / `tab close` | 0 | 会话一览见 `README.md`; 收尾 `logs/agents-final.json` 与关闭后复查均无本 ISSUE 存活会话 |

## 会话与临时项目

- 有效会话: 红 `i05-red009`+`acc-r1`, `i05-red009b`+子验收者, `i05-red010`+两轮子验收者; 绿 `i05-g009r1`+`01a154d4-fe1a`, `i05-g009r2`+`r2-verifier`+`r2-verifier2`, `i05-green010a`+`verify-board-r1`, `i05-green010c`+`acc-stalerecipe2-r1`. 会话 id 与记录目录见 `README.md`.
- 作废轮次: `i05-green009`+`acc-board-r1` (目标与 HEAD 不符, 按第 2 步正确停下; 之后同项目 v2 版重跑列入 `drill-green-009-r1-v2-draft/`), `i05-green010b`+两名子验收者 (首次因派工单要求空工作区停下, 再次因 18201 被并发 board 实例占用而整轮未验证).
- 临时项目: `/tmp/orchestra-05/{board,board-r1,board-r2,norecipe,stalerecipe,stalerecipe2,red-board,red-board2,red-stalerecipe}`, 各夹具提交见 `README.md` 夹具表与 `fixtures/*/git-log.txt`. 证据抄完后已整体删除, 记录在 `logs/cleanup.txt`.
- 宿主与版本: Ubuntu 26.04, herdr 0.9.4, pi 1.3.0, Python 3.14.7 / 3.14.4; 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high, 启动带 `-a`.
- 实际加载来源: `logs/loaded-locations.txt` 从每个会话 jsonl 抽出 `<skill location=...>` 与 md5, 红演练对上 v1, AC-010 绿演练对上 v2, AC-009 绿演练对上 v3.

## 缺口与风险

1. **红演练形态与预期不完全一致**: 旧版不是"无条件复用旧通过结论", 而是"一律重跑, 不做适用性判断"; 只有在被明确点名配方时才处理过时配方. 证据按实际行为记录, 没有为了贴合预期改夹具. 因此本 ISSUE 新增的规则是"条件仍适用就复用并引用"和"默认采信项目配方并按操作缺口分类", 不是从零建立能力.
2. **AC-009-1 与"只重跑受影响场景"的比较弱**: 条件完全没变的轮次里, 验收者仍然把 AC-001/AC-002 复跑了一遍 (报告同时给出旧观察引用). 这符合 AC 文字 (复用并引用确实出现), 但没有证明"绝不重跑"; 若要更强的效率证据, 需要多轮同类任务的对照, 本轮没做.
3. **技能版本与演练对应**: AC-010 的绿演练用 v2, AC-009 用 v3, 提交版是 v4. v2 到 v3 只加第 4 步一句与第 8 步一句 (`logs/skill-diff-v2-v3.txt`), 第 5, 6 步逐字相同; v3 到 v4 只把第 7 步那两段移到四条材料类型之后, 文字未改 (`logs/skill-diff-v3-v4.txt`, 行集合相同). 所以两条 AC 的结论对提交版成立, 但严格说是在 v2/v3 上跑出来的, 没有在 v4 上重跑.
4. **环境干扰**: 并发夹具共用产品标准里钉死的 18201 端口, 造成两轮作废 (已如实记录). 后续同类演练应一开始就给每个夹具分配独立端口; 本轮 stalerecipe2 用 18321 重建后才拿到干净证据.
5. **git 工具钩子**: 操作者一次 `git reset --hard` 被 git-operation-gate 拦下, 之后改用克隆到目标提交的方式准备夹具, 没有再用 reset; 这不影响演练结论, 但说明夹具重建方式依赖宿主权限配置.
6. **样本少**: 每个场景基本一次运行, 未重复抽样, 不说明成功率; 没有测其他模型 (子验收者换过一次模型, 但那是选型结果, 不是对照实验).
7. **未验证**: 其他运行时或全局部署下的加载与行为; 需要真实部署方 relay 服务才能覆盖 AC-003 的成功分支; tdd-as-orchestra 的接入 (ISSUE-14); 配方维护器 (ISSUE-12) 与本 skill 的配方过时分类是否一致 (本轮只在本技能内规定判据, 未做跨技能对照).

## 提交哈希

- 实现与证据提交: 见本报告所在分支最新提交 (`feat: ISSUE-05: 旧证据适用性与项目配方选择切片及演练证据`). 实现与证据提交哈希: `1c22911d8bc318e7986d0555b8981877cb953137`.
