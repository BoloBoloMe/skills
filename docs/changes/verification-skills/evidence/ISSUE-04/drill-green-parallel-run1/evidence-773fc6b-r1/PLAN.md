# 派工计划 (第 1 轮独立验收)

- 目标提交: 773fc6bf093c3b17f18a8817f924536902f13d2b (HEAD, 提交时间 2026-10-19 21:18:27 +0800)
- 判据来源: `docs/changes/relay-board/PRODUCT.md` (`验收标准` 节, `<!-- confirmed-flow: v1 -->`)
- 证据目录: `docs/changes/relay-board/evidence-773fc6b-r1/` (本轮新建, 不覆盖旧证据)
- 证据目录影响判断: 项目无构建脚本, 无 pytest 配置 (无 pyproject.toml / pytest.ini / setup.cfg / tox.ini), pytest 只收集 `test_*.py`,
  证据文件不含该命名模式, 不会被测试发现; `app.py` 不读取 `docs/`. 故证据写在仓库内安全.
- 必验清单共 10 项: 8 个场景 (AC-001-1, AC-001-2, AC-002-1, AC-002-2, AC-003-1, AC-003-2, AC-004-1, AC-005-1) + 2 条审计规则 (BR-001, BR-002)

## 场景组划分

| 组 | 承接人 | 承接标准 | 证据子目录 |
| --- | --- | --- | --- |
| G1 alpha 组 | ver-alpha | AC-001-1, AC-002-1, AC-003-1, AC-004-1 | `ver-alpha/` |
| G2 beta 组 | ver-beta | AC-001-2, AC-002-2, AC-003-2, BR-001 (审计) | `ver-beta/` |
| G3 只读交叉核对组 | ver-read | AC-005-1, BR-002 (审计) | `ver-read/` |

## 共用准备 (只做一次)

实例启动 (端口 18101 alpha, 18102 beta, 数据目录 `runtime/alpha` `runtime/beta`, 共享目录 `runtime/shared`) 由 **ver-alpha** 一次性完成,
并把 `health` 原始输出存到 `ver-alpha/`; 完成后写标记 `coord/instances-up.txt` (含时间戳)。
ver-beta 与 ver-read 不重启实例, 不新建第二套目录, 只引用 ver-alpha 启动的实例, 并在自己材料里记下这一点。

## 争用片段与先后顺序

1. **共享记录写入片段**: AC-003-1 (值 alpha) 必须先于 AC-003-2 (值 beta)。
   依据: AC-003-1 假定 `runtime/shared/record.jsonl` 尚不存在, AC-003-2 假定记录中已有 alpha 条目。
   顺序: ver-alpha 完成 AC-003-1 后写标记 `coord/record-alpha-done.txt`; ver-beta 等到该标记出现再做 AC-003-2 与 BR-001。
   记录写入的实际执行者因此只有 ver-alpha (第 1 段) 与 ver-beta (第 2 段)。
2. **事件日志只增不改核对 (BR-002)**: 必须在无并发写入的安静窗口执行。
   依据: 任务描述与验收者并行写入会让"读前后内容不变"无法归因。
   顺序: ver-read 先做 AC-005-1 (纯只读); 等 `coord/alpha-writes-done.txt` 与 `coord/beta-writes-done.txt` 两个标记都出现后,
   再对同一实例做 前哈希 -> `python3 app.py log` -> 后哈希 的安静窗口核对, 并记录开始/结束时间与之前所有写入者的名字。
3. **只读检查不受争用影响**, 照常并行: AC-001-1/2 (status), AC-005-1 (截图 + report), 以及每组的本地文件读取。

## 并行收益与人数依据

- G1 与 G2 分别占用各自实例的端口与数据目录, 唯一交叉点是共享记录的先后顺序 (以标记交接, 不阻塞其余条目), 可同时开工。
- G3 的两项是跨实例只读交叉核对。若交给 G1 或 G2 的写入者, 就是让写事件日志的会话给自己的写入做"只增不改"审计, 独立性受损;
  故单列一名只在最后做安静窗口核对的验收者, 收益是独立交叉核对, 成本是一个额外会话 (无重复准备)。
- 当轮可用非作者验收者 3 名, 计划人数 3 名, 组数 3 个; 三组都标为并行 (G3 的 BR-002 段是受限片段, 其 AC-005-1 段并行)。
- 没有"每个场景一个会话"的拆分, 也没有为凑人数制造重复准备。

## 原始材料归属

- `ver-alpha/`: 实例启动与 health 输出, AC-001-1/AC-002-1/AC-003-1/AC-004-1 的命令、原始输出、退出码、时间。
- `ver-beta/`: AC-001-2/AC-002-2/AC-003-2 的原始输出与 BR-001 的记录文件原件与比对过程。
- `ver-read/`: AC-005-1 的截图原件、status-page 原始 HTML、report 输出; BR-002 的前后哈希与 `events.log` 原件副本。
- 共享材料 (截图、events.log、record.jsonl 副本) 可在组间传递, 但交出方须记产生者会话标识与时间, 接收方自行核对适用范围后独立下结论。

## 验收者未参与事实

三名验收者均为本轮新开会话, 创建时间晚于被验提交时间 2026-10-19 21:18:27 +0800, 不继承实现会话过程 (不使用 `--continue` / `--resume` / `--fork`)。
每条派工记录里保存其会话标识与创建时间。
