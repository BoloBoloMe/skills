# codebase-map 操作手册

代码库结构可视化 (CodeCharta) 的汉化构建与交付. 三子命令 (build/serve/stop) 的唯一操作入口是 `SKILL.md`; 本文是汉化构建链与布局铺设的手册, 记操作步骤与实测过的坑.

- 性质: 纯手动工具, 不被任何 skill 调用; 只在宿主使用.
- 分析端调度与常驻服务 (build/serve/stop) 的用法见 `SKILL.md`; 本文只覆盖汉化构建链与布局铺设.
- 版本钉死: 前端 `vis-2.9.1`, 分析端镜像 `docker.io/codecharta/codecharta-analysis:2.3.0` (版本核对以 manifest digest `sha256:6402a87f...` 为准, 不信 `ccsh --version`). 升级 = 人工改版本号重跑, 见第 6 节.

## 1 目录布局 (~/.agents/codebase-map/)

| 路径 | 内容 | 归属 |
| --- | --- | --- |
| `cache/src/` | 上游可视化克隆 + node_modules (整体替换, 不叠加) | build-zh.sh 维护 |
| `cache/run-latest/` | 最近一次构建的报告与截图 (stat-A.json, ts/lit-apply-report.json, smoke.json, shot-*.png) | build-zh.sh 维护 |
| `serve-root/` | 前端产物 (index.html 在顶层) + 数据副本 `<库名>-<8位路径哈希>.cc.json` | stage.py 铺设 |
| `state.json`, `logs/` | 服务端口/pid/启动时间/数据键清单, 服务日志 | 三子命令服务创建与维护 |

复原纪律: 删掉整个目录等于放弃实例; 复原 = 重跑 build-zh.sh (重建 cache) + stage.py (重建 serve-root), 无其他隐藏状态. cache 约 1GB (克隆 220M + node_modules 732M), 不入仓库.

## 2 前端汉化构建

```
bash <skill目录>/tools/build-zh.sh            # 默认 tag vis-2.9.1, 缓存 ~/.agents/codebase-map/cache
CC_SMOKE_PYTHON="uv run --with websockets python" bash tools/build-zh.sh   # 无 playwright 的环境用这个跑冒烟
bash tools/build-zh.sh --skip-smoke           # 调试用, 正常不要跳过冒烟
```

流程: 克隆钉死 tag (换 tag 整体替换缓存) -> npm ci -> `git checkout` 还原上游 -> 三通道词表替换 -> `npm run build` -> 渲染冒烟 (临时静态服务 + 无头浏览器截图 + 关键元素断言: 页签/底栏中文, 3D canvas 出建筑, 依赖视图出方块). 冒烟失败即构建失败. 幂等: 连跑两次产物逐字节一致 (实测 sha256 相同).

输出解读 (升级探针):
- `未使用词条` (`--check` 打印, stat-A.json 的 `dict_unused`): 上游改了或删了那句, 需人工处理;
- `未命中` (`untranslated`): 还没翻的文案, 就是进度条;
- 通道 B 的 `同一字面量命中 N 次, 请人工确认` 是已知复核项 (见第 8 节清单), 不算失败.

耗时实测 (容器, Node v24.21.0): 暖缓存端到端 23s (替换 0.1s + build 10s + 冒烟 12s), 产物 6.2M; 冷缓存另加 npm ci 约 22s (实测 37s 级).

## 3 铺设服务根与数据交付

```
python3 tools/stage.py frontend                        # 前端产物 -> serve-root/
python3 tools/stage.py data <库>/.codebase-map/cc.json # 数据副本 -> serve-root/<库名>-<hash8>.cc.json
```

- 键名 `<库名>-<8 位路径哈希>.cc.json`: 哈希 = sha256(库路径 realpath) 前 8 位; 同名不同库不互相覆盖, 重跑同一库覆盖同一键.
- `?file=` 取的是页面同源相对路径, 前端 `<base href="./">` + CSP `self` 要求数据与 index.html 同目录, 所以副本必须落 serve-root; 服务不给根外软链放行, 副本用复制不用软链.
- 交付 URL: `http://<宿主局域网 IP>:<端口>/?file=<键>`. 也可在浏览器里手动选文件.
- 不要用 `python3 -m http.server 8090 -d ~/.agents/codebase-map/serve-root` 临时查看页面: 它会占住 8090, 之后 `serve` 按 `port_in_use` 拒绝启动 (不换端口不接管); 页面查看一律用 `serve`.
- 上游是 hash 路由 (视图切换只改 `#` 后部分), 不需要也不做任何深链回退.

## 4 分析端命令 (`build` 已封装, 见 `SKILL.md`; 本节保留为人工通道与实测依据)

```
podman pull docker.io/codecharta/codecharta-analysis:2.3.0
# 依赖图 (rootless 必须 --userns=keep-id 才能写宿主目录)
podman run --rm --network=none --userns=keep-id \
  -v <目标库>:/proj:ro -v <输出目录>:/out \
  docker.io/codecharta/codecharta-analysis:2.3.0 \
  ccsh dependencyparser /proj -o /out/deps.cc.json -nc
# 指标 + 合并 (官方管道 unifiedparser|dependencyparser 在本环境损坏, 走官方 merge 替代)
podman run --rm --network=none --userns=keep-id -v <目标库>:/proj:ro -v <输出目录>:/out \
  docker.io/codecharta/codecharta-analysis:2.3.0 ccsh unifiedparser /proj -nc -o /out/metrics.cc.json
podman run --rm --network=none -v <输出目录>:/out \
  docker.io/codecharta/codecharta-analysis:2.3.0 ccsh merge /out/metrics.cc.json /out/deps.cc.json -o /out/merged.cc.json -nc
```

