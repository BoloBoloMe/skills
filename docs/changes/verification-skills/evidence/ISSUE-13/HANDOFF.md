# HANDOFF: ISSUE-13 两个复刻包的许可, 来源与行为保真

## 交付了什么

- `workflow/blast-radius/LICENSE` 与 `workflow/benchmark-checklist/LICENSE`: 与上游 `pstack/LICENSE` 逐字节相同的完整 MIT 文本 (版权 `Copyright (c) 2026 Lauren Tan`, 授权段, 随附条件段, 全大写免责段), sha256 都是 `bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e`.
- `workflow/blast-radius/reference/PROVENANCE.md`: 由原 `source-record.md` 改名并扩写 (`git mv`), 补固定 SHA `4382e687a50b8d2c5ce4d141d001186589cff8d5` 与不追浮动 main 的声明, 只读抓取命令与 HTTP 200 实测, 15 行逐项差异表 (源版位置, 目标版位置, 影响, 处理决定), translate-a-skill 第 7 节三条命令与结果, 行为保真演练入口.
- `workflow/benchmark-checklist/reference/PROVENANCE.md`: 新建, 同样字段, 16 行逐项差异表.
- `workflow/benchmark-checklist/SKILL.md`: 一处保真补齐 — 补回上游第 3 问的物理上限算式 (每秒字节数对带宽, 每秒操作数乘每操作成本对核心数, 省下的时间对被改动那一段耗时). 理由与处理决定写进它自己的差异表; 已确认的判定词, 交替次数, 错误计数, 例外与完成条件都没有改动.
- 证据目录 `docs/changes/verification-skills/evidence/ISSUE-13/`: 上游原文副本, 抓取记录, 两份切片记录, 两个核对脚本, 红轮失败输出, 四个会话转录, 会话写的证明与测量脚本原件, 夹具重建脚本, 机械检查与全量快层原始输出.

## 每个验收标准对应的证据

| 验收标准 | 证据文件 | 关键原始材料 |
| --- | --- | --- |
| 两个复刻包内均有完整 MIT 版权/许可/免责文本 | `TS-001.md` | 两个 `LICENSE` 与上游 `upstream/pstack-LICENSE.txt` 的 sha256 相同; `check-provenance-artifacts.py` 逐段核对 (checks=50, failures=0) |
| 差异记录含固定 SHA, 源/目标位置, 影响和处理决定 | `TS-001.md`, 两个包内 `reference/PROVENANCE.md` | 15 行与 16 行差异表; `rg -c "4382e68..."` 在两个 PROVENANCE 各命中 3 行 |
| 中文正文通过 translate-a-skill 的标点与语义检查, 强度与例外未削弱 | `machine-checks.log` 第 4 到第 6 节 | 全角标点 hits=0; 残留英文逐条保留理由在两个 PROVENANCE; 标题结构为 frontmatter 三行加七个 H2 / 一个 H1 加十一个 H2; 语义核对发现的物理上限算式缺口已补齐并单列 |
| 两个复刻各跑一个代表场景, 实际行为与差异记录一致 | `TS-002-drill.md` | `sessions/*.jsonl` (绿轮两个会话), `red-round/*.jsonl` (红轮两个会话), `drill-artifacts/blast-green-probe.py`, `drill-artifacts/bench-green-measure.py`; 对照表逐行给差异表条目与实际表现 |
| 校验命令与结果可复核, 不以 `check_skill.py` 冒充翻译校验 | `machine-checks.log` | `check_skill.py` 只用于 frontmatter (两处 exit 0); 标点与残留英文用第 7 节命令; `check-drill-evidence.py` 核对演练记录 (checks=39, failures=0) |

## 跑过的命令与退出码

- `test -f workflow/blast-radius/LICENSE && test -f workflow/benchmark-checklist/LICENSE` -> exit 0.
- `rg -c "4382e687a50b8d2c5ce4d141d001186589cff8d5" <两个包的 LICENSE 与 PROVENANCE>` -> 4 处命中, exit 0; `rg -c "Copyright \(c\) 2026 Lauren Tan" <两个 LICENSE>` -> 2 处, exit 0.
- `uv run python general/writing-for-llm/check_skill.py workflow/blast-radius/SKILL.md` -> `OK`, exit 0; 同命令对 `workflow/benchmark-checklist/SKILL.md` -> `OK`, exit 0.
- 全角标点扫描 (translate-a-skill 第 7 节命令 1): 两个 `SKILL.md`, 两个 `reference/PROVENANCE.md`, 本目录三个中文文档, 以及两个包与证据目录的全文件扫描 (排除 `*.jsonl` 与 `*.log`) -> hits=0.
- 残留英文审查 (命令 2): 命中集合与保留理由见两个 `PROVENANCE.md`; 都是命令, 代码, 路径, 指标单位, 平台缩写或 frontmatter key.
- 标题结构 (命令 3): 见 `machine-checks.log` 第 6 节.
- `uv run python docs/changes/verification-skills/evidence/ISSUE-13/check-provenance-artifacts.py` -> `checks=50 failures=0`, exit 0 (开工时 `checks=19 failures=11`, exit 1).
- `uv run python docs/changes/verification-skills/evidence/ISSUE-13/check-drill-evidence.py` -> `checks=39 failures=0`, exit 0 (开工时缺演练报告, exit 1).
- `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` -> `7 passed, 18 subtests passed`, exit 0.
- `uv run --with pytest python -m pytest -m "not e2e" -q` -> `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed in 276.01s`, exit 1. 6 个失败是 `general/present/tests/test_browser_session.py` 5 个与 `tests/test_mailbox_admin.py::test_pending_cap_drops_oldest` 1 个, 都是 socket TimeoutError, 与 ISSUE-09 记录的既有失败集合一致, 不比开工时多; 原始输出 `full-suite.log`.

