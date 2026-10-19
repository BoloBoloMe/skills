# 来源, 许可与行为差异

本技能是固定上游版本的复刻与适配, 不是原创. 本文件记录固定来源, 随包许可, 逐项行为差异, translate-a-skill 第 7 节校验材料, 以及行为保真演练入口, 供后续核对.

## 固定来源

- 仓库: `cursor/plugins`, 上游路径 `pstack/skills/blast-radius/SKILL.md`.
- 固定 SHA: `4382e687a50b8d2c5ce4d141d001186589cff8d5`. 不追浮动 main: 上游 main 之后有更新, 本副本以该 SHA 为唯一输入.
- 只读获取命令与结果 (2026-10-19, 无代理):

```bash
curl -sS -m 20 -w "%{http_code} %{size_download}\n" -o /tmp/iss13-upstream/skills_blast-radius_SKILL.md \
  https://raw.githubusercontent.com/cursor/plugins/4382e687a50b8d2c5ce4d141d001186589cff8d5/pstack/skills/blast-radius/SKILL.md
curl -sS -m 20 -w "%{http_code} %{size_download}\n" -o /tmp/iss13-upstream/LICENSE \
  https://raw.githubusercontent.com/cursor/plugins/4382e687a50b8d2c5ce4d141d001186589cff8d5/pstack/LICENSE
```

| 文件 | HTTP | 字节 | 行数 | sha256 |
| --- | --- | --- | --- | --- |
| 上游 `blast-radius/SKILL.md` | 200 | 3856 | 50 | `2e10745b97f5862323dcda3b29ca60d56b5c3c98e37020085d26b48efbe0a436` |
| 上游 `pstack/LICENSE` | 200 | 1067 | 21 | `bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e` |

上游原文副本 (只读抓取, 未改字节) 存于 `docs/changes/verification-skills/evidence/ISSUE-13/upstream/blast-radius-SKILL.md` 与同目录 `pstack-LICENSE.txt`.

## 随包许可

- `workflow/blast-radius/LICENSE` 与上游 `pstack/LICENSE` 逐字节相同, sha256 `bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e`.
- 内容是完整 MIT: 版权行 `Copyright (c) 2026 Lauren Tan`, 授权段, 版权与许可必须随附的条件段, 以及全大写免责段 (无担保, 不承担任何责任).
- 不以作者名或仓库链接代替许可正文: 上述文本就在本包内, 不依赖外部材料.

## 逐项差异表

字段固定为源版位置, 目标版位置, 影响, 处理决定. 每行一条差异, 不把范围缩减藏在普通翻译里.

| 源版位置 | 目标版位置 | 影响 | 处理决定 |
| --- | --- | --- | --- |
| frontmatter `description` 英文触发词清单 ("Use for 'blast radius of X'...", 上游第 3 行) | frontmatter `description` 单行中文摘要, 触发词清单不搬 (本地第 3 行); `disable-model-invocation: true` 上游第 4 行与本地第 4 行逐字相同 | 只改描述措辞; 调用方式没有改变 | 按 DECISIONS D022 把 description 写成一行人类摘要. 不记为调用模式改变: 上游原文第 4 行原本就是用户调用, 本地照抄该行 |
| 标题 `# Blast radius` (上游第 7 行) | 无一级标题, 从引言段开始 (本地第 7 行起) | 少一个 H1 | 保留, 属人工检查结论: 仓库内 SKILL.md 不要求 H1; `check_skill.py` 不检查标题, 标题层级由人工逐行核对, 不借用机检结果 |
| 引言段 "Companion to `how` and `why`" | 无 companion 指针; 历史定位命令内联到第 1 节 | 去掉两个上游 sibling 指针, 规则不丢 | 按 DECISIONS D021 自包含, 不留悬空调用 |
| `## Don't trust your own writeup` 与 `### How sure are you` | 第 3 节 (证据级别 1 到 5) 与第 4 节 (可失败脚本) | 上游 H2 加 H3 拆成两个 H2; 级别序列逐条保留 | 接受: 级别定义与可失败脚本要求仍相邻, 五级文字逐条对应 |
| Step 1 "Use `why` step 2 to pull the PR and commits" | 第 1 节的 5 条 `git log`/`git show`/`git blame` 命令, 再加托管入口读 PR 正文 | 上游指针变成本地可直接执行的命令 | 按 D021 自足; 取不到 PR 材料时写明来源限制 |
| Step 3 框架字面量 ("Solid versus React", microtasks, unmount) | 第 2 节运行时机 (注册时机, 异步, 卸载, 生命周期) | 框架专名改成通用说法 | 接受: 示例不绑定技术栈, 要查的范围 (库源码, 固定版本与本地补丁, JSON, 数据库列, 线格式, 跨语言, feature flag, 三跳下游) 逐项保留 |
| Step 4 "Same rules as `why`" | 第 5 节内联诚实纪律: 真实 `file:line`, 检索空结果也是答案, 不编造调用者或 API | 去掉重复指针, 规则搬到本文件 | 保留: 规则不减, 不改指向外部技能 |
| Step 4 "a search that finds nothing is still an answer" | 第 5 节: 报出实际检索命令与范围, 并说明结论覆盖不到哪里 | 空结果报告要求收紧 | 保留收紧 |
| Step 5 一句 "Write a script or test that runs the real code, run it, and paste what happened" | 第 4 节: 先断言库版本与运行环境, 用 `assert` 或显式非零退出, 脚本全文与输出都留 | 上游一句扩成可失败条件 | 保留收紧: 仍是同一条证明要求, 补的是"判断错会明确失败" |
| Step 6 "run it as an `arena`" 与上游模型指派, Frame/Fan out/Cross-judge/Pick/Graft/Verify 产物流程 | 第 6 节多模型同题调查与 `reference/multimodel.md`, 用 `use-herdr` 与 `llm-select` 承接 | 不搬上游产物流程与模型指派表; 合并规则本地写 (一致取最高证据级别, 分歧并存) | 按 D021 只借"不同模型同题加合并答案" |
| 结尾 "Write it through `unslop`" | 第 7 节按 `reference/report-style-zh.md` 整理中文报告 | 上游英文文风清单不是等价替换 | 按 D021 改写成中文报告规则, 只保留诚实, 去冗, 分事实/推断/未证实 |
| 上游无写入授权句 | 第 4 节: 只读调查直接做, 需要写仓库或跑有副作用的应用时先问 | 新增写入授权边界 | 本地新增, 不改变上游证明要求 |
| 上游无角色句 | 引言: 自己调查并运行是使用者角色; 验收指挥者不能借调用本技能亲自验收 | 新增角色边界 | 按 DECISIONS D025 |
| 上游无单模型缺口处理 | 第 6 节: 只有一款模型可用时写明能力缺口, 已证明事实不改标未证实 | 新增缺口处理 | 本地新增, 不改证据级别强度 |
| 上游无放行句 | 第 7 节: 只交接材料, 不自动合并, 不创建 PR | 新增交付边界 | 按 DECISIONS D024 |
| 结尾 "strip anything private before it goes anywhere public" | 第 7 节 "对外发出前脱敏" | 保留原意 | 保留 |

