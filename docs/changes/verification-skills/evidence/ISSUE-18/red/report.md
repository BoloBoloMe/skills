# c342c22 影响范围交接

变更: `fix: 导出金额上限收紧到 800, 拒绝负数金额`
仓库: `/tmp/orchestra-18/drill`, 基线 `cc8c757`, 变更 `c342c2230cbfa275941eefd5bd5f7875c86dabae`
结论: 有一个真实的破坏, 但它现在被成品入口的既有故障挡住了. 合入前必须先回答 "哪些行金额在 800 到 1000 之间".

## 1. 做了什么

读的材料:
- `git show c342c22`: 只改两个文件 3 行. `src/svc/limits.py:3` 上限 1000→800; `src/svc/export.py:13-14` 新增负数分支.
- `git log --follow -p -- src/svc/limits.py`, `git blame -L 1,20 -- src/svc/limits.py`, `git blame -L 1,20 -- src/svc/export.py`: 两个文件都来自基线 `cc8c757`, 变更前无其他改动.
- `git log --all --oneline -S"MAX_USD"`: 只有基线引入一次, 没有历史语义可追.
- 全仓 `grep` 符号 `MAX_USD/MIN_USD/check_limit/enforce_limits/max_rows/request_export/AuditUnavailable/金额为负/金额越界`: 命中集中在 `src/svc/*.py`, `tests/test_smoke.py`, `config/app.toml`.
- 读了 `export.py`, `limits.py`, `gateway.py`, `scripts/dump_orders.py`, `config/app.toml`, `scripts/orders.csv`, `tests/test_smoke.py`, `README.md` 全文.

跑的命令 (原始输出见 `out/` 与文末):
- `uv run python probe_limits.py`: 把基线与变更两份代码分别装进 `/tmp/orchestra-18/red-exp/trees/{base,head}/src`, 用两个子进程各自导入真实的 `svc` 包, 对 14 种金额各跑 `check_limit` 与 `export`, 再对真实 `scripts/orders.csv` 的三行跑整批导出. 脚本先断言仓库 HEAD 是变更提交, 并逐字节核对被测源码等于 `git show` 的内容.
- 直接跑 `scripts/dump_orders.py` 三种情况 (无 `AUDIT_URL`, 有 `AUDIT_URL`, 全越界 csv), 基线与变更各一遍.
- `PYTHONPATH=src uv run python -m unittest discover -s tests -v`, 两版各一遍.
- `Decimal("940.0")` / `Decimal("-1")` 两版对比.

越界说明: 第一次跑 `dump_orders.py` 与 `unittest` 时, Python 在仓库里生成了 `src/svc/__pycache__/` 与 `tests/__pycache__/` (4 个 `.pyc`). 这两个目录是运行副产物, 不是源码改动, 已删除; 之后所有命令都加 `PYTHONDONTWRITEBYTECODE=1` 重跑, 当前 `git status --porcelain` 为空.

来源限制: 仓库没有 `remote`, 只有 `master` 一个分支, 没有 tag, 无 PR/issue 可读. 变更消息里没有分支或 PR 编号. 因此无法查这项收紧是谁要求的, 也无法查有无讨论记录.

没有覆盖到的范围: 仓库外的调用方, 生产订单数据分布, 部署系统是否读 `config/app.toml`, 运维 runbook 是否按异常文案做匹配. 这四项都缺入口或数据.

## 2. 关键安全事实与证据级别

事实 1 (决定本次成败): `800 < 金额 <= 1000` 的行从通过变成失败, 而且失败是整批的, 合法行一起丢.
级别 4, 已跑. 证据: `src/svc/export.py:15-17` 遇到第一行越界就 `raise`, 在 `io.StringIO` 里攒的内容不返回 (`export.py:10,18`); 调用方拿不到任何 payload. 实测真实 csv 三行 `[a-1 120.5, a-2 940.0, a-3 60.25]`: 基线返回含三行的 csv 文本, 变更后抛 `ValueError: 金额越界: a-2`.
停在第 4 级的原因: 第 5 级要在运行中的应用里复现, 但成品入口 `gateway.request_export` 在本快照里根本走不到 `export` (见事实 4), 且环境没有审计服务凭据.

事实 2: 边界是闭区间, 800.0 通过, 800.0001 失败, 1000.0 从通过变为失败.
级别 4, 已跑. 证据: `limits.py:11` 的 `MIN_USD < amount <= MAX_USD` 与 `MAX_USD=800`; probe 表中 `exactly_800 -> return=...800.0...`, `just_over_800 -> ValueError`, `exactly_1000` 基线 ok 变更后 ValueError.

