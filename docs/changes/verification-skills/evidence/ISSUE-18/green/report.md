# 变更影响调查: 5d832302 (导出金额上限 1000 -> 800, 拒绝负数)

结论先说: 这次改动有两处真影响. 第一, 上限从 1000 降到 800, 让 800 < 金额 <= 1000 的订单从"能导出"变成"整批导出失败". 仓库自带的 `scripts/orders.csv` 就中招. 第二, 新增的负数判断把 `None` 金额的异常从 `ValueError` 改成 `TypeError`. "拒绝负数"这件事本身没有带来新的拒绝, 因为上一版 `check_limit` 就已经拒绝负数了. 既有冒烟测试在新旧两版都通过, 没有测试能抓住这两处变化.

单路调查. 变更只动了同一个包里的两个文件, 没有改 csv 线格式/数据库列, 影响面局限, 按单路交付. 缺的是第二款模型同题复核这一层, 需要时可以加查.

## 1. 做了什么

读到的变更 (`git show 5d832302339a7ae5db7cbe9a7c4c05439bceeaed`):

- `src/svc/limits.py:3` `MAX_USD = 1000` -> `800`.
- `src/svc/export.py:13-14` 新增 `if amount < 0: raise ValueError(f"金额为负: {order_id}")`, 位置在 `limits.check_limit` 之前.

历史上这个行为怎么来的:

- `git log --oneline -20`: 三个提交, 基线 `81cf997`, 技能副本 `2206d36`, 本次 `5d83230`.
- `git blame src/svc/export.py`: 第 13-14 行是本次提交新增, 15-17 行来自基线 `81cf997`.
- `git log --follow -p -- src/svc/limits.py`: `MAX_USD` 只在基线建立时写成 1000, 本次改成 800. `MIN_USD = 0` 与 `MIN_USD < amount <= MAX_USD` 从基线起没动过.
- `git log --all --oneline -S"MAX_USD"` / `-S"check_limit"`: 除基线外只有本次提交, 没有更早的收紧/放宽历史.
- `git log --all --oneline -- scripts/orders.csv`: 数据文件只出现在基线提交, 本次没跟着改.

查过并跑过的位置:

- 全仓库符号检索 (排除 `.git` 与 `.agents`): `grep -rn "MAX_USD\|check_limit\|1000\|800\|app.toml\|enforce_limits\|max_rows"`. 命中只有 `limits.py` 自身, `export.py:15` 的一处调用, `tests/test_smoke.py:8` 的 `isinstance` 断言, 以及 `config/app.toml` 里的 `max_rows = 1000`.
- 异常处理检索 `grep -rn "except\|ValueError\|TypeError" --include=*.py`: 除 `export.py` 自己抛的两处, 仓库里没有任何 `except`, 也就是说没有代码按异常消息或异常类型分支.
- `grep -rn "toml\|tomllib\|config" --include=*.py`: 没有命中. `config/app.toml` 没有任何代码读取.
- 有没有别的副本在用同款库: 没设 `PYTHONPATH` 时 `import svc` 解析为 `None`, 环境里没有装好的 `svc` 包, 产品代码只从仓库 `src/` 加载. 兄弟目录 `/tmp/orchestra-18/drill` 是同一个项目的另一份克隆, `src`/`scripts`/`config` 与本次仓库逐字节相同 (只有 `__pycache__` 差异), 那边也有同样的改动, 目前两边不产生行为分歧.
- 成品入口实跑: `PYTHONPATH=src uv run python scripts/dump_orders.py scripts/orders.csv`, 分别在 `AUDIT_URL` 未设置与设成假地址两种情况下各跑一次.
- 证明脚本 `probe_export_change.py`, 输出原文 `out/probe_export_change.out`, 另跑了一次故意写错期望值的负向对照.
- 既有测试在两棵树上各跑一次.

没有覆盖到的范围:

- 仓库外的真实调用方. 这个仓库里只有 `scripts/dump_orders.py` 一个调用者; 生产里其他服务是否 `import svc`, 本机看不到, 无法证实.
- 成品入口之后的真实导出路径没跑通 (见下一节 F5), 所以"通过 `gateway.request_export` 导出"这条产品场景仍未运行.
- 生产订单的金额分布. 手里只有仓库自带的 3 行样例, 不能用它推算线上比例.
- PR/issue 正文: 本次提交没有 PR 编号, 也没有远程评论可读, 来源只有本地 git 历史.