## 没有搬入的部分

- `how` / `why` 的完整体系; `arena` 的产物流程与模型指派表; `unslop` 的英文风格检查; poteto-mode 的提交, 发布, 自动合并流程.
- 上游按 PR 组织的执行形态: 本技能只交接材料, 不自动合并, 不创建 PR.

## translate-a-skill 第 7 节校验

`check_skill.py` 只查 frontmatter 与名称一致性, 不当标点或翻译忠实性校验器. 忠实性与标点用 translate-a-skill 第 7 节的既有命令, 结果如下 (2026-10-19, 提交见本目录 HANDOFF).

命令 1, 全角标点扫描:

```bash
rg -n "[\x{ff0c}\x{3002}\x{ff1b}\x{ff1a}\x{ff01}\x{ff1f}\x{3001}\x{ff08}\x{ff09}\x{3010}\x{3011}]" workflow/blast-radius/SKILL.md
```

无命中 (rg 退出码 1). 本包 `reference/*.md` 与本文件同样无命中.

命令 2, 残留英文审查 (原样列出命中, 不是要求清零):

```bash
rg -o "[A-Za-z][A-Za-z0-9_./:@|*\-]*" workflow/blast-radius/SKILL.md | sort | uniq -c | sort -rn
```

| 命中 | 保留理由 |
| --- | --- |
| `git`, `log`, `show`, `blame`, `follow`, `oneline`, `grep`, `gh`, `view`, `comments`, `p`, `all`, `S`, `L`, `bash`, `assert`, `pr` | 命令, 参数, 代码字面量, 命令块语言标记 |
| `diff`, `file:line`, `JSON`, `API`, `feature flag`, `true`, `agent` | 技术术语与代码/字段名; `agent` 指本机 agent 运行环境 |
| `PR` | 平台概念, 无稳定中文对应词 |
| `reference/multimodel.md`, `reference/report-style-zh.md`, `blast-radius` | 文件路径与技能名 |
| `name:`, `description:`, `disable-model-invocation:` | frontmatter key |
| `diff.` | 句末的 `diff` 后接 ASCII 句点 |

命令 3, 人工标题结构检查 (只列标题, 判定靠人读):

```bash
rg -n "^(|name:|description:|license:|compatibility:|metadata:|allowed-tools:|disable-model-invocation:|# |## )" workflow/blast-radius/SKILL.md
```

机检与人工检查分列, 不混成一件事:

- 机检: `check_skill.py` 只查 frontmatter 的 `name` 是否为小写 kebab-case 且与目录名一致, 并拒绝 YAML 空值/布尔值/数值这类非文本写法, 不检查标题 (依据 `general/writing-for-llm/SKILL-MECHANICS.md` 第 34 行与脚本实现). 该脚本在本技能上退出码 0.
- 人工: 上面的命令只把 frontmatter 行与标题行列出来, 层级结论靠人逐行读. 人读结果: frontmatter 三行 (`name`, `description`, `disable-model-invocation`) 与七个 H2 标题 (`## 1.` 到 `## 7.`); 没有 H1. 上游两级标题被拍平成顺序编号的七个 H2, 差异与理由见上表.

通读测试: 全文按中文直接可执行, 每个操作步骤的先后顺序无需回看英文; 未发现直译腔或需回看原文才能确定顺序处.

## 行为保真演练

代表场景与对照结论写在 `docs/changes/verification-skills/evidence/ISSUE-13/TS-002-drill.md`, 含临时项目路径与提交, 会话名, 加载方式, 命令与原始输出. 对照口径是本文件的逐项差异表: 演练要确认汉化后仍然只用真实运行的代码证明关键安全事实, 级别与风险/已排除项结构未被削弱.