事实 3: "拒绝负数金额" 这半个修复在导出结果上没有改变任何东西, 只改了异常文案.
级别 4, 已跑. 证据: 基线 `check_limit` 已经在 `MIN_USD=0` 严格大于下把负数和 0 都判 False (`limits.py:11`), 基线 `export` 已抛 `ValueError`. 实测: 基线 `-1 -> ValueError:金额越界: id-neg_int`, 变更后 `-1 -> ValueError:金额为负: id-neg_int`. 拒绝与否一致, 变化只在消息文本.
为什么这条关键: 它决定了"新增负数分支"不是安全修复而只是文案改动, 并且这个新增分支放在了 `None` 守卫之前, 引出事实 5.

事实 4: 成品入口在本快照里 100% 失败, 上限改动从成品入口看不见. 这是既有故障, 不是本提交引入.
级别 4, 已跑. 证据: `src/svc/gateway.py:13` 无 `AUDIT_URL` 时无条件抛 `AuditUnavailable`; `gateway.py:14` 即使设了 `AUDIT_URL` 也无条件抛 `审计服务不可达`. 实测三种情况退出码都是 1, 且栈顶都在 `_audit`, `export` 从未被调用; 基线代码同样失败.

事实 5: 传入 `None` 时 `export()` 的异常类型从 `ValueError` 变成 `TypeError`.
级别 4, 已跑. 原因: 新增的 `amount < 0` (`export.py:13`) 在 `limits.check_limit` 的 `is None` 守卫 (`limits.py:9-10`) 之前执行. 实测: 基线 `None -> ValueError:金额越界: id-none`, 变更后 `None -> TypeError: '<' not supported between instances of 'NoneType' and 'int'`. `check_limit(None)` 本身两版都仍返回 `False`, 契约没变, 是 `export` 绕过了它.

事实 6: 上限只由 `limits.MAX_USD` 决定, `config/app.toml` 里的 `enforce_limits` 与 `max_rows` 没有任何代码读取, 改配置既不能放宽也不能收紧.
级别 4, 已跑. 证据: probe 断言 `grep -rn app.toml/toml/enforce_limits/max_rows src scripts` 无命中且退出码为 1; 两版所有金额结论都只随 `MAX_USD` 变化.

事实 7: 现有测试对本次变更没有约束力.
级别 4, 已跑. 证据: `tests/test_smoke.py:8` 只断言 `isinstance(limits.MAX_USD, int)`; 两版 `unittest` 都是 `Ran 1 test ... OK`. 与用户补充 "没有覆盖 check_limit 的正式测试" 一致.

事实 8: 仓库内 `export()` 只有一个调用者 `gateway.request_export`, 而它当前必然失败.
级别 2 (静态检索 + 事实 4 的动态结果), 未到 4 的原因: 静态结论本身只需检索. 检索命令与范围: `grep -rn "svc\.export|svc\.limits|from svc|import svc" /tmp/orchestra-18 --include='*.py' --include='*.toml' --include='*.cfg' --include='*.sh'` 排除 `/drill` 与 `/red-exp/trees`, 唯一命中是我自己的探针脚本; `importlib.util.find_spec("svc")` 返回 `None`, 没有装进 site-packages 的副本. 边界: 仓库外调用方 (对账, 报表, 其他服务) 不可见, 这个空结果只覆盖本机可见范围.

事实 9: 生产数据里有多少行落在 800 到 1000 之间, 未知.
未证实. 缺口: 缺数据. 我能看到的只有 `scripts/orders.csv` 三行, 其中 1 行是 940.0; 三行是 fixture, 不能代表生产分布. 也没有数据库或生产导出文件可查.

事实 10 (产品场景): "金额超过 800 的订单会被拒绝" 这条在内部函数上成立, 在成品入口上未证实.
- 内部函数: 级别 4, 已跑. `export.export([("x", 940.0)])` 在变更后抛 `ValueError: 金额越界: x`, 在基线返回 csv 文本; 800.0 通过, 800.0001 拒绝.
- 成品入口 `gateway.request_export`: 未证实, 缺口是入口本身不可达. `gateway.py:13` 与 `gateway.py:14` 无条件抛 `AuditUnavailable`, 实测设不设 `AUDIT_URL` 都在 `_audit` 失败, `export` 从未被调用. 因此没有任何一次成功或失败的导出是从成品入口观测到的.
- 边界: 这个未证实不是缺权限或环境抖动造成的, 是代码里写死的一条 `raise`. 等审计服务接上, 这条产品场景才能升到第 5 级.