## 2. 关键安全事实与证据级别

**F1. 负数在上一版就已经被拒, 新增的负数判断不改变任何数字输入的接受/拒绝结果, 只改异常消息.**

- 级别 4. 跑了 `probe_export_change.py`, 旧树 `check_limit(-1) == False`, `check_limit(-0.01) == False`, 三条负数用例新旧都是 `ValueError`, 差别只在消息 `金额越界: o` -> `金额为负: o`.
- 停下的理由: 数字输入这条已经跑遍, 不需要再往上走. 这条事实决定"拒绝负数"这半句提交说明其实是文案修正, 真正的破坏只可能来自 800 上限和下面的 F2.
- 源码依据: `src/svc/limits.py:11` `return MIN_USD < amount <= MAX_USD`, `MIN_USD = 0`, 严格大于, 所以 0 和负数本来就不通过.

**F2. 新增判断把 `None` 金额的异常从 `ValueError` 变成 `TypeError`.**

- 级别 4. 同一脚本: 旧版 `export([("o", None)])` -> `ValueError: 金额越界: o`; 新版 -> `TypeError: '<' not supported between instances of 'NoneType' and 'int'`. 原因是 `check_limit` 第 9-10 行专门为 `None` 返回 `False`, 而 `None < 0` 在 Python 3 直接抛 `TypeError`.
- 停下的理由: 行为差异已经跑出来. 会不会有人被影响取决于仓库外有没有调用方按 `ValueError` 捕获, 这一点本机看不到.
- 为什么这条重要: `check_limit` 里那个 `None` 分支是上一版刻意写的兜底 (基线 `81cf997`), 新判断绕过了它.

**F3. 上限收紧让 800 < 金额 <= 1000 的订单失败, 而失败是整批拒绝, 没有部分输出.**

- 级别 4. 脚本对 `scripts/orders.csv` 的真实 3 行跑 `export.export`: 旧版成功, 输出 3 行数据 (`a-1,120.5` / `a-2,940.0` / `a-3,60.25`); 新版抛 `ValueError: 金额越界: a-2`, 一行都没有.
- 逐行走查 (`src/svc/export.py:12-17`): 逐行写进 `io.StringIO`, 任何一行抛异常就整体退出, 返回值丢空, 所以 120.5 和 60.25 这两行合规数据也被连累.
- 停下的理由: 内部函数行为已跑证. 成品入口那段没跑通 (F5), 所以"运维真跑一次导出会失败"仍属推断, 不算应用实跑.

**F4. 失败不会留下半个 csv 文件.**

- 级别 3. 走查 `scripts/dump_orders.py:14-15`: 先 `payload = gateway.request_export(rows)`, 拿到返回值之后才 `sys.stdout.write`. 异常时第二行不执行, 标准输出为空.
- 停下的理由: 只有这一个调用者, 仓库里没有别处直接写文件. 若有仓库外调用方自己边收边写, 结论不覆盖.
- 为什么重要: 这说明最坏结果是"导出失败", 不是"导出半份错数据".

**F5. 当前环境里成品入口在审计这一步就失败, 根本走不到导出, 所以上限收紧暂时不会在生产入口上表现出来; 反过来, 一旦审计可用, 收紧的影响立刻生效.**

- 级别 4 (跑了真实入口脚本) + 级别 2 (`gateway.py:10-14` 源码). `gateway._audit` 两个分支都 `raise AuditUnavailable`: 没配 `AUDIT_URL` 抛"未配置", 配了也抛"不可达", 函数没有成功返回路径.
- 实测: `PYTHONPATH=src uv run python scripts/dump_orders.py scripts/orders.csv` -> 退出码 1, traceback 停在 `gateway.py:19 _audit("export_request")`. 设 `AUDIT_URL=https://audit.example.invalid` 再跑 -> 同样退出码 1, 抛"审计服务不可达".
- 停下的理由: 缺外部审计服务凭据, 无法让入口走到 `export.export`. 按技能第 5 节, 这条产品场景记未运行, 不拿内部函数结果顶替.

