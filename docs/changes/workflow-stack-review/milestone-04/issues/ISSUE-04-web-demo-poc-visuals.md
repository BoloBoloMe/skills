## 父级
- `../EXECUTION.md`
## 执行
- [x] 已完成
## 要交付什么
地图页把 `demo` 与 `poc` 画成两种各自可辨的星球: 图例各有条目 (演示 demo / 实验 PoC), 类型元数据六键齐全, demo 沿用原卫星外观只换类型键, poc 用新的配色与地貌, 星球外观分派与配色表同步. 渲染巡检脚本的类型清单与夹具跟上, 并新增一条 demo/poc 展示用例.

具体:
1. `workflow/navigate/web/index.html`:
   - `TYPE_META`: `prototype` 键换成 `demo` (label `演示`, 沿用原配色 `#e8955c`), 新增 `poc` (label `实验`, 新配色, 与 demo 明显不同); 六键顺序为 research, deliberate, demo, poc, task, acceptance.
   - 图例: 原"原型 prototype"项换成"演示 demo"(图标沿用卫星), 在其后新增"实验 PoC"项, 图标与配色与 demo 不同; 图例顺序与 `TYPE_META` 一致.
   - `PLANET_PALETTES` 与 `PLANET_FEATURES`: `prototype` 键换成 `demo` (沿用原熔岩岩石配色与 cracks 地貌), 新增 `poc` 键 (新配色与新地貌组合, 不与 demo 或其它类型相同).
   - 星球外观分派 (约 1639 行): `node.m.type === 'prototype'` 改 `'demo'` (保留卫星外观); 新增 `poc` 分支, 用与卫星不同的一套外观 (例如双层轨道环或脉冲光晕), 让人一眼分得开.
   - 保留未知类型回退 (`TYPE_META[node.m.type] || TYPE_META.task`, 约 1544 与 1903 行两处) 不变; 不加新状态, 不动画布其它逻辑.
2. `workflow/navigate/tests/visual/render_checks.py`:
   - `TYPES` 清单改为 `["research", "deliberate", "demo", "poc", "task", "acceptance"]` 之类与页面一致的集合.
   - `small_roadmap` 夹具里 `prototype` 换成 `demo`, 并新增一枚 `poc` 里程碑接入现有连线结构; 保持原 (707,447) 处仍是可点开的未关闭星球, 布局位移就同步调整点击坐标, 不放宽既有断言.
   - 新增 TC-006 一项巡检: 图例文本同时含 `演示 demo` 与 `实验 PoC`; 画布标注 (`fillText`) 同时出现两类; 页面内 `TYPE_META.demo.color` 与 `TYPE_META.poc.color` 不同, `PLANET_PALETTES.demo` 与 `PLANET_PALETTES.poc` 不同, `PLANET_FEATURES.demo.base` 与 `PLANET_FEATURES.poc.base` 不同; 该项与既有各项共用同一次页面加载, 不重复起服务.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-006, BR-002.
