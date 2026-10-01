## 父级

- `../EXECUTION.md`

## 执行

- [ ] 已实现

## 要构建什么

sync-to-pi.py 扩展登记对账: `_merge_extensions` 泛化为扫描 `<skills_dir>/*/pi-extension` 目录 (存在即候选), 对 pi settings.json 的 extensions 数组做集合对账 — 新增当前扫描集路径, 移除管理过且已消失的路径; 管理标记 sidecar `<pi_dir>/extensions.synced.json`; 手工项 (既不在 sidecar 又不在扫描集) 永不增删; 写前备份/原子. mailbox 硬编码调用点改为走泛化路径. 适合 AFK: 语义由 AC-008 三场景固定, fixture 可完全自证.

## 覆盖依据

- Product: `docs/changes/swt-list-sandbox/PRODUCT.md`, AC-008
- Technical: `docs/changes/swt-list-sandbox/TECHNICAL.md`, 模块接口 (M3), 测试接缝 (接缝 D)

## 相关决策

- `docs/changes/swt-list-sandbox/DECISIONS.md`: D001, D012

## 允许范围

- `sync-to-pi.py`: 改造 `_merge_extensions` (或以新函数替代并更新调用点), 新增 sidecar 读写.
- 扩展 `tests/test_sync_to_pi.py`.

## 禁止范围

- 修改同步计划询问/清空/模型合并等其余流程.
- 迁移或删除用户 settings.json 中的任何手工项.
- 触碰 pi 目录其他配置.

## 代码定位提示

- 现状: `_merge_extensions` (约 298 行起, 只追加, 硬编码 mailbox), 主流程调用点 (约 506 行).
- 测试现状: `tests/test_sync_to_pi.py` 既有用例形状 (tmp 目录 + settings/sidecar fixtures).

## TDD 切片

- TS-051:
  接缝: 接缝 D (tmp 目录 fixtures), `tests/test_sync_to_pi.py`.
  测试用例: TC-051.
  先写的失败测试: `test_extension_registration_reconcile` — 三用例: (a) skills 树含两个 pi-extension 目录 → sync 后 settings.extensions 含两路径且 sidecar 记录两路径; (b) sidecar 记录的路径对应目录已删 → sync 后 settings 与 sidecar 均移除该项; (c) settings 预置手工项 → sync 后原样保留且不进 sidecar. 实现前 (a) 对第二个扩展目录失败.
  最小绿色实现范围: 扫描 + 对账 + sidecar 维护 + 调用点接线.
  不得测试: 交互问答流程.
  覆盖: AC-008, BR-008.

## 验证入口

- `uv run --with pytest pytest -m "not e2e" -q tests/test_sync_to_pi.py` 全绿 (既有用例不回归).

## 风险提示

- 对账移除路径时必须同时满足 "sidecar 在册" 且 "扫描集缺席", 双条件缺一即假绿成误删.
- settings.json 解析失败的既有行为 (告警跳过) 保持.

## 停止条件

- 需要改变任一 Spec/决策/issue 边界时停止.

## 适合 AFK 的原因

纯文件系统对账, fixtures 完全覆盖三场景, 无外部依赖.

## 验收标准

- [ ] 登记新增 (多扩展目录) (TC-051a).
- [ ] 登记回收 (目录消失) (TC-051b).
- [ ] 手工项保留 (TC-051c).
- [ ] 既有 sync 用例不回归.

## 被阻塞于

- 无