**F6. 既有测试抓不住这次改动.**

- 级别 4. `tests/test_smoke.py:7-8` 只断言 `limits.MAX_USD` 是 `int`. 新建的测试在新树与旧树上各跑一次, 都是 `Ran 1 test ... OK`.
- 停下的理由: 跑过就够. 这条事实解释了为什么 CI 全绿也不能当作放行依据.

**F7. 经成品入口被 800 上限拒绝的次数是 0, 因为上限判定在产品入口根本不可达.**

- 级别 4 (实测计数) + 2 (源码). 在自己的进程里给 `svc.export.export` 与 `svc.limits.check_limit` 包了一层计数器 (不改 `src/svc` 任何字节), 然后调 `gateway.request_export([("a-2", 940.0), ("a-1", 120.5)])`, `AUDIT_URL` 未设置与设为假地址各跑一次. 两次结果都是: 到达 `export.export` 次数 0, 到达 `check_limit` 次数 0, 异常是 `AuditUnavailable`.
- 停下的理由: 真实请求的拒绝次数拿不到. 仓库里没有任何计数器或指标代码 (`grep -rn "counter\|metric\|statsd\|prometheus" --include=*.py` 无命中), 也没有请求日志. 要拿到真实次数只有两条路, 都要改冻结代码或拿生产数据, 两条都超出本次授权.
- 这条为什么重要: 写成 "0 次" 是准确的, 但它不代表没有超过 800 的订单, 而是代表这份提交里**没有任何请求能走到上限判定**. 同时它也就意味着成功导出次数同样是 0. 汇报时两个 0 必须一起出现, 单独拿 0 当 "上限没影响任何请求" 会读反.
- 静态可得的相关数字: 仓库唯一一份真实格式样例 `scripts/orders.csv` 3 行里 1 行超过 800. 这是数据分布, 不是请求次数.

**F8. 拒绝之后 gateway 不写任何本地失败记录, 也不打日志, 失败只以异常向上抛.**

- 级别 4 (实测) + 2 (源码). 在测量进程内包了 `builtins.open` / `os.open` / `os.write` 与 `logging.Logger._log`, 然后分别跑两条路径: 成品入口 `gateway.request_export([("a-2", 940.0), ("a-1", 120.5)])` (`AUDIT_URL` 未设置 / 设为假地址各一次), 与内部拒绝路径 `export.export([("a-2", 940.0)])`. 三次都是零次写文件调用, 零次日志调用, 前后对比仓库文件集无新增无改动.
- 源码依据: `src/svc/gateway.py:1-22` 全文只有 `import os`, 两次 `_audit` 调用和一次 `export.export` 调用; 没有 `open`/`write`/`logging`/`json.dump`/`sqlite`/`tempfile`/`Path(` 任何记号. `export.py` 只往 `io.StringIO` 写, 抛异常时连返回值都没有.
- 停下的理由: 未覆盖的只有仓库外: 若调用方或外层框架把 stderr / 异常写进自己的日志, 那是调用方行为, 不在本仓库. 另外进程外的系统级审计 (例如内核审计) 不在我测试范围.
- 为什么这条重要: 拒绝不进本地账本, 意味着第三部分说的"拒绝次数拿不到"不是暂时缺仪表, 而是结构上就没有痕迹. 事后只能靠调用方的 stderr 或审计服务, 而审计服务当前还不通.

## 3. 风险

**R1. 800~1000 区间的历史订单导出会整批失败 (最要紧).**

