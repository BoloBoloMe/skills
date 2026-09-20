# MILESTONE-15 测试基建提速 — 收口报告 (2026-09-20)

## 干了什么

1. **分层跑法落地**: pytest marker `e2e` (tests/conftest.py 按类名归层 + pytest.ini 注册),
   用法与改动面映射入 [tests/README.md](../../../tests/README.md).
   归层规则: `*E2E` 后缀 / `SwtBirthFixture` 血统 / 显式表 (m04 三个真实 netns 类,
   m12 TestTS004Containers/TestS2ContainerDirty).
2. **m12 夹具去重**: TestTS201BirthChain 的 birth 链大用例被 17 个子类意外继承重跑,
   全部改为直接继承 SwtBirthFixture; 并留注释防复发.
3. **birth 夹具合并 (方向 2) 评估后 descope**: 实测依据见 U-015.

## 证据 (实测)

| 项 | 前 | 后 |
| --- | --- | --- |
| m12 用例数 | 96 (含 17 份重复 birth 链) | 79 (断言覆盖面不变) |
| m12 全量 | 5m18s | 4m16s (-19%) |
| 快层 (全仓, -m "not e2e") | — | 109s, 344 过 (swt 核心快层秒级) |
| 全量回归 m04+m07+m09 | — | 84 过 7m57s (全绿) |

命令基线: `uv run --with pytest pytest`.

## 偏差记录

- 完成判据 "m12 减半以上" 未字面达成: 判据按 20-40min 估计校准, 实测基线 5m18s,
  去重后 -19%. 再降的两条路 (动产品内等待 / 并行) 分别越界与已被里程碑否决, 见 U-016.
- TestMultiPairIsolation 基线轮见过一次性 flake (BadStatusLine 读 ssh banner, 疑端口
  竞争), 单测重跑与后续全量均过; 已记入 tests/README.md 已知事项.
- general/present/tests/test_browser_session.py 5 个失败为改动前预存 (环境性), 非本
  里程碑范围, 见 U-017.

## 触及文件

- `tests/conftest.py` (e2e 归层), `pytest.ini` (marker 注册), `tests/README.md` (新建)
- `tests/test_swt_m12.py` (17 处继承修正 + 防复发注释)
