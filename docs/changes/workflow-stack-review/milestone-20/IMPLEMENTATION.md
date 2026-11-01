# milestone-20: mailbox 信头时间加 MAILBOX_TZ 覆盖

任务标识 NAV-20, 分支 m20-mailbox-tz (起点 50eb649), 类型 task.
范围: general/mailbox 信头 发送时间 的呈现时区可由 `MAILBOX_TZ` 覆盖;
不硬编码 +08, 不改系统时区, 不加依赖.

## 实现

- `general/mailbox/scripts/mailbox.py`
  - 新增 `_parse_mailbox_tz(raw)`: 先按偏移写法 `+HH:MM` / `+HHMM` /
    `+HH` 自己解析 (正负均可, 限 ±24h 内, 便于无 tzdata 环境),
    再回退 `zoneinfo.ZoneInfo` 解析 IANA 名; 都不行返回 None. 只用标准库.
  - 新增 `resolve_mailbox_tz()`: 读 `MAILBOX_TZ`, 未设/空返回 None
    (= `astimezone()` 系统本地时区, 与改动前行为一致); 同一值解析结果
    按值缓存; 非法值回退系统本地时区并向 stderr 提示一次
    (`MAILBOX_TZ 值无效, 信头时间回退系统本地时区: <值>`), 不让取信失败.
  - `print_letter` 的 发送时间: `astimezone(resolve_mailbox_tz())`.
    只改这一处呈现. `log_event` 的 UTC 加 Z 与 presence 的 age_text
    相对时间均未动.
  - 模块 docstring 的 env 清单补 `MAILBOX_TZ` 条目.
- `general/mailbox/SKILL.md` (第 32 行那句): 补 MAILBOX_TZ 覆盖说明
  (IANA 名或偏移, 未设或非法时按系统本地时区, 事件日志仍为 UTC),
  措辞风格与原文一致.
- `tests/test_mailbox_prompts.py`: 新增 3 组用例 (6 例), 见下.

## 已实测通过

命令 (容器内, PATH 前置了 `/tmp/navigate-milestone-20/bin` 的空 podman
shim 以绕过 conftest 会话钩子对 podman 的硬依赖; 容器无 podman):

```
PATH=/tmp/navigate-milestone-20/bin:$PATH NAVIGATE_WEB_RUNTIME_DIR=/tmp/navigate-milestone-20 \
  uv run python -m pytest tests -k mailbox -m "not e2e" -q
```

输出摘要: `1 failed, 201 passed, 521 deselected in 165.53s`.
唯一失败 `tests/test_mailbox_listen_mark.py::test_mailbox_listen_tool_schema_smoke`
为环境问题 (node 脚本报 "无法从 pi shim 解析 cmd-shim-target"),
已用 `git stash` 在基线 50eb649 复跑确认同样失败, 与本次改动无关.

```
PATH=... NAVIGATE_WEB_RUNTIME_DIR=/tmp/navigate-milestone-20 \
  uv run python -m pytest tests/test_mailbox_prompts.py -m "not e2e" -q
```

输出摘要: `24 passed`.

手动渲染 (脚本 /tmp/navigate-milestone-20/render_letter.py, 信件
ts=1784442605.987654, UTC 时间 2026-07-19 06:30:05):

- `MAILBOX_TZ=Asia/Shanghai uv run python /tmp/navigate-milestone-20/render_letter.py`
  → `发送时间: 2026-07-19 14:30:05 +08:00` (UTC+8)
- `MAILBOX_TZ=+08:00 ...` → 同上 `+08:00`
- 未设 MAILBOX_TZ (TZ=CST-8) → `2026-07-19 14:30:05 +08:00`
  (跟随系统本地时区, 与改动前一致)
- `TZ=CST-8 MAILBOX_TZ=Mars/Olympus ...` → 照常输出信头
  `2026-07-19 14:30:05 +08:00`, stderr 出现一次
  `MAILBOX_TZ 值无效, 信头时间回退系统本地时区: Mars/Olympus`, 退出码 0

## 测试覆盖 (tests/test_mailbox_prompts.py)

- `test_sent_time_unset_mailbox_tz_keeps_local_behavior`: 未设 MAILBOX_TZ
  时跟随 TZ 注入的系统本地时区, 与改动前一致.
- `test_sent_time_mailbox_tz_override_is_utc_plus_8`: 参数化
  `Asia/Shanghai` 与 `+08:00`, 断言信头偏移为 `+08:00` 且小时数与 UTC
  差 8; 只比较偏移与差值, 不锁死具体日期. tzdata 缺失时 skip IANA 例.
- `test_sent_time_invalid_mailbox_tz_falls_back_without_failure`:
  非法值不失败, 回退系统本地时区, stderr 同值只提示一次.

## 未验证

- 无 tzdata 环境 (如精简容器) 下的 IANA 用例: 本容器 tzdata 在场,
  skipif 分支未实际走过; 偏移写法路径不受影响.
- pi 扩展/守护实际取信路径只验证了 `print_letter` 单元与脚本级渲染,
  未走真实 serve+send 全链路 (受本次范围与环境限制).

## 证据缺口

- `test_mailbox_listen_tool_schema_smoke` 的环境失败未修复 (基线即失败,
  非 m20 引入), 修复超出本里程碑范围, 待环境/上游处理.