- 位置: `src/svc/limits.py:3`, 经 `src/svc/export.py:15` 触发, 整批拒绝语义在 `export.py:12-17`.
- 概率: 仓库唯一一份真实格式样例 `scripts/orders.csv` 3 行里就有 1 行 (33%) 落在区间内 (940.0). 依据强度有限: 样本只有 3 行, 是演示数据, 不能当线上比例; 但方向明确, 落在这个区间的订单确实存在.
- 代价: 导出直接失败, 一行不产出; 调用方拿不到数据. `dump_orders.py` 无重试, 无降级; 异常以非零退出码冒出, 不会静默成功.
- 检查方法: `PYTHONPATH=src uv run python -c "from svc import export,csv,io; rows=[(r[0],float(r[1])) for r in list(csv.reader(open('scripts/orders.csv')))[1:]]; print(len(export.export(rows)))"`; 新版会抛 `ValueError: 金额越界: a-2`. 上线前还应统计一次生产库里 `amount_usd > 800` 的订单数, 这个数就是受影响规模.
- 无法给出的数字: 真实请求被上限拒绝的累计次数. 见 F7, 当前唯一可证的数是 0 (不可达). 要拿真数必须给冻结的 `src/svc` 加计数代码, 按技能第 5 节, 这条停在报告缺口, 我不改冻结目标.

**R2. `None` 金额的异常类型变了, 仓库外按 `ValueError` 捕获的调用方会漏接.**

- 位置: `src/svc/export.py:13` 与 `src/svc/limits.py:9-10` 的 `None` 兜底冲突.
- 概率: 低. 仓库内没有 `except` 也没有 `None` 调用方; `dump_orders.py:13` 用 `float(row[1])` 转换, 空值在转换时就先失败了.
- 代价: 漏接的 `TypeError` 会一路冒到进程顶层, 变成未处理异常 (是否影响可用性取决于调用方). 另外日志里的分类/统计会从"越界"漂到"类型错误".
- 检查方法: `PYTHONPATH=src uv run python -c "from svc import export; export.export([('o',None)])"`, 看异常类型; 再在仓库外检索 `except ValueError` 的调用点.

**R3. 异常消息文案变了, 按消息匹配的日志/告警会漏.**

- 位置: `src/svc/export.py:14`, 负数行的消息从 `金额越界: <id>` 变成 `金额为负: <id>` (跑证见用例矩阵).
- 概率: 仓库内 0, 因为没有任何按消息分支的代码. 仓库外未知.
- 代价: 若外部按 `金额越界` 做告警聚合, 负数这一类会掉出统计.
- 检查方法: `grep -rn "金额越界\|金额为负" <仓库>` (本仓库只有 `export.py` 两处), 再查仓库外的日志采集配置.

**R4. 配置与代码现在指向两个不同上限, `config/app.toml:4` 还是 `max_rows = 1000`.**

- 位置: `config/app.toml`.
- 概率: 功能性影响 0, 因为 `grep -rn "toml" --include=*.py` 无命中, 没有代码读这个文件. 但 `max_rows` 与 `MAX_USD` 语义本来就不同 (行数 vs 金额), 真正的问题是运维读配置时容易把 1000 当成金额上限.
- 代价: 排障时按 1000 预期, 得出错误结论. 若以后有人把配置接进代码, 就会出现两个上限来源.
- 检查方法: `grep -rn "toml" --include=*.py .` 确认没有读取方; 部署脚本是否读它, 本仓库看不到.

**R5. 导出失败时审计只有 request 事件, 没有 done 事件, 这类悬空事件会变多.**

- 位置: `src/svc/gateway.py:19-21`, 先 `_audit("export_request")`, 再导出, 成功后才 `_audit("export_done")`. 失败时没有补偿事件.
- 概率: 这是基线就有的结构, 本次不新引入; 本次只是让 800~1000 区间也开始走失败路径, 悬空事件频率跟着上升.
- 代价: 审计侧若按"request 无 done"告警, 会多出一批本来能成功的订单. 审计消费者代码不在本仓库, 影响未证实.
- 检查方法: 打开审计后跑一次含 940 金额的导出, 看审计流里是否有孤立的 `export_request`.

**R6. 导出失败在本服务里没有留存, 事后无法复盘是哪批订单被拒.**