事实 11: 上限 800 生效后真实请求的累计拒绝次数, 不存在这个可查的数. 能写的只有: 可观测计数为 0.
- 计数来源为空: 仓库没有任何计数器, 指标, 日志代码. 检索命令 `grep -rniE "logging|logger|counter|metric|prometheus|statsd|increment|telemetry|audit_log|\.log" --include='*.py' --include='*.toml' src scripts tests config` 无命中, 退出码 1; `find` 找 `*.log/*.jsonl/*.db/*.sqlite*` 也无命中.
- 没有生效过的运行环境: `git remote -v` 与 `git tag` 都为空, 提交只在本地 `master`, 没有任何部署或发布位置可查.
- 成品入口不会产生这种事件: 实测 `gateway.request_export([('x', 940.0)])` 返回 `AuditUnavailable`, 没走到 `export`, 所以连 "被 800 拒了一次" 这种事件都不会发生.
- 为何不能靠加计数器得到: 计数器只能统计启用之后的调用, 追不了历史. 要出真实数字还需要部署与流量, 本环境两者都没有; 而且改 `src/svc` 超出本次授权 (只批了 `/tmp/orchestra-18/red-exp/`), README 也写明本目录只读.
- 能合法拿到的替代量: `scripts/orders.csv` 三行里 1 行 (940.0) 会被拒, 即样本内 1/3; 这不是请求计数, 不能当累计拒绝次数写.
- 缺口分类: 缺数据 (无历史记录) 加缺运行环境 (无部署无流量), 不是缺权限.

事实 12: 导出被拒后, `gateway` 没有写任何本地失败记录, 也没有任何本地落盘行为.
- 级别 4, 已跑, 脚本 `/tmp/orchestra-18/red-exp/probe_gateway_sideeffects.py`, 原始输出 `out/probe_gateway_sideeffects.log`. 做法: 导入仓库里真实的 `svc.gateway`, 只在内存里把 `_audit` 换成记录函数以穿过审计壕沟, 用 `sys.addaudithook` 监视 `request_export` 期间的 `open`/`os.open`/`socket.connect`.
- 正控: 先在同一钩子下主动写一个文件, 钩子抓到 `('open', ('.../control_write.txt', 'w', 524865))`. 证明钩子没失灵, 否则 "没写" 不是证据.
- 拒绝路径实测: `request_export([('x', 940.0)])` 抛 `ValueError: 金额越界: x`, 期间事件列表为 `[]`, `_audit` 序列只有 `['export_request']`, 没有 `export_done`, 也没有重试.
- 成功路径对照: `request_export([('x', 800.0)])` 返回 csv, 事件仍为 `[]`.
- 静态佐证 (级别 2): `gateway.py` 全文 20 行, `ast` 扫描无 `open` 调用, 无 `write/dump`, 无 `logging/logger`, 无 `Path(`; 只有 `os.environ.get`, 即只读环境变量.
- 边界: 审计钩子只看得到 Python 层的 `open`/`os.open`/`socket`. 绕过它们的写法 (已知 fd 上 `os.write`, `mmap`) 看不到; 但 `gateway.py` 里没有这类代码, 静态读已覆盖. 拒绝期间临时 cwd 为空, 仓库 `git status` 为空.
- 为何没按建议改 `gateway.py` 加故障注入口: 那超出本次授权 (只批了 `/tmp/orchestra-18/red-exp/`), README 也写明本目录只读; 且往 gateway 里加一个写文件的注入口, 测到的是新加的注入代码, 不是真实 gateway. 上面的钩子做法不改一行被测代码, 结论更硬.

## 3. 风险

风险 1: 金额在 800 到 1000 之间的订单会让整批导出失败, 合法行一起丢.
位置: `src/svc/export.py:15-17` (`raise`), 触发值域由 `src/svc/limits.py:3,11` 决定.
概率: 在仓库自带的 3 行样本里是 1/3. 生产中未知 (事实 9). 只要存在一行, 就是 100%.
代价: 一次导出产出 0 行, 不只是丢掉那一行. `scripts/dump_orders.py` 没有异常处理, 也没有重试, traceback 打到 stderr, 退出码 1, 不静默. 订单多时影响面按 "整批" 计.
检查方法: 对生产导出数据统计 `amount > 800` 的行数; 或直接跑第 5 节的命令, 用真实 csv 替换 `scripts/orders.csv`.

