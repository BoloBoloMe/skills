## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已完成
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
执行后填写: render_checks 完整输出 (含 TC-006 行), 截图路径与人工核对结论, 未知类型回退观察结果, pytest 汇总行, 材料位置 `/tmp/m9-04-04/`.
## 风险提示
- 夹具改动会挪动布局, 既有 (707,447) 点击坐标与新里程碑的遮挡最容易踩; 发现点不中要调夹具或坐标, 不要调松断言.
- 图例顺序与 `TYPE_META` 顺序必须一致, 否则容易被后续维护改乱.
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 验收标准
- [ ] 图例有"演示 demo"与"实验 PoC"两项, 且顺序与 `TYPE_META` 六键一致.
- [ ] demo 星球是带卫星环绕的外观, poc 用另一套配色与地貌, 人类看一眼能分开.
- [ ] `TYPE_META`, 配色表, 地貌表, 外观分派均覆盖 demo 与 poc; 未知类型回退 task 保留.
- [ ] render_checks 类型清单与夹具已更新, TC-006 在且绿, 既有巡检项与 pytest 仍全绿.
## 被阻塞于
- `ISSUE-01-milestone-type-enum.md` (验证入口第 1 步用 `roadmap.py` 造 demo/poc 夹具, 枚举不接受时造不出)
