# ISSUE-23 交接: blast-radius 被动句残留与 PROVENANCE 节数/节号

## 交付了什么

1. `workflow/blast-radius/SKILL.md:24` 命令注释 "符号被增删的历史提交" 改为 "找到增删该符号的提交". 这是 H3 点名的最后一处非警告 "被" 残留.
2. `workflow/blast-radius/reference/PROVENANCE.md` 修正 N2:
   - 人工核对结论从 "七个 H2 (`## 1.` 到 `## 7.`)" 改成 "八个 H2", 并按正文顺序逐个列出八个现有节名; "上游两级标题被拍平" 改为主动句 "改为顺序编号的八个 H2".
   - 逐项差异表的目标版位置一律写成 "第 N 节 (现有节名)", 节号按现有正文修正: 诚实纪律与空结果两条从旧 "第 5 节" 改为第 6 节 (风险与已排除项); 多模型两条从旧 "第 6 节" 改为第 7 节 (大或宽变更用多模型同题调查); 报告整理/脱敏/放行两条从旧 "第 7 节" 改为第 8 节 (交接). 其余行补上节名, 便于机械对照.
   - 残留英文保留理由表补 `TC` 一行 (正文第 5 节 "非正式 TC" 沿用), 使命令 2 的每个命中都有理由.
   - "行为保真演练" 段 "结构未被削弱" 改为 "结构都没削弱".
3. `workflow/blast-radius/reference/multimodel.md:3` 同一禁字规则:"改了被下游共享的线格式" 改为 "改了与下游共享的线格式", 语义不变 (H3 依据的 translate-a-skill 第 2 节第 2 刀要求全文禁 "被").
4. 新增本目录: 两个可重跑脚本与红/绿/机械检查证据.

未改: 许可文本, 固定 SHA, 借用范围, 其它技能, PRODUCT/TECHNICAL/DECISIONS/Spec, 全局部署副本. 未运行 `sync-to-pi.py`, 未勾选任何复选框.

## 每个验收标准对应的证据

| 验收标准 | 证据文件 | 结论 |
| --- | --- | --- |
| 被动句残留已改, 有扫描证据 | `red-ts001.log` (改前 4 处命中, exit 1), `green-ts001.log` (改后 0 命中, exit 0) | 通过 |
| 差异记录节数与节名与正文一致, 有对照证据 | `red-ts002.log` (改前 24 项不符, exit 1), `green-ts002.log` (改后 0 项不符, 打印八个节号加节名, exit 0) | 通过 |

TDD 切片对照:

- TS-001 接缝=正文文风. 红: `scan-passive.py` 在 `workflow/blast-radius/` 扫到 4 处 "被" (SKILL.md:24, PROVENANCE.md:95,101, multimodel.md:3), exit 1. 绿: 同命令 0 命中, exit 0.
- TS-002 接缝=差异记录准确性. 红: `check-section-refs.py` 报 "人工结论称 七个 H2, 正文实际 8 个", 八个节名全未列出, 差异表 13 处节引用没带节名或节号对不上, 共 24 项, exit 1. 绿: 0 项, exit 0.

## 跑了哪些命令与退出码

证据里的原始输出见 `machine-checks.log`, `full-suite-summary.log`, 红绿日志.

| 命令 | 退出码 |
| --- | --- |
| `uv run python general/writing-for-llm/check_skill.py <worktree>/workflow/blast-radius/SKILL.md` | 0 (`OK`) |
| `rg -n "[\x{ff0c}\x{3002}...]" workflow/blast-radius` (全角标点扫描) | 1 (无命中, 符合预期) |
| `rg -o "[A-Za-z]..." workflow/blast-radius/SKILL.md \| sort \| uniq -c` | 0, 命中逐项对照 PROVENANCE 保留理由表 |
| `rg -n "^(|name:...|# |## )" workflow/blast-radius/SKILL.md` | 0, 三个 frontmatter 行加八个 H2, 无 H1 |
| `uv run python evidence/ISSUE-23/scan-passive.py workflow/blast-radius` | 0 (改前 1) |
| `uv run python evidence/ISSUE-23/check-section-refs.py` | 0 (改前 1) |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 6 failed, 659 passed, 2 skipped, 103 deselected; 失败集合与 `../BASELINE.md` 完全相同, 不超基线 6 条 |

脚本不打磨输出: 两个脚本只做机械比对 (扫 "被" 字, 解析 `## N. 名` 与 "第 N 节 (名)"), 结论靠人读日志.

## 会话名与临时项目路径

无. 本 ISSUE 是文本修订, ISSUE 文件明确 "不要求真会话演练", 因此未开 herdr 会话, 未建 `/tmp/orchestra-23/` 临时项目. 依据是本 ISSUE 的专属要点 ("小范围文本修订, 不要求真会话演练, 要节名对照证据与扫描结果"), 覆盖依据只有 STANDARDS-2 的 H3 未闭合部分与 N2, 不涉及行为保真.

## 缺口 / 风险 / 未验证项

1. 未做行为演练: 只改命令注释与来源记录, 不改规则语义, 所以没有真实 pi 会话证据. 若评审要求行为证据, 需另开 ISSUE.
2. `check-section-refs.py` 只核对节号与节名是否对得上正文, 不判断差异表 "影响/处理决定" 两列内容是否仍然准确. 那两列本次未改.
3. 节名带全角以外的正常中文, 脚本按字面逐个匹配; 以后改节名必须同时改 PROVENANCE, 否则脚本会红. 这正是想要的效果, 但会挡住只改标题的提交.
4. 全量快层的 6 条失败是开工基线既有 (present 浏览器套接字超时, mailbox 超时), 与本次改动无关; 未逐条复跑确认环境原因.
5. 未检查 `docs/changes/verification-skills/` 里其他文档对 blast-radius 节号的引用 (范围外, 且扫描显示除 PROVENANCE 外无 "第 N 节" 引用).

## 提交哈希

见下方 `git log -1 --format=%H` 的最终值:
`__COMMIT__`