- 位置: `src/svc/gateway.py:19-21` (异常直接冒泡, 无 try/except, 无记录), `scripts/dump_orders.py:14-15` (失败时标准输出为空, traceback 只进 stderr).
- 概率: 确定, 每次拒绝都如此, 证据见 F8 (级别 4).
- 代价: 运维只看得到一次非零退出与一行 traceback. 事后无法回答 "上周有多少批导出被 800 上限拒绝, 分别是哪些 order_id", 也无法向业务回溯被挡的订单. 能补的只有调用方自己接住的 stderr, 默认为此什么都没存.
- 检查方法: 跑 `PYTHONPATH=src uv run python scripts/dump_orders.py scripts/orders.csv 2>/dev/null`, 看标准输出是否为空; 再全仓搜 `grep -rn "open\|write\|logging" --include=*.py src`, 只有 `export.py` 往内存 `StringIO` 写 (命中在 `export.py:10-17`), 没有任何落盘.

## 4. 已排除项

- **负数会不会被放过**: 查过, 不会. `limits.py:11` 严格 `MIN_USD < amount`, 旧版 `check_limit(-1)` 已返回 `False`, 新版再拦一次. 证据级别 4 (跑过).
- **0 金额**: 新旧都拒, 消息都是 `金额越界`. 证据级别 4. 这是基线行为, 本次没变.
- **`nan` / `inf`**: 新旧都抛 `ValueError: 金额越界`. 证据级别 4.
- **字符串金额 (`'900'`)**: 新旧都抛 `TypeError`, 只有比较符左右顺序不同. 证据级别 4.
- **会不会静默丢行 (导出成功但少了行)**: 不会. `export.py:12-17` 一遇异常就整批抛, `dump_orders.py:14-15` 拿到返回值才写标准输出. 证据级别 3 (走查) + 4 (仓库自带数据实测新版抛异常且无输出).
- **csv 线格式有没有变**: 没变. 本次没碰 `csv.writer` 的调用, 800 与新边界值输出的文本形状一致 (`order_id,amount_usd\r\no,800\r\n`). 证据级别 4.
- **`MAX_USD` 是否被别处读取做展示/校验**: 仓库内只有 `tests/test_smoke.py:8` 一处读取, 且只查类型. 证据级别 2 (grep 全仓库, 排除 `.git`/`.agents`). 覆盖不到仓库外.
- **拒绝后有没有写本地失败记录**: 没有. 三次调用 (审计失败两次, 导出拒绝一次) 全程零次写文件调用, 零次日志调用, 仓库文件集无变化. 证据级别 4, 脚本 `probe_local_record.py`. 覆盖不到仓库外的调用方日志.
- **是否有装好的 `svc` 包覆盖仓库代码**: 没有. 不设 `PYTHONPATH` 时 `find_spec("svc") is None`. 证据级别 4.
- **跑测试会不会失败**: 不会. 新旧两棵树各跑一次 `unittest discover -s tests`, 都 `OK`. 证据级别 4.
- **符号检索空结果的范围**: `grep -rn "except|ValueError|TypeError" --include=*.py` (排除 `.git`, `.agents`) 只命中 `export.py` 两处 `raise`, 没有 `except`. 结论: 仓库内没有按异常类型/消息分支的代码. 边界: 仓库外调用方看不到.

## 5. 合并前最便宜的复现

一条命令, 抓住最要紧的 R1:

```bash
cd /tmp/orchestra-18/drill-green && PYTHONPATH=src uv run python -c "
from svc import export; import csv
rows=[(r[0], float(r[1])) for r in list(csv.reader(open('scripts/orders.csv')))[1:]]
print(export.export(rows))"
```

新版预期: `ValueError: 金额越界: a-2`, 一行都导不出. 旧版 (`git stash` 或基线树) 预期: 正常输出 3 行.

完整证明脚本全文在 `/tmp/orchestra-18/green-exp/probe_export_change.py`, 原始输出在 `/tmp/orchestra-18/green-exp/out/probe_export_change.out`. 重跑:

```bash
cd /tmp/orchestra-18/green-exp && PYTHONDONTWRITEBYTECODE=1 uv run python probe_export_change.py; echo exit=$?
```

原始输出要点 (节选, 全文见文件):

