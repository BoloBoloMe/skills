## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已完成
## 要交付什么
`roadmap.py` 的里程碑类型枚举换成 `research` / `deliberate` / `demo` / `poc` / `task` / `acceptance`, 顺序即报错里合法值清单的顺序; `prototype` 从此被拒, 不留别名. 模板里的枚举行同步. 新增三条枚举用例守住这三件事.

具体:
1. `workflow/navigate/scripts/roadmap.py` 第 35 行 `TYPE_VALUES` 改为上述六值; 校验函数与错误文案模板一字不动 (文案由常量拼出, 改常量即改文案).
2. `workflow/navigate/TEMPLATES.md` 第 31 行 `type` 行的合法值与顺序同步为六值.
3. `workflow/navigate/tests/test_roadmap_validation.py` 新增三条用例, 复用文件里既有的 `run_cli` / `write_doc` / `legal_doc` 辅助:
   - TC-002 (对应 AC-002): 先造 `milestone-01.type` 为 task 的夹具, `save ... milestones.milestone-01.type demo` 退出 0, `query` 得 demo.
   - TC-003 (对应 AC-003): 夹具同上, `save ... type prototype` 退出 1, `error` 里合法值恰为六值且不含 prototype, 文件前后逐字节相同.
   - TC-005 (对应 AC-005): 同样夹具 `save ... type poc` 退出 0, `query` 得 poc.
   - docstring 写明 `TC-002 (m04 AC-002)` 形式: 同文件里既有的 TC-002/TC-003 注释属 navigate-roadmap-json 变更, 号码语义不同.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-002, AC-003, AC-005, AC-016 (TEMPLATES 枚举行部分), BR-001, NG-001.
- Technical: `../TECHNICAL.md`, 模块接口 (roadmap.py 命令行与合法值集合, 不变量), 非功能要求 (回归检查).
## 相关决策
- `../../milestone-03/DECISIONS.md`: D001 (demo 取代 prototype 且不留别名), D008 (poc 成为独立类型), D016 (保留独立类型与不新建 skill 的部分).
## 允许范围
- `workflow/navigate/scripts/roadmap.py`: 只 `TYPE_VALUES` 一行.
- `workflow/navigate/TEMPLATES.md`: 只 `type` 枚举行.
- `workflow/navigate/tests/test_roadmap_validation.py`: 只新增用例.
## 禁止范围
- 不动 `roadmap.py` 的命令集, 写入路径语义, 校验分支结构与错误文案模板.
- 不加 `prototype` 别名, 不做旧图读取兼容 (NG-001).
- 不碰 `web/index.html` 与 `tests/visual/render_checks.py` 的类型清单 (ISSUE-04 的活); 不碰导航正文与 demo skill (ISSUE-02/03 的活).
## 代码定位提示
- 入口: `workflow/navigate/scripts/roadmap.py:35` `TYPE_VALUES`; 引用它的校验在 `_fast_validate` (`:220` 附近) 与 `_validate_milestone` (`:270` 附近).
- 模板: `workflow/navigate/TEMPLATES.md:31` 的 `type` 行.
- 用例样板: `workflow/navigate/tests/test_roadmap_validation.py` 里既有的非法枚举用例与 `legal_doc()`.
- 阅读顺序: 先看 `TYPE_VALUES` 与两条校验点, 再跑一遍现状 CLI (见验证入口第一步) 确认改前行为, 再改常量, 补用例.
## 验证契约
- 变更类型: 行为变更.
- 对应范围: `roadmap.py` 接受与拒绝的 `type` 值集合 (CLI 外部可观察行为), 以及模板的合法值声明.
- 验证要求/证据: 逐条跑 AC-002/003/005 的真实 CLI 命令, 记录命令, 退出码, stdout JSON; 用 TC-002/003/005 在 pytest 内复跑; 用 `git diff workflow/navigate/scripts/roadmap.py` 证明只动一行常量; 用前后 `md5sum` 证明被拒写入不改文件; 对现网 `ROADMAP.json` 跑只读 query 并在 `/tmp` 副本上做 save 往返, 证明不含新类型的旧图照常读写.
## 验证入口
```bash
# 1 改前基线 (prototype 被接受, demo 被拒)
mkdir -p /tmp/m9-04-01
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-01/r.json milestones.milestone-01 '{"title":"夹具","type":"task","question":"q"}'
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-01/r.json milestones.milestone-01.type demo
#    期望改前: 退出 1, 合法值清单里是 prototype 且无 demo

# 2 AC-002 / AC-005
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-01/r.json milestones.milestone-01.type demo
uv run python workflow/navigate/scripts/roadmap.py query /tmp/m9-04-01/r.json milestones.milestone-01.type
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-01/r.json milestones.milestone-01.type poc
uv run python workflow/navigate/scripts/roadmap.py query /tmp/m9-04-01/r.json milestones.milestone-01.type
#    通过标准: save 退出 0 且 success=true; query 依次得 "demo" 与 "poc"

# 3 AC-003
md5sum /tmp/m9-04-01/r.json
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-01/r.json milestones.milestone-01.type prototype
md5sum /tmp/m9-04-01/r.json
#    通过标准: 退出 1, stdout 单行 JSON, error 含 "合法值: research, deliberate, demo, poc, task, acceptance" 且不含 prototype; 两次 md5 相同

# 4 旧图不变量 (只读 + /tmp 副本往返)
uv run python workflow/navigate/scripts/roadmap.py query docs/changes/workflow-stack-review/roadmap/ROADMAP.json milestones.milestone-04.type
cp docs/changes/workflow-stack-review/roadmap/ROADMAP.json /tmp/m9-04-01/copy.json
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-01/copy.json notes.0 '"y"'
#    通过标准: query 退出 0 得 "task"; save 退出 0 (现网文件未被改动)

# 5 回归 (先停守护服务)
uv run python workflow/navigate/scripts/web_server.py stop
uv run python workflow/navigate/scripts/web_server.py status
uv run python -m pytest workflow/navigate/tests
#    通过标准: status 报 alive:false; pytest 退出 0, 无 failed (拆分时基线 27 passed)
```
TECHNICAL 不变量 "不含 demo/poc 的既有 ROADMAP.json 照常读取与校验通过" 由第 4 步的 CLI 往返承担, 不另加 pytest 用例: 既有 schema 测试已覆盖校验机制, 再写只会重复枚举字面量.
## 交付证据
执行后填写: 每条命令的退出码与 stdout, `git diff workflow/navigate/scripts/roadmap.py`, 两次 md5, pytest 汇总行, 材料位置 `/tmp/m9-04-01/`.
## 验收标准
- [ ] `TYPE_VALUES` 恰为 research/deliberate/demo/poc/task/acceptance, 顺序与 BR-001 一致.
- [ ] demo 与 poc 可写入并读回; prototype 被拒且文件逐字节不变, 报错列完整合法值.
- [ ] `TEMPLATES.md` 枚举行同步.
- [ ] TC-002/TC-003/TC-005 在且绿; 既有用例与完整 pytest 套件仍全绿.
## 被阻塞于
- 无