- Technical: `../TECHNICAL.md`, 模块划分 (web/index.html 条目), 模块接口 (展示页按 type 取元数据, 六值覆盖, 未知回退), 接缝与依赖 (TYPE_META 与渲染分派属模块内部接缝).
## 相关决策
- `../../milestone-03/DECISIONS.md`: D001 (网页类型标签改演示, 视觉分支与配色同步), D012 (demo 与 poc 各用独立外观, poc 标签英文 PoC 中文 实验, 有区分度要求).
## 允许范围
- `workflow/navigate/web/index.html`: 类型元数据, 图例, 星球外观分派, 配色与地貌表.
- `workflow/navigate/tests/visual/render_checks.py`: 类型清单, 夹具, 新增巡检项.
## 禁止范围
- 不改 `roadmap.py`, `web_server.py`, `navigate/SKILL.md`, `workflow/demo/` (其它 issue 的活).
- 不引入外部资源或 CDN, 不加构建步骤 (既有审计测试会扫 `index.html` 的外部引用).
- 不改已关闭状态的渲染 (D014: 终止与成功关闭的区别只在关闭摘要文本).
- 不放宽既有巡检阈值与断言来让新用例通过.
## 代码定位提示
- 入口: `workflow/navigate/web/index.html` 的图例块 (约 177-220 行), `TYPE_META` (257-263 行), `PLANET_PALETTES` (1196-1208 行), `PLANET_FEATURES` (1211-1220 行), 星球外观分派 (1610-1650 行), 元数据回退点 (1544, 1903 行).
- 巡检脚本: `workflow/navigate/tests/visual/render_checks.py` 的 `TYPES` (30 行), `small_roadmap` (57-68 行), `run()` 里既有的 "验收类型展示" 用例可照抄写法.
- 阅读顺序: 先看 TYPE_META 与图例, 再看分派与配色表, 最后看 render_checks 的既有用例与坐标.
## 验证契约
- 变更类型: 行为变更.
- 对应范围: 展示页在 `?roadmap=` 下呈现的类型元数据, 图例与星球外观 (外部可观察), 以及巡检脚本的类型覆盖.
- 验证要求/证据: 自动化侧给 render_checks 退出码与失败项数为 0 的报告, 并给 TC-006 那一行输出; 人工侧给一张截图 (含图例与两种星球) 与逐项核对结论, 覆盖"图例两项文本正确"和"两类型一眼可分"; 另给 `TYPE_META` 六键与回退点未变的代码摘录; 给未知类型回退的人工观察结果.
## 验证入口
```bash
# 0 前置: 无展示服务占用默认端口
uv run python workflow/navigate/scripts/web_server.py stop
uv run python workflow/navigate/scripts/web_server.py status     # 期望 alive:false

# 1 造含 demo 与 poc 的夹具 (依 ISSUE-01 的枚举)
mkdir -p /tmp/m9-04-04
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-04/fixture.json milestones.milestone-01 '{"title":"演示","type":"demo","question":"q"}'
uv run python workflow/navigate/scripts/roadmap.py save /tmp/m9-04-04/fixture.json milestones.milestone-02 '{"title":"实验","type":"poc","question":"q"}'
#    未知类型回退另用一份手工副本: cp fixture.json unknown.json 后把某个 type 改成不存在的值

# 2 AC-006 / BR-002 自动化侧 + 回归
uv run --project general/access-web/browse python workflow/navigate/tests/visual/render_checks.py
#    通过标准: 退出 0, 报告 0 项失败; 其中 TC-006 行显示图例与画布均识别演示 demo 与实验 PoC
#    环境缺口时: 改做第 4 步人工核对, 并在证据里写明 playwright/chromium 缺失

# 3 AC-006 人工侧 (页面与截图)
uv run python workflow/navigate/scripts/web_server.py start
#    打开给出的 URL 后拼 ?roadmap=/tmp/m9-04-04/fixture.json
#    通过标准: 图例里有 "演示 demo" 与 "实验 PoC" 两项; 画布上 demo 是带卫星的星球,
#    poc 是另一套配色与地貌, 两者一眼能分开; 截图存 /tmp/m9-04-04/
uv run python workflow/navigate/scripts/web_server.py stop

# 4 未知类型回退 (模块接口不变量)
#    用 unknown.json 起页面, 观察那个未知类型星球按 task 元数据渲染
#    通过标准: 页面无 JS 报错, 该星球外观与标签走 task 分支, 回退表达式仍在代码里

# 5 元数据与残留
grep -n "demo\|poc" workflow/navigate/web/index.html | head -20   # 通过标准: TYPE_META/图例/配色/分派均有 demo 与 poc
grep -rn "prototype" workflow/navigate/web/index.html workflow/navigate/tests/visual/   # 通过标准: 零命中
grep -c 'TYPE_META.task' workflow/navigate/web/index.html     # 通过标准: 回退点仍在 (期望 2 处)
uv run python -m pytest workflow/navigate/tests      # 通过标准: 退出 0, 含 stdlib 与外部引用审计用例仍绿
```
## 交付证据
执行人 ex04, 分支 issue/04, 基点 181b3cd. 原始输出与截图在 `/tmp/m9-04-04/` (render_checks.txt, fixture.png, unknown.png, pixcheck2-4 脚本与输出).

- 前置: `web_server.py stop` + `status` 得 `alive:false`; 夹具经 `roadmap.py` 造出 (demo/poc 各一枚, `query` 回读确认), 未知类型副本 unknown.json 把 type 改成已废弃的旧名 `prototype` (顶两个用途: 回退 + 旧名不再被识别).
- render_checks (AC-006 自动化侧): 退出码 0, `10 项检查, 10 项通过, 0 项失败`. TC-006 行原文:
  `PASS demo/poc 类型展示           图例两项(True/True), 画布标注(demo=True poc=True), 标签色(#e8955c/#63c9a3), 配色与地貌均不同`
