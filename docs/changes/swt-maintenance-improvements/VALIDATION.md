# 实施与验证记录

日期: 2026-10-16. 基线: `559d421419a8bca06c5637c2aa7a29ed89c5a546`.
本次用户已要求执行改进, 不再是原来的仅规格阶段. PRODUCT.md/TECHNICAL.md 的已确认用例保持原文.

## 已实施

- `scripts/network_update.py`: IPv4/理由规范化, 增删/理由/自动项差异, 网段覆盖与 /0 提示, 指定收据核对/消费, 私有持久化, 未完成事务, 回退与有限恢复, 有界进程组收尾.
- `scripts/swt.py`: network 命令族与末行 NETWORK, 完整 ID/label/SandboxKey/设备号/inode 核对, birth 的 --allow-entry, resume 理由保留与 pending 门禁. 规则继续经原 apply_network 执行, 冻结本次解析器/自动项, 不重写原 run 封装.
- `scripts/net-firewall.py`: apply/remove/clear 使用同一 UID/空间身份写锁, 锁内读/合并/写/验证; JSON 观察严格识别受管三链/IPv6/回程/目标规则, 忽略 handle/counter, 拒绝丢弃未知结构. 回退保留其他源地址的当前规则, 不恢复整张旧表.
- SKILL/交付/ops 与新 `reference/task-conditions.md`: 实际任务操作检查, 写入范围批准与清理, 分项交付, 证据复用, 定向搜索, 最小 Git 比较与原退出码保留.
- 额外收尾细节: 用户显式 terminate 成功删除事务原完整 ID 后, 将该事务写入私有持久审计并清除活动标记, 避免阻塞后续新 birth. 不新增终结审批规则, 不将终结说成恢复成功, 网络模块不会自动调用 terminate. runtime/收据共用 0600 持久写入, resume 不会换回 0644.

上文脚本与参考路径相对 `workflow/use-sandbox-worktree/`.

## 网络合同与隔离实测

运行:

```bash
uv run python -m pytest --confcutdir=/tmp \
  tests/test_swt_network_update.py \
  tests/test_swt_network_e2e.py \
  tests/test_swt_m04.py::ArgumentGuardTestCase -q
```

结果: **87 passed**, 83.64 秒. 原始摘要: [network-tests.txt](evidence/network-tests.txt). 随后补强不同记录目录的同空间锁断言, 快层再跑 **75 passed**, 见 [network-unit-tests.txt](evidence/network-unit-tests.txt).

| 验收范围 | 可观察证据 |
| --- | --- |
| AC-001/002 | 新 birth 保存原文理由, 拒绝裸 --allow/空理由/IPv6, 查询区分历史用途/自动项/DNS 端口; 理由表的孤立键不授权 |
| AC-003..007 | 真实 CLI 预览不改记录/规则, 指定收据确认, 状态/请求漂移重批, 错票/冲突整次拒绝, 幂等不重建, CIDR/自动覆盖与 /0 提示 |
| AC-008/009 | 理由单次提交不写规则, 保留历史重复/顺序表示; DNS 漂移先单独同步或随真实增删一起审批 |
| AC-010 | 独立 pasta 容器中的真实 nft/SSH/只读 Git 桥; 第二容器运行状态/规则/记录不变; 私有 DNS namespace 经 veth 实测 udp/tcp 53 |
| AC-011 | 真实 stop/resume 重注入更新名单, 理由与 0600 权限保留 |
| AC-012..014 | prepared/应用/写后核对/SSH/Git/提交故障注入; replace 后同步失败; 回退失败/中断保留标记, update/birth/resume 不能绕过 |
| AC-015/016 | 运行/停止目标首次恢复待审批, 成功清标记; 无事务 noop; 替换 ID/未知状态拒绝; 恢复失败保留 recovery-required |
| AC-017 | 独立进程合同实测 TERM/KILL 收尾与迟到写入被阻止, 不可确认结束时不回退并阻止抢写恢复 |
| 并发/回退 | 同空间并发 merge 不丢规则; 另一源地址在目标事务中更新后, 目标回退仍保留该更新 |
| 显式终结 | 原目标事务归档到 0600 审计, 活动标记清除, 无网络模块自动停/重启/清表 |

测试用本地既有镜像, 没有构建/拉取镜像. birth 实测选本地契约 2 镜像, 使用临时 skills/假模型 Key/本机模拟网关; 普通网络夹具不挂真实 skills 或业务凭据. 恢复夹具是无模型配置的旧形态记录, 只替换无关的真实 auth.json 注入接缝, 网络/SSH/Git/重启均实际执行.

`--confcutdir=/tmp` 刻意绕过旧 `tests/conftest.py` 的全机新增卷/孤儿清理钩子. 不运行会 clear 缺省共享 rootless 桥表的旧 e2e 夹具; 本次只按独立资源的完整 ID/专有 namespace/进程清理.

## 公共指导的固定场景执行/回放

运行:

```bash
uv run python tests/fixtures/swt_maintenance_replay.py \
  docs/changes/swt-maintenance-improvements/evidence/public-guidance-replay.json
```

证据: [public-guidance-replay.json](evidence/public-guidance-replay.json), 包含命令摘要, 原检查时间, 分项报告与实际 HTTP/缓存操作日志.

这不是关键词扫描, 也不是自动 agent 行为测试框架. 当前会话依据公共参考选择操作, 固定夹具保存并复现给定场景. 工具链版本响应/缓存协议/批准事件是明确的模拟输入; HTTP 获取/内容核对/缓存读写清理/Git/退出码从独立资源实际执行. 不把它冒充真实 Maven 构建, 真实 Redis 或第三方账户可用性验收, 也不证明所有未来 agent 都会遵守文档.

| 用例 | 实际执行/回放与报告 |
| --- | --- |
| AC-018 | 只检查夹具 JDK 8/Maven 响应和指定 `com.example:demo-parent:1.0` 的 POM 操作, 没因无关配置探测 Redis. 请求实际从独立容器发出. 200 且内容为所需构件才通过, 401/302 后登录页均受阻, 即使凭据文件在位 |
| AC-019 | 交付引用原检查时间, 构件请求未重复; 新增上下文测试只补一次受影响服务检查, 模拟响应 503 后标受阻, 不重跑未受影响的构建检查 |
| AC-020 | 分开报告可登录/构件检查通过/上下文条件受阻/批准前写权限未检查. 独立代码阅读可继续, 未实际执行的阅读/上下文测试不报告为完成 |
| AC-021 | 批准前缓存写请求为 0. 给定同任务/资源/键/SET-GET-DEL/清理批准后同范围执行两次, 两次 DEL 后 GET 均确认不存在. 换资源/操作只提出新批准范围, 未先执行. 注入 DEL 403 后 GET 仍有残留, 明报操作成功但清理失败, 不计整项通过 |
| AC-022 | 沿临时项目字段读取临时 HOME 的已知来源, 不输出假秘密原值. 另一个相关仓库定向 rg 返回 1; 后续只提出扩围必要性与范围, 未搜索整个家目录 |
| AC-023 | 自建本地源仓与裸远端, 两次成功查询已核实分支的相同完整提交 ID 后停止, 比较过程没有 clone. 不推断其他分支/未提交文件一致 |
| AC-024 | 实际 Bash 捕获 `git ls-remote` 原码再 head: 成功为 original_rc=0/filter_rc=0, 失败为 original_rc=128/filter_rc=0, 整个命令仍返回 128 |

这里的批准事件仅是用例给定前提, 不是对任何真实共享服务的授权. 清理失败的对象仅在夹具内存中, 资源结束后整体销毁.

## 既有回归与未处理问题

用临时测试插件仅复用原 conftest 的 e2e 分类, 不载入全机清理钩子, 对以下套件跑 `-m 'not e2e'`:

- test_swt_m12.py / test_swt_llm_select_mount.py / test_swt_birth_env.py / test_swt_list.py
- test_env_docs.py / test_swt_web_access.py / test_swt_stage_env.py

结果: **112 passed, 2 failed, 53 deselected, 8 subtests passed**, 原始输出见 [legacy-regression.txt](evidence/legacy-regression.txt).
两个失败均另用 `git show HEAD:workflow/use-sandbox-worktree/scripts/swt.py` 保存的原始源码复现:

1. `TestDeliveryCallSitesUseConfirmedAddress::test_call_sites_use_confirmed_address_and_web_port`: 测试期望 5 个交付调用点, 原始源码已有 6 个.
2. `TestBirthSingleActiveContainer::test_name_writeback_single_source_before_conflict_check`: 原始源码已不存在测试要求的 `name_explicit = bool(args.name)` 文本.

原始源码复现输出见 [baseline-failures.txt](evidence/baseline-failures.txt). 这是基线失败, 本次没有放宽断言或顺手修复. 没跑全仓/旧共享网络 e2e 全量, 不声称全仓全绿. 本次更新了旧 m12 创建夹具的裸 --allow 写法以跟随新接口, 没降低原有断言.

## 范围审计

- 只改技能源仓库的相关脚本/参考/测试与本变更记录. PRODUCT/TECHNICAL 已确认用例未改写.
- 没改实际部署 skills/原业务项目/业务容器及其运行记录, 没探测共享服务, 没运行 sync-to-pi.py.
- 没改宿主/容器全局 AGENTS 或公共 run 的返回码语义, 没添加项目默认地址/服务矩阵/通用探测框架.
- 没开启新会话/子代理. 修改和规格校验不构成部署授权; 真正使用新 network 命令仍逐次预览审批.
- 测试创建的容器/本地服务/专用 DNS namespace/桥进程均按本夹具身份回收. 共享锁只协调本版本入口, 不承诺阻止同 UID 手工 nft/旧脚本绕过锁.
