---
name: ponytail-help
description: >
  当我说 "ponytail help" 或 /ponytail-help 时使用.
  所有 mode, skill 和命令的快速参考卡. 一次性展示.
---

# Ponytail Help

调用时展示此参考卡. 一次性, 不要切换 mode, 不要写 flag 文件, 不要持久化任何东西.

## Levels

| Level | Trigger | 变化 |
|-------|---------|------|
| **Lite** | `/ponytail lite` | 按请求构建, 一行指出更懒的替代方案. |
| **Full** | `/ponytail` | 阶梯强制执行: YAGNI → stdlib → native → one line → minimum. 默认. |
| **Ultra** | `/ponytail ultra` | YAGNI 极端主义者. 删除优先于添加. 构建前先质疑需求. |

Level 持续生效直到更改或 session 结束.

## Skills

| Skill | Trigger | 作用 |
|-------|---------|------|
| **ponytail** | `/ponytail` | 懒模式本身. 最简可行方案. |
| **ponytail-review** | `/ponytail-review` | 过工程审查: `L42: yagni: factory, one product. Inline.` |
| **ponytail-audit** | `/ponytail-audit` | 全仓库过工程审计, 按砍掉行数排序. |
| **ponytail-debt** | `/ponytail-debt` | 收集所有 `ponytail:` 注释到账本. |
| **ponytail-gain** | `/ponytail-gain` | 实测影响记分牌: 更少代码, 更少成本, 更快速度. |
| **ponytail-help** | `/ponytail-help` | 本卡片. |

## Deactivate

"stop ponytail" 或 "normal mode" 关闭. 随时用 `/ponytail` 恢复. `/ponytail off` 也可以.

## Configure Default Mode

默认 mode = `full`, 每个 session 自动激活. 修改方式:

**环境变量** (最高优先级):
```bash
export PONYTAIL_DEFAULT_MODE=ultra
```

**配置文件** (`~/.config/ponytail/config.json`, Windows: `%APPDATA%\ponytail\config.json`):
```json
{ "defaultMode": "lite" }
```

设为 `"off"` 禁止 session 启动时自动激活, 需要时用 `/ponytail` 手动激活.

解析顺序: env var > config file > `full`.