- 指标与展示按官方的来: 3D 城市面积=rloc, 高度/颜色=complexity, 不自建指标, 不改默认 URL 参数; 层号 (level) 在官方依赖视图看 (页签 `依赖`, 自带"位于环中/指向上一层"过滤). 数据里 level 在 dependency lens, 不在 metrics, URL 绑 level 会被前端静默改写 (实测), 不要用 `?height=level`.
- 权威数据落点: `<目标库>/.codebase-map/cc.json`, 再用 stage.py data 铺副本.

## 5 大库观感手段

搜索/过滤框定位文件; URL 参数 `?area= / ?height= / ?color=` 绑官方指标 (只绑 metrics lens 里存在的指标); 依赖视图默认只显示环与向上依赖; 聚焦文件夹缩小范围. 何时值得做服务端聚合, 等实际看过大库再定.

## 6 升级上游前端

1. 改 `tools/build-zh.sh` 里的 `CC_TAG` (当前 `vis-2.9.1`), 重跑; 缓存整体替换, node_modules 随克隆重装.
2. 看两个数字: `--check` 的未使用词条 (上游删改的文案) 与报告的未命中 (没翻的).
3. 新文案挖掘: `CC_ROOT=<cache>/src/visualization/app python3 tools/scan-candidates.py ts|lit` (通道 B/C 候选; 通道 A 看 stat-A.json 的 untranslated); 逐条人工判定后补进 `i18n/` 三本词表.
4. 首个会红的点: `patch-package` 的 `echarts-wordcloud+2.1.0.patch` 因上游依赖变动冲突, build 第一步失败 (实测); 升级后若红, 需人工核对补丁.
5. 不跑上游单测: 汉化会打掉 62 个测试文件里的可见文本断言, 这是接受的成本, 质量由渲染冒烟保证.

## 7 词表格式 (i18n/)

三本词表都是 TAB 分隔:
- `zh.txt` (通道 A): `英文原文<TAB>中文`; 键从统计报告原样拷贝 (含 `&amp;`/`&#8217;`/尾随空格), `{{ }}` 插值写成 `{{0}}`, 译文可重排; 译文禁裸 `< > &`.
- `zh-ts.txt` (通道 B): `文件相对路径<TAB>英文整条字面量<TAB>中文`; 模板字面量的每个 `${...}` 写成 `⟦0⟧` (按出现顺序), 译文恰好各含一次可重排; 真实换行写 `\n`; 译文 `(空)` 表示替换为空串 (仅拼接句首尾段).
- `zh-lit.txt` (通道 C): 同 B, 目标是 `.html` 绑定/插值内的字面量, 用 `localize_ts.py --allow-any` 应用.
- 术语单一译法: Area=面积, Height=高度, Color=颜色, Edges=边, Labels=标签, Scenario=场景, Folder=文件夹, Flatten=压平, Metric=指标, Dependencies=依赖, Inspector=检查器, Badge=徽标, Node=节点, Building=建筑; 语境不同才按文件覆盖.

## 8 已知坑 (全部有实测依据)

1. **多命中复核项** (词表键在同一文件出现多次, 脚本报 ERROR 但全部替换, 逐条人工核过同义): metricTitles `Cyclomatic Complexity`x2 (complexity 与 sonar_complexity 同标题), mapColorLabel `⟦0⟧ to ⟦1⟧`x5 (区间格式), fixedFolderValidator `⟦0⟧ Found: ⟦1⟧`x4 与 `⟦0⟧ and ⟦1⟧`x2, fileValidator `...Found duplicate of...`x2, inspectorBadges `package ⟦0⟧`x2, export3DMapDialog `Change/Switch and continue`x2 (按钮+消息引用), 通道 C 的 `Copied!`/`Copy path`x2 (title+aria-label 同按钮) 等.
2. **词表键必须从报告原样拷贝**: 带 HTML 实体 (`&hellip;`) 与尾随空格的键手打会永不命中; 拼接前缀键 (如 `'Colour of: '`) 的译文也要带对应空位.
3. **模板字面量嵌套替换分两轮**: 先普通字面量 (含模板内层) 后模板外层, 外层重建时保留内层译文; 反引号串里带 `` \` `` 转义的仍跳过并报 SKIP.
4. **场景文件会存中文串**: 布局算法名 (`矩形树图`) 与排序名 (`名称`) 是枚举值字符串, 汉化后保存的场景/会话里记录中文; 跨"中文构建/英文官方版"互导场景文件会认不出, 恢复失败会提示"以下属性未被恢复".
5. **checksum 功能受限**: 浏览器只在 https 或 localhost 下能算文件校验和, 局域网 http 访问时加载大文件无校验和 (上游行为, 界面有中文提示).
6. **冒烟样例的条件渲染**: 领域页签与依赖视图"层级"段分别随 domain lens / packages 数据出现, 合成冒烟样例没有这两类数据, 缺它们是预期 (冒烟已按此写断言).
7. **docker/podman**: 命令按 podman 写 (宿主无 docker); rootless 必须 `--userns=keep-id`, 否则写盘 Permission denied.
