## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已完成
## 要交付什么
`workflow/prototype/` 整个目录改为 `workflow/demo/`, 三份正文按演示语义重写: frontmatter 与 description 换成演示用途, 适用范围句划清"演示成品不调用本 skill", 通用规则 1/5/6 按"不进产品, 可保留回看, 验证止于能演示"改写, 三子形态的路径/前缀/路由/分支只把 `prototype` 这个词换成 `demo`, 三处清理义务换成"由仓库主人点名删除", 正文不出现 PoC. README 技能表那一行同步.

具体:
1. `git mv workflow/prototype workflow/demo`; 目录里仍是 `SKILL.md`, `LOGIC.md`, `UI.md` 三个文件.
2. `workflow/demo/SKILL.md`:
   - frontmatter: `name: demo`; description 重写为演示用途 (让人看清某个样子, 行为或过程), 保留 `disable-model-invocation: true`.
   - 适用范围句写明: 拿已交付的成品或线上系统演示时不调用本 skill, 直接跑成品 (D004). 全文不出现 PoC 字样.
   - 规则 1 改为: 演示材料不进产品, 不承诺交付, 可以保留回看; 保留"一眼认出是演示材料"的标记要求, 去掉"注定被丢弃"的定位; 写明代理不主动删除演示材料, 需要清理时由仓库主人点名删除对象.
   - 规则 5 捕获改为四项: 演示了什么, 想请仓库主人据此判断什么, 材料位置, 相关 issue 指针. 不写"归档并清理"口吻.
   - 规则 6 改为"验证止于能演示, 其余由我驱动", 不再写"验证止于冒烟".
