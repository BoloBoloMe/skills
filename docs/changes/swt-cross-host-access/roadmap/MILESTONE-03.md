# 状态: 已关闭
# 类型: task
# 阻塞于: 无 (MILESTONE-02 已关闭)

## 问题

信箱通道实施 (AFK 编码, 形态按 M01 账本): `swt-base-server.py` 单体 (吸收 llm-proxy + 信箱: 端口区间绑定/身份探测/双向签名+防重放/设备路由/指令白名单/7 天清理, D001-D010) + 设备侧 pi 扩展 + 阻塞取信脚本 + swt.py birth 集成 (--allow 宿主网关 + 注入容器 key/服务地址) + e2e 测试 + skill 文档. 按 M01 盘问结论与 M02 原型经验落地.

## 结论 (2026-09-14, tdd-as-orchestra AFK 8 ISSUE 全收口)

- 产物: `workflow/use-sandbox-worktree/scripts/swt-base-server.py` (信箱+中转单体, stdlib 零依赖, 192 pytest 绿) + `pi/extensions/swt-mailbox-relay.ts` + `swt-mailbox-fetch.mjs` (21 node:test 绿) + swt.py birth 自动接线 + `tests/test_swt_base_server*.py`/`test_swt_birth_mailbox.py` + SKILL.md 基础服务章节 + `swt-base-server.service` 驻留件.
- 测试: 213 项全绿 (192 pytest + 21 node:test); e2e 门禁 `tests/test_swt_base_server.py` 覆盖 D010 全清单 (投信/阻塞取信/双向签名验签/防重放/按设备路由/白名单降级/7 天清理/端口区间+身份探测).
- 关键演进 (评审驱动, 详见 [UNAUTHORIZED_DECISIONS](../milestone-03/UNAUTHORIZED_DECISIONS.md) UD-01..UD-14): post 响应签名用投信容器 key 可验 (UD-06); 响应签名密钥每设备一份 (UD-08); 补 /mailbox/ack 闭环 D004 存续 (UD-09); 取信脚本 Node 化 (UD-10); 缺省路由也过目标作用域 (UD-05); 驻留件 systemd user unit (UD-14, 待用户确认).
- 移交 M08: admin `POST /admin/whitelist` 注册指令集成员 (当前空集, waypipe 拉起命令待 M06/M08 定形后填, UD-03); 容器内投信 env 已由 birth 注入 (SWT_BASE_URL/SWT_MAILBOX_KEY/SWT_CONTAINER_NAME).
- 未验证边界: 真机部署 (Quadlet→service 驻留/真 birth/真设备取信) 归 M09; resume/switch/terminate 信箱联动未做 (缺口记录在 EXECUTION).
