# 文件写入检查误拦与废弃会话

## 现象

`v02-g2b` (green-evidence, 新版技能) 把多条场景命令写进一个临时 shell 脚本, 脚本里用 `2>/tmp/ev_stderr.$$` 接标准错误. pi 的 `filesystem-operation-gate` 把脚本正文里的重定向目标误判为 cwd 外写入, 列出 `/printf`, `/echo`, `/AC-001-1` 等并不存在的写入目标, 拦截了整条命令.

会话随后停在拒绝提示上, 输入不再响应; 该轮没有写出任何证据 (`git status` 为空). 这是宿主扩展的误判, 不是待测技能的行为结论.

## 处理

- 关闭该 tab, 在干净复制的同一夹具上开 `v02-g2d`, 任务里明确"所有临时文件放在证据目录内". 通过演练以 `v02-g2d` 为准.
- `v02-red4` 因启动参数把模型名打成 `deepseek-v4.1-flash-expires-on-9310`, pi 报 `model_not_found`, 该轮作废; 重开 `v02-red4b` 使用正确模型.
- 未改任何全局配置, 未放宽权限.

## 原始日志

- `drill-G2b-blocked.log`: 误拦时的屏幕与最后状态.
