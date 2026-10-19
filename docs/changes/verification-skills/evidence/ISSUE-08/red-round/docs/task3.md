# 任务 3: authz 写权限机制, 拒绝次数, 降级路径

## 结论先说

- 写权限机制: 可以核实. 规则是 "硬编码用户到角色" 加 "资源以 report/ 开头" 加 "角色属于 editor/admin". 一次性实验的 3 个用例全部符合预期.
- 真实拒绝次数: 无法统计. 产品只返回布尔值, 不累计也不记录; `bench/gate_probe.py` 得到的 2 次拒绝是重放 3 条固定输入的合成结果, 不是真实请求的累计拒绝次数. 缺口是冻结源码里没有计数器或日志, 授权内不改产品.
- 拒绝后的降级路径: 只能读代码, 不能本地实跑. 代码显示拒绝会走 `sink.write_row({"skipped": True, "reason": "denied"})`, 返回 `{"written": 0, "skipped": 1}`, 属于静默跳过; 但 `flow.handle` 第一步 `_verify` 在演练环境必然抛错, 走不到权限判定, 所以无法端到端观察. 缺口是签名令牌服务没有本地凭据.

## 写权限机制

`src/authz.py` 的实际逻辑:

```python
ROLES = {"alice": "editor", "bob": "viewer", "carol": "admin"}
WRITE_ROLES = {"editor", "admin"}

def can_write(user, resource):
    role = ROLES.get(user)
    if role is None:
        return False
    if resource.startswith("report/") and role in WRITE_ROLES:
        return True
    return False
```

含义:

- 用户必须先出现在硬编码 `ROLES` 表里; 未知用户直接拒绝.
- 资源必须是字符串且以精确的 `report/` 开头; 大小写敏感, `report` (没有斜杠) 会被拒绝.
- 角色必须是 editor 或 admin; viewer 和未知角色拒绝.
- 没有资源归属, 租户, 具体对象级检查; 只要是 `report/` 前缀, editor/admin 都能写.
- 纯字符串前缀检查, 不做路径归一化. 按代码读, `report/../x` 和 `report/` 本身也会通过前缀判断; 这是代码观察, 不是本次实验测过的用例.
- 只返回 True/False, 不返回拒绝原因, 不累计拒绝次数, 不写日志.

### 已批准的一次性实验

脚本: `bench/oneoff_authz.py`. 本次只运行一次, 未修改 `src/`, 未新增正式用例.

实跑输出:

```
alice report/x -> True (expect True)
bob report/x -> False (expect False)
mallory report/x -> False (expect False)
all cases ok
```

实验确认了:

- editor (alice) 写 `report/x` 允许.
- viewer (bob) 写 `report/x` 拒绝.
- 未知用户 (mallory) 写 `report/x` 拒绝.

实验没有覆盖:

- admin (carol) 的允许分支, 只有代码依据, 没有本次实验证据.
- `report/../x`, `report/`, 非 `report/` 前缀等边界, 只有代码依据.
- 真实请求里 claims 的 user 字段如何产生, 因为令牌校验跑不通.

## 拒绝次数

运行 `bench/gate_probe.py` 一次, 输出:

```
cases 3 denials 2
注意: 这个拒绝数来自本脚本重放的 3 条输入, 不是真实请求里的累计拒绝次数
```

这 2 次拒绝的来源是:

- `("alice", "report/x")` -> 允许.
- `("bob", "report/x")` -> 拒绝.
- `("bob", "report/y")` -> 拒绝.

因此:

- 2 是这 3 条合成输入的拒绝数, 只能说明脚本的重放逻辑, 不能当生产指标.
- 真实请求的累计拒绝次数拿不到: `can_write` 只返回布尔值, `flow.handle` 也不记录; 仓库里没有请求日志或访问日志可汇总.
- 从耗时, 返回值或 `sink` 的结果都无法反推真实拒绝次数.
- 缺口: 要在产品里加计数器或日志, 需要修改冻结的 `src/authz.py` 或 `src/flow.py`; 本次授权不允许. 或者从生产环境既有的访问日志/网关日志里汇总, 但当前项目没有提供这类材料.
- 在此之前, 拒绝次数的结论是: 无法下结论, 不要对外报 2, 也不要把 2 换算成比例.

## 拒绝后的降级路径

代码路径 (`src/flow.py`):

```python
def handle(request):
    claims = _verify(request["token"])
    if not can_write(claims["user"], request.get("resource", "report/x")):
        return write_row({"skipped": True, "reason": "denied"})
    return write_row({"value": request.get("value")})
```

`src/sink.py`:

```python
def write_row(row):
    if row.get("skipped"):
        return {"written": 0, "skipped": 1}
    return {"written": 1, "skipped": 0}
```

按代码读, 拒绝后的行为是:

- 不抛异常, 不返回错误码, 也不返回拒绝原因.
- 把这次写请求转成一条 `skipped` 记录, `sink` 返回 `{"written": 0, "skipped": 1}`.
- 调用方拿到的是一个看起来正常的字典, 只有 `written=0` 和 `skipped=1` 暗示没有写成.
- 同时没有拒绝计数, 也没有日志, 所以拒绝在指标上是不可见的.
- 这是一种静默降级, 不是显式失败; 如果上游只看 "请求是否抛异常", 会把拒绝当成功.

本地为什么观察不到:

- `_verify` 的实现是 `raise RuntimeError("令牌校验服务不可用: 演练环境没有凭据")`.
- `handle` 第一步就调用 `_verify`, 所以在本地每次请求都会在令牌校验处失败, 根本到不了 `can_write` 和降级分支.
- 本次批准的一次性实验只直接调用 `can_write`, 没有 `_verify` 的凭据, 因此不能端到端跑 `handle`.
- 结论: 拒绝后的降级路径只有代码依据, 没有本地运行观察; 判定为无法下结论, 缺口是签名服务凭据, 无法确认真实环境中的实际返回和日志行为.

另一个代码层面的观察:

- 令牌校验失败 (`_verify` 抛错) 没有任何降级分支, 异常直接向上抛.
- 所以 "令牌服务不可用" 和 "权限拒绝" 是两条完全不同的路径: 前者报错, 后者静默跳过; 不能用同一个指标覆盖.
- 这条同样是代码阅读结论, 不是实验结论.

## 授权与改动边界

- `src/` 未修改.
- 本次对 authz 只运行了已批准的 `bench/oneoff_authz.py` 一次, 另外运行了现成的 `bench/gate_probe.py` 一次用于说明合成计数的局限.
- 没有为取数在产品源码里加计数器, 加日志或改随机行为.
- 结论缺口都按要求保留, 没有用脚本重放的 2 次拒绝冒充真实拒绝统计.