## 会话, 临时项目, 清理

- 宿主与运行时: Ubuntu 26.04.1 LTS x86_64, 16 核; pi 版本 1.3.0, herdr 0.9.4, Python 3.14.7.
- 会话: `br13-g1` (blast-radius 绿轮, tab `w1E:t12`, pane `w1E:p12`), `bm13-g1` (benchmark-checklist 绿轮, tab `w1E:t11`, pane `w1E:p11`), `br13-red` (红轮一, tab `w1J:t4Q`, pane `w1J:p4S`), `br13-red2` (红轮二, tab `w1J:t4S`, pane `w1J:p4V`).
- 模型与思考档位: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 启动参数 `pi --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`; `-a` 只做本次项目信任, 未改任何全局配置.
- 提交渠道: `herdr pane send-text <pane> '<任务>'` + `herdr agent send-keys <名> "alt+\\"`.
- 临时项目: `/tmp/orchestra-13/lab` (起始提交 `bb5902c`), `/tmp/orchestra-13/red-lab` (起始 `e248487`), `/tmp/orchestra-13/red2-lab` (起始 `a94b619`); 夹具本体提交 `f8ec59a`, 可用 `setup-fixture.sh` 重建.
- 加载方式: 临时项目 `.agents/skills/<名>/` 放交付版副本, 项目 cwd 内用 `/skill:<名>` 点名加载; 会话转录带 `<skill name="..." location="/tmp/orchestra-13/<项目>/.agents/skills/<名>/SKILL.md">`, 即实际来源.
- 清理: 四个演练 tab 全部关闭, 关闭后 `herdr agent list` 与 `herdr tab list` 里没有 `br13-*` / `bm13-*`; 三个临时项目在证据抄完后删除 (`rm -rf /tmp/orchestra-13`). 演练项目 `git status --short` 在收尾时为空, 会话只在仓库外 `/tmp` 写临时脚本.

## 缺口, 风险, 未验证

- 红轮不对称: blast-radius 的变异版二删掉证据级别与交接里的证明要求后, 报告丢掉五级证据级别标注, 被抓到偏离; 变异版一只删两节, 行为没有偏离 (技能内部冗余兜住), 如实记录. benchmark-checklist 没有跑变异版会话, 它的红轮只由"缺可对照记录"的静态检查承担.
- `workflow/benchmark-checklist/SKILL.md` 的物理上限算式是本次补回的, 属语义核对发现的保真缺口; 这次改动落在已确认的技术要求内, 但没有为本条新增会话演练, 只有绿轮的整体行为覆盖.
- 演练全部用受控夹具 (`time.sleep` 与小型字典索引, 4000 行), 只证明方法与判定流程, 不代表任何真实产品性能; 对外引用前须在真实实现上复测.
- 多模型同题调查在演练里没有做: 绿轮按影响面判窄走单路, 并写明 `llm-select` 里只有当前这款有评分. 该缺口是演练材料缺口, 不是技能行为缺失.
- 只在单一宿主与 pi 1.3.0 + herdr 0.9.4 上验证; 未运行 `sync-to-pi.py`, 未写 `~/.agents` 或 `~/.pi`, 结论不覆盖全局部署已生效.
- 原始会话转录与部分原始输出里有全角标点与英文残留, 按原始材料原样保留, 未改写; 全角标点扫描的范围是两个技能包与本目录中文文档.

## 提交

- 提交: 分支 `issue/13` 顶端的 `feat: ISSUE-13: 两个复刻包补齐 MIT 许可, 固定来源差异记录与行为保真演练` 提交, 本报告随该提交入库; 实际哈希以 `git log --oneline -1 issue/13` 为准. 开工基线 `e922bfe`.
- 开工基线: `e922bfe`; 工作区在本报告写入前后均保持干净 (证据目录内的原始材料已随提交入库).
