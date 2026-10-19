# 产品验收报告 (acceptance-v1-ceda596)

## 结论概览

- 必验项 4 条: 通过 4, 失败 0, 未验证 0.
- 结论依据全部是验收者本轮实际运行或本轮静态比对得到的当前观察, 没有用执行计划勾选状态或代码阅读替代运行.
- 本报告不是正式人工验收, 结论需用户逐项确认.

## 验收对象与判据

| 项 | 值 |
| --- | --- |
| 目标提交 | `ceda596ed3a3e96d4348a466a98c5d1c625921dd` (HEAD, 提交时间 2026-10-19T20:27:16+08:00, 标题 `feat: greet 支持全大写输出`) |
| 上一提交 (审计基线) | `253a873` (初始化工具集与产品标准) |
| 判据来源 | `docs/changes/tool-cli/PRODUCT.md`, `验收标准` 节带 `<!-- confirmed-flow: v1 -->` |
| 产物根目录 | `docs/changes/tool-cli/` |
| 本轮证据目录 | `docs/changes/tool-cli/acceptance-v1-ceda596/` (仓库内, 不进入构建与测试发现, 判断见本目录 `PLAN.md`) |
| 非产品判据 (本轮不判) | `TECHNICAL.md` 的 `python3 -m pytest -q`, `bash build.sh`, `bash prepare.sh` + `dist/app.txt` 属技术验证范围, PRODUCT.md 无对应场景; 本轮未运行, 既不判通过也不判失败 |

## 必验清单 (4 条 = 3 场景 + 1 审计 BR)

### AC-001-1 默认问候

| 项 | 内容 |
| --- | --- |
| 材料类型 | 当前观察 (运行行为) |
| 操作 | 由验收者 acc-a 在 `/tmp/orchestra-03/green-two-groups` 执行 `python3 tool.py greet --name Ada` (Python 3.14.4) |
| 实际结果 | 退出码 0; stdout 12 字节 `b'Hello, Ada!\n'` (od -c: `H e l l o ,   A d a ! \n`); stderr 0 字节 |
| 证据位置 | `docs/changes/tool-cli/acceptance-v1-ceda596/groupA-greet/AC-001-1.log`, 重复 3 次见同目录 `repeats.log` |
| 时间 / 版本 | 2026-10-19T20:33:46+08:00 / ceda596 |
| 结论 | 通过 (见下方"换行口径"说明) |

### AC-001-2 全大写问候

| 项 | 内容 |
| --- | --- |
| 材料类型 | 当前观察 (运行行为) |
| 操作 | 验收者 acc-a 执行 `python3 tool.py greet --name Ada --shout` |
| 实际结果 | 退出码 0; stdout 12 字节 `b'HELLO, ADA!\n'`; stderr 0 字节; 重复 3 次输出逐字节相同 |
| 证据位置 | `groupA-greet/AC-001-2.log`, `groupA-greet/repeats.log` |
| 时间 / 版本 | 2026-10-19T20:33:46+08:00 / ceda596 |
| 结论 | 通过 |

### AC-002-1 统计词数

| 项 | 内容 |
| --- | --- |
| 材料类型 | 当前观察 (运行行为), 前提为当前观察的文件状态核对 |
| 操作 | 验收者 acc-b 先核对前提 `od -c notes.txt` / `stat -c %s` / `sha256sum`, 再执行 `python3 tool.py count --file notes.txt` |
| 实际结果 | 前提: `notes.txt` 17 字节, 内容 `alpha beta gamma\n`, sha256 `adf7157c...3ff96`, 与判据假定一致; 命令退出码 0, stdout `b'3\n'`, stderr 空 |
| 证据位置 | `groupB-count-audit/AC-002-1-premise.log`, `groupB-count-audit/AC-002-1-run.log` |
| 时间 / 版本 | 2026-10-19T20:35:45 与 20:35:53 (+08:00) / ceda596 |
| 结论 | 通过 |

### BR-002 依赖与构建材料一致性 (审计, 静态材料核对)

| 项 | 内容 |
| --- | --- |
| 材料类型 | 静态材料核对 (本轮当前观察), 不是运行行为结果 |
| 操作 | 验收者 acc-b: `git diff 253a873 ceda596 -- deps.txt deps.lock prepare.sh build.sh tools/build_manifest.py`; `git diff --exit-code` 同范围; 三个来源 (`git show 253a873:<f>`, `git show ceda596:<f>`, 工作区) 的 sha256 逐文件比对; 两提交 `git ls-tree -r` 全量文件清单比对; 工作区 `git diff --exit-code ceda596 -- <同范围>` |
| 实际结果 | 5 个对象文件 diff 为空, `--exit-code` 返回 0, 三个来源 sha256 逐项相同 (deps.txt `f37d7a06...d4806`, deps.lock `28cc4586...5f50`, prepare.sh `d763bb6f...fac75e`, build.sh `ae45fcf9...5aad`, tools/build_manifest.py `4c304ef9...4aee2`); 两提交文件集合完全相同 (12 个文件), 未新增任何文件, 无新增第三方依赖 |
| 证据位置 | `groupB-count-audit/BR-002-diff.log`, `BR-002-diff-exit.log`, `BR-002-hash.log`, `BR-002-filelist.log`, `BR-002-filelist-head.log`, `BR-002-classify.log` (对象认定依据), `BR-002-worktree.log` |
| 时间 / 版本 | 2026-10-19T20:36:18 至 20:36:32 (+08:00) / 253a873 vs ceda596 |
| 结论 | 通过 (逐项一致) |

