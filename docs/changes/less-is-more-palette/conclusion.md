# less-is-more.html 重设计: 结论记录

> 命名备注 (2026-08-23 审查修正): 文中 `adaptive-presentation` 即现行 `present` skill (提交 f22847e 改名).

## 问题

1. 例子页配色换代 (原暖纸).
2. 例子页是否真正遵循 SKILL 声称的 Saul Steinberg 式概念插画风格 — 原答案: 否 (几何太阳图标 + 机器贝塞尔, 实为东亚极简).

## 结论 (经 6 轮原型迭代定稿)

- **配色**: 米白 — paper `#faf7ef`, ink `#2e2c27`, muted `#948d7e`, line `#d6cebd`, accent `#b3562e` (accent 备正文页用, 例子里未出现).
- **构图**: 星谱 — 五线谱左端平直, 右端扬起; 音符沿途脱杆, 符→点→星芒→主星; 一个音符坠落成雨. 音符四形态: 四分/八分连音对/二分 (空心)/双音和弦.
- **文案**: EN "all those moments will be lost in time, like tears in rain" + CN "所有瞬间终将消逝于时间, 一如泪水没入雨中."
- **手法**: `feTurbulence` + `feDisplacementMap` 低频位移制造手绘抖动; 低饱和自然色; 思源宋体 + Spectral.
- **气质指引**: "哀吾生之须臾, 羡长江之无穷" — 只作构图指导, 不上页面.
- **淘汰**: 冷墨/苔绿/陶土/蜜金/藕色/深焙 (配色); 旭日/地平线, 同雨, 一滴的旅程, 名册, 溶钟, 胶片, 信, 长江, 涟漪, 星海同雨 (构图); 星谱 v2 (闭合轨道)/v3 (无轨道) 精修版.

## 落地

- 最终方案已写回 `general/present/examples/less-is-more.html`.
- 原型归档: `prototypes/palette/prototype.palette.html` (本目录下, 合并主干前清理).