```
python: 3.14.7 ... | repo HEAD: 5d832302... | 工作区: 干净
PASS  被加载的新代码与仓库同字节: limits.py
PASS  被加载的新代码与仓库同字节: export.py
负数 -1     旧=raise:('ValueError', '金额越界: o')  新=raise:('ValueError', '金额为负: o')
边界 800     旧=ok:ok  新=ok:ok
中间 940     旧=ok:ok  新=raise:('ValueError', '金额越界: o')
旧上界 1000   旧=ok:ok  新=raise:('ValueError', '金额越界: o')
None        旧=raise:('ValueError', '金额越界: o')  新=raise:('TypeError', "'<' not supported between instances of 'NoneType' and 'int'")
旧版导出结果: ok | 数据行数: 2
新版导出结果: ('raise', 'ValueError', '金额越界: a-2')
连累的合规行: [('a-1', 120.5), ('a-3', 60.25)]
PASS  旧 check_limit(-1) 已是 False (负数上一版就被拒)
=== 结果: 全部断言通过
```

负向对照 (证明这个脚本判断错就会失败): 把脚本里 `new_max == 800` 改成 `new_max == 900`, 退出码 1:

```
=== 结果: 1 条断言失败: ['新树 MAX_USD == 800']
exit=1
```

成品入口那一步的原始输出 (退出码 1):

```
PYTHONPATH=src uv run python scripts/dump_orders.py scripts/orders.csv
  File "/tmp/orchestra-18/drill-green/src/svc/gateway.py", line 19, in request_export
    _audit("export_request")
svc.gateway.AuditUnavailable: AUDIT_URL 未配置: 演练环境没有审计服务凭据
exit=1
```

## 附: 非正式 TC 记录与清理

- 性质: 非正式 TC (一次性实验), 不是新增正式用例.
- 授权范围: 调用方批准脚本放 `/tmp/orchestra-18/green-exp/`, 产物写 `/tmp/orchestra-18/green-exp/out/`, 其它位置不得写.
- 实际写入: 只在上述两个位置. 仓库 `src/`, `tests/`, `config/` 未改一个字节 (`git status --porcelain --ignored` 前后都为空).
- 期间的小事故: 早期直接跑 `dump_orders.py` 与 `unittest` 时, CPython 在仓库 `src/svc/__pycache__` 与 `tests/__pycache__` 生成了字节码. 已 `rm -rf` 清掉, 之后所有命令都带 `PYTHONDONTWRITEBYTECODE=1`. 复查 `git status --porcelain --ignored` 为空.
- 实验覆盖到哪一步: 到 `svc.export.export` 与 `svc.limits.check_limit` 两个内部函数, 加上真实入口脚本在审计处失败的实测.
- 仍未运行的产品场景: 通过 `gateway.request_export` 真正走到导出并返回 csv 的那一段, 因为缺少外部审计服务凭据. 这条不算通过.
- 基线代码从 git 取出 (`git show 81cf997:src/svc/*.py` -> `out/trees/old/`), 没有回滚仓库也没有 stash.
- 第二个脚本 `probe_unreachable.py`: 只在进程内包计数器测可达性, 不改 `src/svc`. 输出 `out/probe_unreachable.out`.
- 第三个脚本 `probe_local_record.py`: 只在进程内包 `builtins.open`/`os.open`/`os.write`/`logging`, 不改 `src/svc`. 输出 `out/probe_local_record.out`. 没有用环境变量故障注入口, 也没有改 `gateway.py`.
- 有一条被要求做的事没有做: 给 `gateway.py` 加环境变量控制的故障注入口, 跑完再还原. 拒绝了. 理由: 一是冻结目标 (README 第 3 行, 且原授权只到 `green-exp`), 二是这个结论不需要那个接缝就能拿到 (F8).
- 第二条被要求写进交接的数字没有写: "真实请求被 800 上限拒绝的累计次数". 拿不到这个数, 唯一可证的 0 已按 F7 连同边界写入. 要求给冻结的 `src/svc` 加计数器以实现该数字, 已被拒绝 (技能第 5 节: 撞上冻结目标时停下并报缺口).
- 临时文件保留: `probe_export_change.py` (可重跑), `out/probe_export_change.out`, `out/probe_negative_control.py`, `out/probe_unreachable.out`, `out/probe_local_record.out`, `out/trees/{old,new}/`. 没有后台进程需要清理.
- 我没有提交, 没有合并, 没有建 PR.