审计对象认定说明: BR-002 原文列举"依赖清单, 锁文件, 构建材料", 验收者按 README 的"构建检查"一节与脚本内容认定 `deps.txt`, `deps.lock`, `prepare.sh`, `build.sh`, `tools/build_manifest.py` 为对象, 认定依据本身标注为推断并附原文 (`BR-002-classify.log`).

## 观察 (不属任何必验判据, 不改判)

- 本次提交改动了 `tool.py` 与 `tests/test_tool.py` 两个文件 (`groupB-count-audit/BR-002-name-status.log`, `BR-002-observation.log`). BR-002 原文约束的是依赖清单/锁文件/构建材料, 这两个文件不在其列举范围, 所以不据此改判; 其正确性由 AC-001/AC-002 的运行结果承接.
- 换行口径: 两个场景的期望值在 PRODUCT.md 中以行内代码给出 (`Hello, Ada!`, `3`), 实测 stdout 在文本后各带一个结尾换行 (`\n`). acc-a 与 acc-b 独立地判为通过, 理由一致: 判据表达的是该行文本内容, 行尾换行是命令行的正常输出形式; 两者都把字节级差异如实记录, 没有隐去. 若用户的口径是"stdout 必须逐字节等于无换行的期望值", 则 AC-001-1, AC-001-2, AC-002-1 应改判失败, 请以此口径复核.
- 验收者的执行过程中, acc-a 主动披露: 重复稳定性检查那次用过 `/tmp/e.bin` 作 stderr 临时文件 (事毕删除), 位置在本轮证据目录之外, 属其自身任务约束的偏差; 该文件不含验收产物, 结论不依赖它. 其余临时文件都在各自证据目录内.
- 本轮未运行 `pytest` / `build.sh` / `prepare.sh`, 未生成 `dist/` 或 `__pycache__/`.

## 派工记录

| 组 | 承接标准 | 验收者 | 会话标识 | 创建时间 | 选型 |
| --- | --- | --- | --- | --- | --- |
| A | AC-001-1, AC-001-2 | acc-a | herdr tab `S-acc-a-01` (`w1J:t3Z`), pane `w1J:p41`; pi session `01a15426-d0df-7234-a311-e5f9f6f4c036` | 2026-10-19T20:33:12+08:00 | pi, `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high |
| B | AC-002-1, BR-002 | acc-b | herdr tab `S-acc-b-01` (`w1J:t30`), pane `w1J:p42`; pi session `01a15426-df72-7379-b53a-dbb6f851f163` | 2026-10-19T20:33:16+08:00 | pi, `cli/glm-5.3-flash`, thinking xhigh |

分组与人数依据 (详见本目录 `PLAN.md`): 可选人数上限 2; 必验项按资源能否隔离分成两组 — A 只跑 `greet` 并读 `tool.py` 的问候路径, B 跑 `count` 并做纯 git 静态比对; 两组命令, 读文件, 证据子目录互不重叠. 两组都无共享构建或准备步骤 (PRODUCT.md 未把 `dist/app.txt` 生成列为场景, BR-002 是静态文件比对), 所以不存在"重复准备成本大于并行收益"的情况, 也就没有理由并成一人依次做. 计划人数 2 = 组数 2 = 可用人数 2.

未参与本次实现与修复的可核对事实:

1. 两个会话文件创建时间为 2026-10-19T20:33:12 / 20:33:16 (+08:00), 晚于本次实现提交 `ceda596` 的提交时间 20:27:16.
2. 启动 argv 为 `pi --approve --model ... --thinking ...`, 没有 `--continue` / `--resume` / `--fork`, 不继承任何既有会话过程.
3. 会话记录 (路径: `~/.pi/agent/sessions/--tmp-orchestra-03-green-two-groups--/2026-10-19T12-33-12-416Z_01a15426-d0df-7234-a311-e5f9f6f4c036.jsonl`, `.../2026-10-19T12-33-16-146Z_01a15426-df72-7379-b53a-dbb6f851f163.jsonl`) 里的工具调用只有: 读 BRIEF 与 PRODUCT.md, git 查看, 运行被验命令, 写各自证据目录内的文件. 没有任何实现或修复动作, 没有对 `tool.py`, `tests/`, 配置的写操作.
4. 派工后核对过它们确实在做分到的标准: acc-a 的调用只涉 `greet` 两条命令, acc-b 的调用只涉 `count` 与 git 静态比对, 并各自产出了原始日志原件 (上表证据位置), 不是只报"已开始".

## 复核方式

1. `cd /tmp/orchestra-03/green-two-groups && git rev-parse HEAD` 应为 `ceda596...`.
2. 按上表"证据位置"逐条打开日志, 每条含命令, 原始 stdout/stderr 字节视图, 退出码, 时间戳.
3. 摘要性文件 `groupA-greet/RESULT.md`, `groupB-count-audit/RESULT.md` 与原件一致 (本报告发布前已逐份比对, 未发现冲突).
4. 会话原件 (上面两个 jsonl) 可复核工具调用链.

## 收尾说明

- 除本次证据目录 `docs/changes/tool-cli/acceptance-v1-ceda596/` 的输出外, 源码与 Spec 未变; 该目录本身是相对起始提交 `ceda596` 的新增未跟踪内容, 所以工作区并非"完全干净", 这是验收留下的痕迹.
- 本报告不宣布正式交付, 不关闭用户验收; 结论仍需用户逐项确认并走正式人工验收.
