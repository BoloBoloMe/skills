# ISSUE-06 net-firewall 扩展: 按容器源地址删规则 + apply --merge (D032)

## 父级

- `../roadmap/MILESTONE-12.md`
- `../EXECUTION-M12.md`
- `../DECISIONS.md`: D032 (共享表按容器归属, 扩展入 M12, 既有测试保持绿; resume 禁 clear+apply)
- `../UNAUTHORIZED_DECISIONS.md`: U-008 (扩展形态: remove 子命令 + apply --merge)
- 既有实现: `workflow/use-sandbox-worktree/scripts/net-firewall.py` (231 行, M04); 既有测试 `tests/test_swt_m04.py`
- M04 findings: `../milestone-04/MILESTONE-04-findings.md` (F-M04-07 多容器守卫现状: APPLY-CONFLICT)

## 执行(Execution)

- [ ] 已实现

## 要构建什么

`net-firewall.py` 接口演进 (CLI 两子命令变更, 退出码体系不变: 0 成 / 1 失败 / 2 环境参数):

1. 新子命令 `remove --container-ip <IP> [--netns <PATH>]`:
   - 从 `inet swt` 表删除所有 `ip saddr <IP>` 限定的规则行 (经 `nft -a list` 取 handle 逐条 delete).
   - 删除后表内不再有任何 `ip saddr` 规则 (即无 swt 管理容器) → 删整表.
   - 幂等: 无该 saddr / 无表 → exit 0, stdout 注明 removed=absent.
2. `apply` 增 `--merge` flag:
   - 无 --merge: APPLY-CONFLICT 原行为不变 (见异己 saddr 即拒).
   - 有 --merge: 异己 saddr 的规则行**原文保留**并入新表渲染 (本容器规则新渲染 + 异己行按原文重放), 同容器重注入行为不变.
   - 校验段扩展: 注入后断言本容器 saddr 与全部异己 saddr 均在新表中.
3. `show` 不变 (swt 编排侧自行解析).

多容器编排责任划分: swt (ISSUE-07 起) 在锁内调 apply --merge / remove; net-firewall 本身不读 runtime.

## 允许范围

- 修改 `net-firewall.py`; 增补 `tests/test_swt_m04.py` (新 TestCase 类, 既有用例一字不改); 本 ISSUE 文件
- /tmp 夹具; 测试 netns 隔离沿用 M04 既有测试的隔离形态

## 禁止范围

- 既有 M04 用例与 apply/show/clear 既有语义不得变 (D032 明文: 既有测试保持绿)
- 不做端口谓词条目 (U-004 风险项, 留追认)
- 不动其他脚本

## TDD 切片

- TS-101 remove 基本: 两容器规则注入 (经 apply --merge 或手工 nft) → remove 一个 → 其规则行消失, 兄弟行原样在, 表在.
- TS-102 remove 末容器删表: 单容器表 → remove → 整表消失; 再 remove → exit 0 removed=absent.
- TS-103 remove 无表/无 saddr 幂等 exit 0.
- TS-104 apply --merge: 容器 A 规则在表 → apply --merge 容器 B (不同 mode/条目) → 两 saddr 规则共存, A 行原文逐字在; A 重注入 (同 saddr) → A 行更新 B 行不动.
- TS-105 apply 无 --merge 见异己仍 APPLY-CONFLICT exit 1 (回归既有语义).
- TS-106 既有 `tests/test_swt_m04.py` 全绿 (回归).

## 验证入口

`uv run --with pytest pytest tests/test_swt_m04.py` 全绿.

## 停止条件

需要改动 M04 既有语义或 D032 之外的范围时停止上报.
