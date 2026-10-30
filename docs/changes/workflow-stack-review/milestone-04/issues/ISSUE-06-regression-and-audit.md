## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已完成
## 要核验什么
五个实施 issue 拼起来后, 本变更对外的承诺是否成立, 且没有越界:
- 全套回归与文档机检: AC-015, AC-017, TECHNICAL 非功能要求的回归检查与文档机检.
- 三条审计: BR-003 (活跃内容不残留 prototype 类型名, 路径约定, 分支约定), BR-004 (没改已安装 skills 与全局配置, 没运行同步, 没宣称安装效果), BR-006 (演示材料与变体分支没被主动清理).
- 抽查两条容易被后续改动破坏的既有不变量: `roadmap.py` 的命令集与写入路径语义未变, 展示页未知类型仍回退 task, 以及 BR-001 的枚举字面量.
- 逐个复核 AC-001 到 AC-014 与 AC-016 的可观察结论, 只记录事实与差距, 不修代码.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-015, AC-017, BR-003, BR-004, BR-006; 复核 AC-001 到 AC-014 与 AC-016.
- Technical: `../TECHNICAL.md`, 非功能要求 (回归检查, 文档机检, 不宣称安装效果), 模块接口 (roadmap.py 命令行不变量, 展示页未知类型回退).
## 相关决策
- `../../milestone-03/DECISIONS.md`: D001 (不留别名, 历史文件原样), D013 (ADR 边界), D019 (不主动清理演示材料与分支).
- `../../milestone-01/DECISIONS.md`: D006 (演示活动不新增产品交付承诺, 不改已安装 skills 的定位).
## 代码定位提示
- 回归入口: `workflow/navigate/tests/`, `workflow/navigate/tests/visual/render_checks.py`.
- 审计对象: `workflow/` (skill 正文, 模板, 脚本, 网页, 测试), `README.md`, `general/`, `docs/changes/`, `docs/adr/0024-*`, `~/.agents/skills/` (只读核对).
- 复核入口: `workflow/navigate/scripts/roadmap.py`, `workflow/navigate/web/index.html`, `workflow/navigate/TEMPLATES.md`, `workflow/demo/`, `workflow/navigate/SKILL.md`.
## 验证入口
```bash
# 0 前置: 展示服务占着默认端口会让三个 lifecycle 用例假红
uv run python workflow/navigate/scripts/web_server.py stop
uv run python workflow/navigate/scripts/web_server.py status        # 期望 alive:false

# 1 AC-015 与 TECHNICAL 回归检查
uv run python -m pytest workflow/navigate/tests
#    通过标准: 退出码 0, 末行显示全部通过, 无 failed

# 2 视觉巡检回归 (环境缺口时降级并写明)
uv run --project general/access-web/browse python workflow/navigate/tests/visual/render_checks.py
#    通过标准: 退出 0, 0 项失败
#    若 playwright/chromium 缺失: 改为人工起页面加截图, 证据里写明缺口, 不写成已跑

# 3 AC-017 与文档机检
uv run python general/writing-for-llm/check_skill.py workflow/demo/SKILL.md
uv run python general/writing-for-llm/check_skill.py workflow/navigate/SKILL.md
#    通过标准: 两次都输出 OK 且退出 0

# 4 BR-003 审计 (活跃内容)
grep -rn 'prototype' workflow/ README.md general/ --include=*.md --include=*.py --include=*.html
#    通过标准: 零命中
grep -rln 'prototype' docs/
#    通过标准: 命中项逐条分类为允许例外后写入证据: docs/changes/ 下的历史一手材料与决策记录,
#    以及 docs/adr/0024-demo-poc-milestone-types.md (记录旧名由来); 活跃内容里不得出现

# 5 BR-004 审计
git status --short
git diff --stat
#    通过标准: 改动文件全部落在 EXECUTION.md 的全局允许范围内; 未改 PRODUCT/TECHNICAL/DECISIONS,
#    未改 docs/changes 历史材料, 未改已安装 skills
ls ~/.agents/skills | grep -x -E 'demo|prototype'
#    通过标准: 只列 prototype (证明没安装/没同步), 没有 demo
#    另核对: 本次会话没有任何 sync-to-pi.py 调用记录; 完成证据不含安装效果或模型行为结论

# 6 BR-006 审计
git diff --stat docs/changes
git status --short docs/changes
ls docs/changes/less-is-more-palette/prototypes/
git branch --list 'prototype/*'
#    通过标准: docs/changes 无删除项, 历史 prototypes 目录内容仍在, 旧分支列表与改动前一致

# 7 BR-001 与两条不变量抽查
grep -n 'TYPE_VALUES' workflow/navigate/scripts/roadmap.py
mkdir -p /tmp/m9-04-06
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-06/r.json milestones.milestone-01 '{"title":"夹具","type":"task","question":"q"}'
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-06/r.json milestones.milestone-01.type prototype
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-06/r.json milestones.milestone-01.type poc
uv run python workflow/navigate/scripts/roadmap.py query docs/changes/workflow-stack-review/roadmap/ROADMAP.json milestones.milestone-04.type
#    通过标准: 常量为六值; prototype 退出 1 且报完整合法值; poc 退出 0; 现网 ROADMAP.json 仍可读
grep -c 'TYPE_META.task' workflow/navigate/web/index.html    # 通过标准: 回退点仍在 (2 处)

# 8 逐条复核 AC-001 到 AC-014 与 AC-016
#    对每条 AC 的断言读文件或跑命令, 记录结论与差距; 参考 EXECUTION.md 覆盖矩阵里的验证入口
```
## 完成证据
执行后填写: 每条命令的实际输出摘要 (pytest 汇总行, render_checks 报告, check_skill 两行 OK, 四条审计的命中清单与分类判定, 两条不变量结论), 逐条 AC 复核表, 原始输出与截图路径 `/tmp/m9-04-06/`; 若有未通过项, 写明差距与是否阻塞验收.
## 风险提示
- 展示服务占用默认端口造成 lifecycle 用例假红, 必须先 stop 并 status 确认.
- 审计 grep 会命中历史材料与 ADR, 一律判失败就误报; 要按 BR-003 的范围与例外逐条分类.
- `~/.agents/skills` 是宿主只读挂载, 只做只读核对, 不改不装.
## 停止条件
需要改变任一 Spec, 决策或核验范围时停止; 发现需要修代码才能通过时不在本 issue 修, 报告并交回对应实施 issue.
## 适合 AFK 的原因
全部动作是跑命令与读文件, 判据已由 AC 与审计口径定死, 不需要新的产品/API/架构决策; 唯一判断是审计命中的分类, 分类规则本身写在 BR-003 里.
## 验收标准
- [ ] pytest 全绿, render_checks 0 项失败 (或按环境缺口降级并写明).
- [ ] 两份改过的 SKILL.md 通过 check_skill.py.
- [ ] BR-003 活跃内容零 `prototype` 残留, 例外逐条分类留证.
- [ ] BR-004 改动不越界, 已安装 skills 与全局配置未动, 无同步调用, 无安装效果结论.
- [ ] BR-006 历史演示材料与旧分支未被动过.
- [ ] AC-001 到 AC-014 与 AC-016 逐条有结论, 未通过与差距都写明.
## 被阻塞于
- `ISSUE-01-milestone-type-enum.md`
- `ISSUE-02-demo-skill-rename-rewrite.md`
- `ISSUE-03-navigate-type-vocabulary.md`
- `ISSUE-04-web-demo-poc-visuals.md`
- `ISSUE-05-adr-naming-record.md`