- 截图: `/tmp/m9-04-04/fixture.png` (demo+poc 同屏), `/tmp/m9-04-04/unknown.png` (未知类型页, 面板展开). 环境无缺 (playwright 由 general/access-web/browse 提供, chromium 在 `~/.cache/ms-playwright`), 未启用降级条款.
- 人工核对结论 (本模型不支持直接看图, 以像素取样代替目视, 脚本与输出均在材料目录):
  1. 图例两项文本正确: legend 文本平化后含 `演示 demo` 与 `实验 PoC`, 顺序与 TYPE_META 六键一致 (调研, 权衡, 演示, 实验, 任务, 验收).
  2. 两类型一眼可分: demo 星球本体平均 RGB [90,70,68] (熔岩暖棕) 且外圈 26-40px 有 42 个灰色卫星像素/0 绿色像素; poc 本体 [109,140,128] (苔绿) 且外圈 22-38px 有 180 个绿色像素 (脉冲环)/2 灰色像素. 色相家族不同, 装饰形态不同.
  3. 未知类型回退: unknown.json (type=prototype) 页面无 JS 报错; 该星球本体 [156,129,104] 走 task 沙色外观; 点开面板显示 `类型 prototype` (原文回显); 副标注只显 `待处理` 不带类型后缀; 页面整体正常渲染.
- grep: index.html 中 demo/poc 覆盖图例/TYPE_META/配色/地貌/分派五处 (见验证入口第 5 步输出); `grep -rn prototype workflow/navigate/web/index.html workflow/navigate/tests/visual/` 在 index.html 零命中, render_checks.py 有 3 处命中但全是 JS 内建属性 `CanvasRenderingContext2D.prototype` (基点 181b3cd 就有, 非类型名残留, 属 BR-003 允许例外); `grep -c 'TYPE_META.task'` = 1.
- pytest: `30 passed in 8.00s`, 退出码 0, 无 failed (基线 27 + ISSUE-01 新增 3).
- 规格偏差 2 条 (不阻塞, 原文如实记录):
  1. issue 写回退点两处 (约 1544 与 1903 行) 且 grep 期望 2; 实际 `TYPE_META[node.m.type] || TYPE_META.task` 只在 1544 行一处, 1903 行是 `TYPE_META[n2.m.type]` 配 `meta ? ... : ''` (未知类型不显类型后缀, 语义等价的回退但不含 `TYPE_META.task` 字样). 按禁止范围未动画布逻辑, 保持原样.
  2. 验证入口的 prototype grep 通过标准写零命中, 但 render_checks.py 既有代码的 `CanvasRenderingContext2D.prototype` (JS 语言内建) 无法避开且不在本 issue 允许改动语义内; 已按上述判定为例外, 交 ISSUE-06 审计复核.
- 补录 (ISSUE-07): pytest 汇总行复跑 `uv run python -m pytest workflow/navigate/tests` → `30 passed in 8.05s`, 退出码 0, 无 failed (原始输出 `/tmp/m9-04-07/pytest.log`).
## 风险提示
- 夹具改动会挪动布局, 既有 (707,447) 点击坐标与新里程碑的遮挡最容易踩; 发现点不中要调夹具或坐标, 不要调松断言.
- 图例顺序与 `TYPE_META` 顺序必须一致, 否则容易被后续维护改乱.
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 验收标准
- [x] 图例有"演示 demo"与"实验 PoC"两项, 且顺序与 `TYPE_META` 六键一致.
- [x] demo 星球是带卫星环绕的外观, poc 用另一套配色与地貌, 人类看一眼能分开.
- [x] `TYPE_META`, 配色表, 地貌表, 外观分派均覆盖 demo 与 poc; 未知类型回退 task 保留.
- [x] render_checks 类型清单与夹具已更新, TC-006 在且绿, 既有巡检项与 pytest 仍全绿.
## 被阻塞于
- `ISSUE-01-milestone-type-enum.md` (验证入口第 1 步用 `roadmap.py` 造 demo/poc 夹具, 枚举不接受时造不出)
