## 父级
- `../EXECUTION.md`
## 执行
- [x] 已完成
## 来由
双轴评审 (REVIEW-01-standards.md / REVIEW-02-spec.md) 与影响复查 (IMPACT-REVIEW.md) 的采纳项返工. 只处理本轮总指挥采纳的条目; 未采纳条目的理由见 `../ROADMAP` 之外的本目录关闭摘要, 不在本 issue 改动.

## 要交付什么
1. `workflow/navigate/TEMPLATES.md:88` 把旧类型中文语汇 `原型` 改成 `演示材料` (TECHNICAL.md 模块划分点名 TEMPLATES "只改枚出行与原型一词" 的第二处, 首轮漏改). 只改这一个词, 不动该行其余措辞.
2. `workflow/navigate/SKILL.md` 的 poc 条目指针句去掉变更内规则号 `(BR-005)`, 保留指向 `workflow/software-engineering-consensus/SKILL.md` 的完整指针, 不新增也不删该句其余内容 (该规则号随变更归档后不可解析, 与同句另一个完整路径指针参照系不一).
3. `README.md` 工作流技能表把 demo 一行按字母序移到 deliberate 之后, 其余行不动 (表中其余 36 行严格字母序, 改名后原位保留会破序). 行内容不变, 仍指向 `workflow/demo/SKILL.md`.
4. `workflow/navigate/tests/visual/README.md` 覆盖表补一行本轮新增的 `demo/poc 类型展示` (TC-006), 并把 `7 个里程碑` 描述改为与实际夹具一致的 8 个; 表里基线就缺的两行 (验收类型展示 / 无 JS 报错) 不在本 issue 补.
5. `workflow/navigate/tests/test_roadmap_validation.py` 模块 docstring 补本轮三条用例 (TC-002 demo 可写入 / TC-003 prototype 被拒 / TC-005 poc 可写入, 带 m04 前缀消歧), 不动既有用例与编号.
6. 证据补录 (只追加, 不改旧内容): 在 `issues/ISSUE-03-navigate-type-vocabulary.md` 的 交付证据 节补一条 `无冒烟` 反向 grep 的实际输出; 在 `issues/ISSUE-04-web-demo-poc-visuals.md` 的 交付证据 节补 pytest 汇总行的实际复跑输出与命令.

## 允许范围
- `workflow/navigate/TEMPLATES.md` (只第 88 行那个词)
- `workflow/navigate/SKILL.md` (只 poc 指针句的规则号)
- `README.md` (只移动 demo 行)
- `workflow/navigate/tests/visual/README.md` (只覆盖表两处)
- `workflow/navigate/tests/test_roadmap_validation.py` (只模块 docstring)
- `docs/changes/workflow-stack-review/milestone-04/issues/ISSUE-03-*.md` 与 `ISSUE-04-*.md` 的 交付证据 节 (只追加)
- 本 issue 文件

## 禁止范围
- 不改 PRODUCT.md / TECHNICAL.md / DECISIONS.md / EXECUTION.md.
- 不改 roadmap.py / web/index.html / render_checks.py / web_server.py / workflow/demo/ 三文件 (本轮已验收内容).
- 不动 docs/changes 下历史一手材料, 不跑 sync-to-pi.py, 不改 ~/.agents 下真实安装的 skills.
- 不改任何既有 AC 断言涉及的措辞 (例如图例 `实验 PoC` 是 milestone-03 D012 定的, 不动).

## 验证入口
```bash
grep -rn '原型' workflow/ README.md --include=*.md   # 通过标准: 零命中
grep -n 'BR-005' workflow/navigate/SKILL.md          # 通过标准: 零命中 (指针句其余措辞仍在)
grep -n 'demo\|deliberate' README.md | head          # 通过标准: demo 行位于 deliberate 之后
sed -n '20,40p' workflow/navigate/tests/visual/README.md   # 通过标准: 覆盖表含 demo/poc 类型展示, 8 个里程碑
sed -n '1,12p' workflow/navigate/tests/test_roadmap_validation.py  # 通过标准: docstring 含 m04 三条用例
grep -n '无冒烟' docs/changes/workflow-stack-review/milestone-04/issues/ISSUE-03-navigate-type-vocabulary.md
uv run python general/writing-for-llm/check_skill.py workflow/navigate/SKILL.md   # OK 且退出 0
uv run python workflow/navigate/scripts/web_server.py status     # 若非 alive:false 先 stop
uv run python -m pytest workflow/navigate/tests                  # 退出 0, 无 failed
uv run --project general/access-web/browse python workflow/navigate/tests/visual/render_checks.py  # 0 项失败
```

## 交付证据
执行人 ex07, 分支 issue/07, 基点 a6670e3. 原始输出在 `/tmp/m9-04-07/` (greps.log, check_skill.log, pytest.log, render_checks.log, webserver-stop-status.log).

- 1 `grep -rn '原型' workflow/ README.md --include=*.md`: 零命中 (exit 1).
- 2 `grep -n 'BR-005' workflow/navigate/SKILL.md`: 零命中 (exit 1); 指针句其余措辞仍在, 仍指向 `workflow/software-engineering-consensus/SKILL.md` 的 PoC 词条.
- 3 `grep -n 'demo\|deliberate' README.md`: demo 行在 44 行, deliberate 在 43 行, demo 行位于其后且行内容未改.
- 4 `sed -n '20,40p' workflow/navigate/tests/visual/README.md`: 覆盖表含 `demo/poc 类型展示 (TC-006)` 行, 帧率行已改为 `8 个里程碑` (与 render_checks.py 夹具 `"8 个里程碑, ...含 demo 与 poc 各一枚"` 一致).
- 5 `sed -n '1,12p' workflow/navigate/tests/test_roadmap_validation.py`: 模块 docstring 含 m04 三条用例 (TC-002 demo 可写入 / TC-003 prototype 被拒且文件逐字节不变 / TC-005 poc 可写入), 既有用例与编号未动.
- 6 证据补录: ISSUE-03 交付证据节追加 `无冒烟` 反向 grep 输出 (`grep -n '冒烟' workflow/navigate/SKILL.md` 零命中, exit 1); ISSUE-04 交付证据节追加 pytest 汇总行复跑输出与命令. 均只追加, 未改旧内容.
- check_skill: `uv run python general/writing-for-llm/check_skill.py workflow/navigate/SKILL.md` → `workflow/navigate/SKILL.md: OK`, 退出码 0.
- 前置: `web_server.py stop` + `status` 得 `alive:false`.
- pytest: `uv run python -m pytest workflow/navigate/tests` → `30 passed in 8.05s`, 退出码 0, 无 failed.
- render_checks: `uv run --project general/access-web/browse python workflow/navigate/tests/visual/render_checks.py` → `10 项检查, 10 项通过, 0 项失败`, 退出码 0, 含 TC-006 `PASS demo/poc 类型展示`.
## 停止条件
需要改 Spec/决策, 或需要动的文件超出允许范围时停止并报告.
## 验收标准
- [x] `原型` 在 workflow/ 与 README.md 零命中; `BR-005` 不在 navigate/SKILL.md.
- [x] README demo 行按字母序; tests/visual/README.md 覆盖表与夹具一致.
- [x] 测试文件 docstring 含 m04 三条用例; ISSUE-03/04 证据补录到位.
- [x] check_skill OK, pytest 全绿, render_checks 0 项失败.
