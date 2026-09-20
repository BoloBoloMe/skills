# MILESTONE-16 回归耗时续压 — 收口报告 (2026-09-20)

## 干了什么

**L1: m12 并行化** (重开 M15 方向 3, 用户拍板):

- 容器名冲突: 夹具对缺 --name 的 birth 按 分支+tmpdir 后缀 自动派生; 5 处硬编码名加后缀.
- 6080 竞态 (产品已知 TOCTOU: 探针与 pasta 绑定之间) 夹具层消化:
  birth PARTIAL → rm 重建重试; resume 竞态 → 等释放 + 重开收据重试.
- 断言适配: TS201 偏好断言改采样式 (串行严格性不变), TS210 回落断言改重试构造,
  ts507 邻对存活改 podman inspect 直查.
- 产品行修复 (U-018): swt identity_probe 捕 http.client.HTTPException — 修掉
  M15 基线轮就已出现的 BadStatusLine flake 根因.
- 卫生修复 (U-020): rm 一律 -v (匿名卷泄漏曾胀满 podman 2048 锁), pkill 模式放宽
  + socat 桥同扫, conftest 会话级兜底.

**L2: 镜像构建缓存** — 实测证伪后 descope (U-021): 收尾清理只删 tag, 层缓存跨轮
存活, 暖构建 3m39s; 10min 是存储真冷时的物理成本, 非测试基建浪费.

## 证据

| 项 | 前 | 后 |
| --- | --- | --- |
| m12 串行 (关账口径) | 4m16s | 4m10s (79 全绿, 无回归) |
| m12 并行 (-n 4) | — | **~70s**, 8+ 轮全绿, 资源零泄漏 |
| m04+m07 | — | 58 全绿 (239s) |
| m09 | ~10min 冷 | 26 全绿, 暖 3m39s |

## 遗留发现 (待路由)

- swt terminate 的 `podman rm` 不带 -v — 每轮漏匿名卷 (产品侧, 测试已用 -v 兜底).
- PARTIAL 路径 (尤其 legacy 迁移竞态重试) daemon/socat 桥收割不全 — 会话级兜底
  已拦, 产品侧根治待立项.

## 触及文件

- `tests/test_swt_m12.py` (并行化主体), `tests/conftest.py` (会话兜底),
  `tests/test_swt_m04.py` / `test_swt_m09.py` (rm -v), `tests/README.md` (并行守则)
- `workflow/use-sandbox-worktree/scripts/swt.py` (U-018 一行加固 + import)