3. `workflow/demo/LOGIC.md`: 第 7 行路径改 `docs/changes/<feature-slug>/demos/<demo-name>/`; 第 62 行"合并主干前由人类清理"换成与"材料可保留回看, 清理由仓库主人点名"一致的说法.
4. `workflow/demo/UI.md`: 子形态判定顺序照旧 (A 贴现有页面优先, 仅当没有邻近宿主页面才用 B, 没有前端项目时降级 C) 并写清; `prototype.` 前缀改 `demo.` (第 17, 23 行), 第 22 行路由名改含 `demo`, 第 58 行路由改 `/demo/<name>`, 第 23 行多文件子目录改 `demo/`, 第 31 行路径改 `demos/<demo-name>/`, 第 84 行变体集分支改 `demo/<feature-slug>`; 第 82 行"失败变体和 switcher 从工作分支删除"与第 85 行"合并主干前由人类清理"改为不主动删除, 清理由仓库主人点名; 保留"切回工作分支后这些文件不在工作树里"的事实陈述, 去掉删除义务语气.
5. `README.md` 第 54 行: 链接改 `workflow/demo/SKILL.md`, 名称与用途写演示.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-001, AC-004, AC-010, AC-016 (README 部分), AC-018, AC-019, BR-006, NG-002, NG-003.
- Technical: `../TECHNICAL.md`, 模块划分 (workflow/demo/ 条目), 模块接口 (SKILL.md frontmatter 不变量).
## 相关决策
- `../../milestone-03/DECISIONS.md`: D001 (改名不留别名, 历史文件原样), D002 (三子形态落位只换词), D004 (demo skill 只管造材料, 成品演示不调用, 不提 PoC), D005 (创建条件扩到需要看清样子/行为/过程), D017 (完成标准与成品演示一行摘要), D019 (材料与分支不主动清理, 删除由仓库主人点名).
- `../../milestone-01/DECISIONS.md`: D006 (demo 是演示用途, 不新增产品交付承诺).
## 允许范围
- `workflow/demo/`: `SKILL.md`, `LOGIC.md`, `UI.md`.
- `README.md`: 技能表 demo 一行.
## 禁止范围
- 不改三子形态的判定顺序与落位规则, 不新建 `poc` skill (NG-003).
- 不删改 `docs/changes/*/prototypes/` 等历史一手材料, 不动历史 `prototype/<slug>` 分支 (NG-002, BR-006).
- 正文不出现 PoC 字样, 不写任何 PoC 证据引用或未证实标注 (AC-018).
- 不碰 `workflow/navigate/SKILL.md` (ISSUE-03) 与 `roadmap.py` / `web/index.html` / `render_checks.py` (ISSUE-01/04).
## 代码定位提示
- 入口: `workflow/prototype/SKILL.md` (frontmatter 1-4 行, 适用范围句 7 行, 规则 1 在 26 行, 规则 5 在 30-33 行, 规则 6 在 34 行).
- `workflow/prototype/LOGIC.md`: 第 7 行路径, 第 62 行清理句.
- `workflow/prototype/UI.md`: 子形态节 6-31 行, 第 58 行路由, 第 82-85 行捕获与清理.
- `README.md:54`.
- 阅读顺序: SKILL.md 全文 → LOGIC.md 第 5 步 → UI.md 子形态节与第 6 步. 改前先留结构基线 (见验证入口第 1 步).
## 验证契约
- 变更类型: 结构变更 + 行为变更.
- 对应范围: 结构变更覆盖目录名, skill 名, 三子形态的路径/前缀/路由/分支词面; 须保持的公开接口是"由 navigate 的 demo 条目点名调用, `disable-model-invocation: true` 不变"和"三子形态判定顺序, `?variant=` 机制, 冲突加时间戳规则不变". 行为变更覆盖 SKILL.md 适用范围句与通用规则 1/5/6 的语义, 以及三处清理约定.
- 验证要求/证据: 结构变更须有改前基线 (文件清单与 `prototype` 命中快照) 与改后相同命令的对比, 只允许预期变化; 行为变更须逐条对照 AC-010/018/019 的可观察断言, 并给出 check_skill.py 的 OK; 清理约定须有三处改后原文摘录; 另给"全文无 PoC"与"frontmatter 保留调用开关"的 grep 证据.
## 验证入口
```bash
# 1 改前基线 (在动文件之前留档)
mkdir -p /tmp/m9-04-02/before
find workflow/prototype -type f | sort > /tmp/m9-04-02/before/files.txt
grep -rn 'prototype' workflow/prototype README.md > /tmp/m9-04-02/before/prototype-hits.txt

# 2 AC-001 目录与命名
git mv workflow/prototype workflow/demo
ls workflow/demo            # 通过标准: 只有 SKILL.md LOGIC.md UI.md
test ! -e workflow/prototype && echo "old dir gone"
sed -n '1,4p' workflow/demo/SKILL.md
#    通过标准: name: demo; description 写演示用途; disable-model-invocation: true 仍在

# 3 AC-018 适用范围且全文无 PoC
grep -ni 'poc' workflow/demo/ ; echo "expect no hit above"
grep -n '成品\|线上系统' workflow/demo/SKILL.md
#    通过标准: grep -ni poc 零命中; 适用范围句写明成品演示不调用本 skill, 直接跑成品

# 4 AC-019 规则 1/5/6
grep -n '注定被丢弃\|验证止于冒烟' workflow/demo/SKILL.md   # 通过标准: 零命中
grep -n '不进入产品\|不进产品\|保留回看\|验证止于能演示\|演示了什么' workflow/demo/SKILL.md
#    通过标准: 规则 1 有"不进产品/不承诺交付/可保留回看"; 规则 5 有四项捕获; 规则 6 是"验证止于能演示"

# 5 AC-010 三处清理约定 + BR-006
grep -rn '合并主干前由人类清理\|用完即删\|用完即焚' workflow/demo/   # 通过标准: 零命中
grep -rn '点名' workflow/demo/    # 通过标准: SKILL.md, LOGIC.md, UI.md 各有可回看且不主动删除, 清理由仓库主人点名的说法

# 6 AC-004 落位与子形态
grep -n 'demo\.\|/demo/<name>\|demos/<demo-name>\|demo/<feature-slug>\|demo/' workflow/demo/LOGIC.md workflow/demo/UI.md
#    通过标准: A 用 demo. 前缀放在 src/ 宿主页面附近; B 用 /demo/<name> 与 demo/ 子目录;
#    C 产物放 docs/changes/<feature-slug>/demos/<demo-name>/; A 与 B 变体集进 demo/<feature-slug>;
#    判定顺序仍是 A 优先, 仅当没有邻近宿主页面才 B, 没有前端项目降级 C

# 7 AC-016 (README) 与文档机检
grep -n 'demo' README.md          # 通过标准: 行内链接 workflow/demo/SKILL.md, 用途写演示
uv run python general/writing-for-llm/check_skill.py workflow/demo/SKILL.md   # 通过标准: OK, 退出 0

# 8 结构对比与残留
find workflow/demo -type f | sort
grep -rn 'prototype' workflow/demo README.md    # 通过标准: 零命中
git status --short                               # 通过标准: 只有重命名与预期内文本改动, 无 docs/changes 删除
```
## 交付证据
执行后填写: 改前基线与改后对比 (文件清单, prototype 命中), 三处清理约定改后原文摘录, check_skill 输出, 全文无 PoC 的 grep 结果, 材料位置 `/tmp/m9-04-02/`.
## 风险提示
- 目录改名同一次提交内要连带 README 链接, 否则活跃文档指向不存在的路径.
- UI.md 的"自动移除"是 git 行为陈述, 改时别顺手把它写成清理义务, 也别删掉这条事实.
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 验收标准
- [ ] `workflow/demo/` 只有 SKILL.md, LOGIC.md, UI.md, `name: demo`, description 是演示用途, 仓库里没有 `workflow/prototype/`.
- [ ] 适用范围句写明成品演示不调用本 skill, 全文无 PoC 字样.
- [ ] 规则 1/5/6 按演示语义写, 无"注定被丢弃"与"验证止于冒烟".
- [ ] 三子形态只换词, 判定顺序与 `?variant=` 机制不变; 路径/前缀/路由/分支均为 demo 词面.
- [ ] 三处清理约定都是可留回看加点名删除; LOGIC.md 第 5 步原句已换.
- [ ] README 行指向 `workflow/demo/SKILL.md` 且用途写演示; check_skill OK.
## 被阻塞于
- 无