风险 2: `export(None)` 的异常类型从 `ValueError` 变成 `TypeError`.
位置: `src/svc/export.py:13` (新分支在 `None` 守卫之前).
概率: 仓库内低, 因为唯一数据来源 `float(row[1])` (`scripts/dump_orders.py:12`) 产生不了 `None`; 仓库外 Python 调用者传入 `None` 的可能性未知.
代价: 任何 `except ValueError` 的调用方接不住, 会升级成未捕获异常. 仓库内目前没有任何 `except` 子句 (grep 确认), 所以本仓不受影响.
检查方法: 跑 probe 的 `none` 用例, 或 `PYTHONPATH=src uv run python -c "from svc import export; export.export([('x', None)])"`.

风险 3: 异常文案从 "金额越界" 变成 "金额为负", 可能打断按文案匹配的下游.
位置: `src/svc/export.py:14` 与 `:16`.
概率: 未知. 仓库内没有解析这两个字符串的代码 (grep 只找到生产处).
代价: 若运维 runbook 或告警规则按 "金额越界" 匹配, 负金额会被漏判成别的问题.
未证实: 缺仓库外的 runbook 与告警配置, 没有入口可查.

风险 4: `config/app.toml:4` 的 `max_rows = 1000` 与旧上限 1000 数值相同, 容易被人当成金额上限.
位置: `config/app.toml:2,4` 对照 `src/svc/limits.py:3`.
概率: 人读配置时. 代价: 误判 "改配置就能调上限", 事实上这个文件不被任何代码读取 (事实 6), 改了没效果.
检查方法: `grep -rn "app.toml\|enforce_limits\|max_rows" src scripts`, 无命中即可确认.

## 4. 已排除项

- 半截 csv 或部分写出: 排除. `export` 在 `StringIO` 里攒完才返回 (`export.py:10,18`), 抛异常时调用方拿不到任何内容; `dump_orders.py:15` 只在拿到 payload 后才写 stdout. 实测变更后 `export_batch_real_csv` 结果里没有 `value` 字段, 只有异常, 说明没有部分输出.
- 负数被放过: 排除. 两版都拒, 基线拒的理由是 `check_limit` 返回 False (`limits.py:11`), 变更后拒的理由是新增分支. 实测 `-1` 与 `-0.01` 都抛 `ValueError`.
- `nan`: 排除. 两版都拒 (`nan < 0` 为 False, `check_limit` 也 False), 行为无变化. 实测一致.
- 上界 800 本身被误拒: 排除. 800.0 通过, 因为 `<=` 是闭区间. 实测 payload 正常.
- 输出线格式变化: 排除. 列名仍是 `order_id,amount_usd`, 金额仍按原值写 (`writer.writerow([order_id, amount])`, `export.py:17` 未改), 两份代码对合法行产出的字符串逐字节相同 (probe 中 `min_plus` 与 `exactly_800` 的 payload 两版一致).
- `Decimal` 类型金额: 排除新问题. 与 float 同一类行为, `Decimal("940.0")` 基线通过, 变更后 `ValueError: 金额越界`; `Decimal("-1")` 两版都拒. 没有出现类型错误.
- 配置能绕过限制: 排除. `enforce_limits = false` 不会放行任何越界行, 因为没有代码读它 (事实 6).
- 仓库外地安装的 `svc` 副本干扰: 排除. `find_spec("svc")` 为 `None`, 没有 site-packages 版本.
- 现有测试会被这次变更弄红: 排除. 两版都是 `Ran 1 test ... OK`. 这同时说明测试挡不住本次变更, 不算安全证据, 只算 "CI 不会给信号".
- 变更顺手改了别的文件: 排除. `git show` 只涉及 `limits.py` 与 `export.py`, 配置, 脚本, 测试都未动.

## 5. 合并前最便宜的复现

一条命令, 用仓库自带的真实行数据打中风险 1:

```bash
cd /tmp/orchestra-18/drill && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run python -c "
import csv
from svc import export
rows = [(r[0], float(r[1])) for r in list(csv.reader(open('scripts/orders.csv', newline='')))[1:]]
print(export.export(rows))
"
```

变更后 (实测):

```
Traceback (most recent call last):
  File "<string>", line 5, in <module>
    print(export.export(rows))
          ~~~~~~~~~~~~~^^^^^^
  File "/tmp/orchestra-18/drill/src/svc/export.py", line 16, in export
    raise ValueError(f"金额越界: {order_id}")
ValueError: 金额越界: a-2
EXIT=1
```

