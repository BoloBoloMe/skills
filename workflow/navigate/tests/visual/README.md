# navigate 展示页巡检 (浏览器侧)

这里放的是**人肉可读的巡检脚本**, 不是 pytest: 它们要真的起展示服务 + 真的开浏览器,
检查的是"画面对不对 / 一帧多长 / 大规模行不行"这类只有跑起来才知道的事。

## 前置

- Playwright 环境 (本仓库自带的 access-web/browse 项目):
  `uv sync --project general/access-web/browse && uv run --project general/access-web/browse python -m playwright install chromium`
- 脚本自己会起/停展示服务 (用临时 runtime 目录), 不用手动开。

## 跑

```bash
# 画面与性能巡检 (约 40 秒)
uv run --project general/access-web/browse python workflow/navigate/tests/visual/render_checks.py

# 星色分布 (不需要浏览器, 从 index.html 抽出真实函数在 node 里跑)
uv run python workflow/navigate/tests/visual/star_colors.py

# 背景星闪烁 (同上, 查多频叠加/幅度分层/位置微抖/每帧 sin 预算)
uv run python workflow/navigate/tests/visual/star_flicker.py
```

`render_checks.py` 覆盖:

| 检查 | 期望 |
|---|---|
| 1440x900 帧率 | 7 个里程碑的常规视图 >= 55fps |
| 交互 | 点星球开面板 / Esc 关 / 滚轮缩放 / 拖拽平移 都生效, 无 JS 报错 |
| 动效恒开 | 即使系统省动画, 连续两帧画布也不同 (不跟随 prefers-reduced-motion) |
| 天幕不受视角影响 | 平移视角后, 纯天空区域的像素差为 0 |
| 星球光照 | 亮面朝向终点恒星 (同型同排对照: 右半比左半亮) |
| 大规模 | 1000 个里程碑: 贴图数 <= 60 张, 加载期无 >500ms 卡顿帧 |

`star_colors.py` 覆盖: 星色按黑体色温表抽取, 各档占比接近真实星空比例, 色相覆盖橙红到蓝白
且中间没有绿色 (黑体色不经过绿)。

`star_flicker.py` 覆盖: 闪烁档设计比例 60/28/12, 实际分层比例, 各档绝对 alpha 摆幅区间, 深远层比近层更弱,
主频/次频/三频/慢包络都落在设计频段 (主频 0.30~1.50Hz 等, 不是分钟级呼吸), 位置微抖只出现在明显档
且幅度按星半径缩放 (大星基准 0.12~0.40px, 小星压到亚像素), 频率 0.10~0.32Hz (慢速漂移),
每颗每帧平均 sin 次数 <= 2.2 (性能红线)。

## 注意

- 这是**软检查**: 帧率阈值给得宽 (虚拟机/无头软件渲染比真机慢), 别当硬门禁用。
- `render_checks.py` 里的像素采样点刻意选在远离地图内容 (星球/连线/未知海域的雾) 的位置,
  否则地图本身随平移移动会干扰"天幕不动"的判定。
