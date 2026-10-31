## 父级
- `../EXECUTION.md`
## 执行
- [x] 已完成
## 来由
独立核验 (VERIFY-02) 判 AC-010 失败: PRODUCT.md 的 AC-010 要求 `workflow/demo/SKILL.md` / `UI.md` / `LOGIC.md` 三处都写明"演示材料与变体分支可以留着回看, 代理不主动删除", 且"要清理时由仓库主人点名删除对象"; 实际三处只写了演示材料, 变体分支 (子形态 A/B 进 `demo/<feature-slug>` 分支) 的保留与点名清理没有同样写明, 且 `UI.md` 把点名清理只写在子形态 C 一条上. 这是实现缺失, 不是文档风格问题.

## 要交付什么
在三个文件里把"变体分支"与"演示材料"并列写清保留与清理约定, 不动其它内容与既有措辞的责任边界:
1. `workflow/demo/SKILL.md` 通用规则 1 (第 28 行): 把"代理不主动删除演示材料; 需要清理时由仓库主人点名删除对象"扩成同时覆盖变体分支 (例如: 演示材料与变体分支都可留着回看, 代理不主动删除; 需要清理时由仓库主人点名删除对象). 规则其余句子不动.
2. `workflow/demo/LOGIC.md` 第 5 步 (第 60-62 行): 在既有的"演示材料可保留回看, 代理不主动删除; 需要清理时由仓库主人点名删除对象"之外, 补明变体分支同样可留回看与本条清理口径. 第 60/61 行关于逻辑模块与页面外壳保留的句子不动.
3. `workflow/demo/UI.md` 第 6 步 (第 78-85 行): 让 A/B 与 C 两处都写明"可保留回看, 代理不主动删除, 需要清理由仓库主人点名删除对象"; 去掉会让读者以为变体分支是待废弃物的说法 (例如 "一次性分支"), 分支名 `demo/<feature-slug>` 与"胜出变体融入真实代码"的规则保留.
4. 三处都不许出现"合并主干前清理""用完即删""用完即焚"之类义务句.

## 允许范围
- `workflow/demo/SKILL.md`, `workflow/demo/LOGIC.md`, `workflow/demo/UI.md` 的上述位置.
- 本 issue 文件.

## 禁止范围
- 不改 navigate / roadmap.py / web/index.html / render_checks.py 等其它文件, 不改 PRODUCT.md / TECHNICAL.md / DECISIONS.md / EXECUTION.md.
- 不新增交付承诺, 不改三子形态 A/B/C 的判定顺序与落位规则, 不动 `demo/` 前缀, `/demo/<name>` 路由与 `demos/` 目录约定.
- 不跑 sync-to-pi.py, 不改 ~/.agents 下真实安装的 skills.

## 验证入口
```bash
grep -n '变体分支\|演示材料' workflow/demo/SKILL.md workflow/demo/LOGIC.md workflow/demo/UI.md
#    通过标准: 三处都能读到 演示材料与变体分支 可留回看 / 代理不主动删除 / 主人点名删除
grep -n '合并主干前\|用完即删\|用完即焚' workflow/demo/       # 零命中
grep -n '一次性分支' workflow/demo/UI.md                       # 零命中
grep -n 'demo/<feature-slug>\|/demo/\|demos/' workflow/demo/UI.md | head   # 约定仍在
uv run python general/writing-for-llm/check_skill.py workflow/demo/SKILL.md   # OK 且退出 0
uv run python -m pytest workflow/navigate/tests                # 退出 0, 无 failed (展示服务占端口就先 stop 并 status 确认 alive:false)
```

## 交付证据
执行后填写: 三处改后原文摘录, 各条 grep 结果, check_skill 退出码, pytest 汇总行, 原始输出放 `/tmp/m9-04-08/`.

改动文件: `workflow/demo/SKILL.md` (通用规则 1), `workflow/demo/LOGIC.md` (第 5 步), `workflow/demo/UI.md` (第 6 步).

三处改后摘录:
- SKILL.md 规则 1: "演示材料与变体分支都可留着回看, 代理不主动删除; 需要清理时由仓库主人点名删除对象."
- LOGIC.md 第 5 步: "演示材料与变体分支 (如产生) 都可保留回看, 代理不主动删除; 需要清理时由仓库主人点名删除对象."
- UI.md 第 6 步 A/B: "完整变体集作为一手材料进入变体分支 `demo/<feature-slug>` ... 变体分支可留着回看, 代理不主动删除; 需要清理时由仓库主人点名删除对象." (C 一条原有口径未动; "一次性分支"已改"变体分支")

验证结果 (原始输出在 /tmp/m9-04-08/):
- `grep -n '变体分支\|演示材料'` 三文件: 三处均读到 可留回看/不主动删除/点名删除 (grep-1-retention.txt, exit 0)
- `grep -rn '合并主干前\|用完即删\|用完即焚' workflow/demo/`: 零命中 (exit 1)
- `grep -n '一次性分支' workflow/demo/UI.md`: 零命中 (exit 1)
- `grep -n 'demo/<feature-slug>\|/demo/\|demos/' workflow/demo/UI.md`: 约定仍在 (exit 0)
- check_skill: `workflow/demo/SKILL.md: OK`, 退出 0 (展示服务已先 stop, status alive:false)
- pytest: `30 passed in 8.08s`, 退出 0; 收工时 status alive:false
## 停止条件
需要改 Spec/决策; 需要动允许范围之外的文件. 停下报告.
## 验收标准
- [ ] 三处都写明演示材料与变体分支可留回看, 代理不主动删除, 主人点名才清理.
- [ ] 无"一次性分支"/"合并主干前清理"类义务句; 三子形态与路径约定未改.
- [ ] check_skill OK, pytest 全绿.