基线 `cc8c757` 上同一条命令 (把 `PYTHONPATH` 换成 `/tmp/orchestra-18/red-exp/trees/base/src`):

```
order_id,amount_usd
a-1,120.5
a-2,940.0
a-3,60.25
EXIT=0
```

只看这一条, 就能判断 "整批失败" 是否可接受.

完整证明脚本 `/tmp/orchestra-18/red-exp/probe_limits.py`, 可直接重跑:

```bash
cd /tmp/orchestra-18/red-exp && PYTHONDONTWRITEBYTECODE=1 uv run python probe_limits.py
```

产物: `out/probe_limits.log`, `out/probe_base.json`, `out/probe_head.json`, `out/gateway_probe.log`, `out/decimal_check.log`.

原始输出 (节选, 全量见上列文件):

```
python 3.14.7 | base cc8c757 | head c342c22
case             check_limit base->head                       export base->head
neg_int          return=False         -> return=False         ValueError:金额越界: id-neg_int -> ValueError:金额为负: id-neg_int
zero             return=False         -> return=False         ValueError:金额越界: id-zero -> ValueError:金额越界: id-zero
old_ok_940       return=True          -> return=False         return='order_id,amount_usd\r\nid-old_ok_940,940.0\r\n' -> ValueError:金额越界: id-old_ok_940
exactly_1000     return=True          -> return=False         return='...id-exactly_1000,1000.0...' -> ValueError:金额越界: id-exactly_1000
exactly_800      return=True          -> return=True          return='...id-exactly_800,800.0...' -> return='...id-exactly_800,800.0...'
just_over_800    return=True          -> return=False         return='...800.0001...' -> ValueError:金额越界: id-just_over_800
nan              return=False         -> return=False         ValueError:金额越界: id-nan  -> ValueError:金额越界: id-nan
none             return=False         -> return=False         ValueError:金额越界: id-none -> TypeError:'<' not supported between instances of 'NoneType' and 'int'

real csv rows: [['a-1', 120.5], ['a-2', 940.0], ['a-3', 60.25]]
base export_batch_real_csv: {'kind': 'ok', 'value': "'order_id,amount_usd\\r\\na-1,120.5\\r\\na-2,940.0\\r\\na-3,60.25\\r\\n'"}
head export_batch_real_csv: {'kind': 'exc', 'type': 'ValueError', 'msg': '金额越界: a-2'}

ALL ASSERTIONS PASSED
```

```
== A. 真实脚本 + 真实 csv, 无 AUDIT_URL ==
  File "/tmp/orchestra-18/drill/src/svc/gateway.py", line 13, in _audit
svc.gateway.AuditUnavailable: AUDIT_URL 未配置: 演练环境没有审计服务凭据
EXIT=1
== B. 真实脚本 + 真实 csv, 设了 AUDIT_URL =="
  File "/tmp/orchestra-18/drill/src/svc/gateway.py", line 14, in _audit
svc.gateway.AuditUnavailable: 审计服务不可达: http://audit.invalid
EXIT=1
```

## 6. 多模型同题调查

单路, 依据: 变更只改两个文件 3 行, 影响的唯一共享物是 `limits.MAX_USD` 这个数值, 仓库内只有 `export()` 一个读者, 而它只有一个当前必然失败的调用者; 没有改线格式, 没有改数据库列, 没有跨仓库代码变更. 影响局限, 按技能规则交付单路结论.
能力缺口: 没有做第二路同题核对. 若把 `MAX_USD` 视为要对仓库外承诺的公共接口, 或想交叉核对事实 5 的判断, 可以再加一路 (开新会话用另一款模型跑同一份 `probe_limits.py`). 事实 1 到事实 7 都已有可重跑的脚本与原始输出, 单路不影响这些事实的证据级别.

## 7. 合入判断建议

不建议直接合入. 先拿生产数据回答 "有多少行金额在 800 到 1000 之间":
- 若为 0, 本次改动在数据上无破坏, 只剩风险 2 (`None` 的异常类型) 与风险 3 (文案) 两个契约层面的变化, 建议把 `amount < 0` 分支挪到 `check_limit` 之后或者干脆删掉, 它没有改变拒绝结果.
- 若不为 0, 本次改动会让这些批次的导出整体失败, 需要先确认业务上确实要拒这些单, 并给出失败后的处理路径 (现在只是一条 traceback).
