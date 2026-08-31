# 交接: present-web-server 全部 9 ISSUE 完成, 待用户确认 AFK 决定

日期: 2026-08-30 (ISSUE-03..09 会话)
工作区: /home/bolo/Workspace/skills (注意: 旧 handoff 的 /var/mnt/DATA/... 路径已不存在)
模式: tdd-as-orchestra AFK; 执行者 ai-work-zai/glm-5.3-flash (用户中途指定, 之前 glm-5.3), 审核者 ai-work-zai/glm-5.3

## 结果

- ISSUE 9/9, TC 28/28 自动化全绿 (TC-029 人工, 规格如此).
- 最终全量: `~/.local/bin/uv run --with pytest --with playwright python -m pytest general/present/tests -q` → 106 passed, 1 skipped, 0 failed (用户裁决 A 后命令含 playwright, browser_session 62/62 绿; skip 为 browser integration 需 PRESENT_REAL_BROWSER).
- web_server 用例 41: cli 6 / lifecycle 19 / content 9 / control_plane 7; skill 契约 3 (含新增远程段断言).
- 提交: 54d143f (I03) / e344d3d (I04) / ffe6d0c (I05) / e795750 (I06) / aa9a693 (I07) / 4541ae9 (I08) / ea2f242 (I09) + U-004..U-010 决定记录 5 个 doc 提交. 未推送.

## 待用户确认的 AFK 决定 (docs/changes/present-web-server/UNAUTHORIZED_DECISIONS.md)

- 上会话: U-001 自建 EXECUTION / U-002 测试命令 / U-003 调度粒度.
- 本会话: U-004 测试命令适配本机 (已修订含 playwright) / U-005 browser_session 环境差异认定 (已撤销, 见修订记录) / U-006 子代理模型选型 (后被用户改为 flash 执行+glm-5.3 审核) / U-007 add-dir 端点回写 server.json roots (审核 S1, 消除 D005 矛盾) / U-008 不可读挂载 listing 语义 (全不可读 404, 部分 200 子集) / U-009 控制面放行 loopback 或源==bind (修 B1 回归: bind 具体 IP 时 CLI 自身 ping 被 403) / U-010 /__control__/* loopback 下不回落静态 (遮蔽兑现).

## 本会话异常 (均已处理)

- sed 勾选误伤全文件 + python 修复时引入 NUL 字节 → 从 54d143f 恢复重做, amend 无痕 (教训: 勾选一律 python 行级编辑).
- 执行者超时 2 次 (ISSUE-06/07 修复轮, flash xhigh 验收循环过长): 工作已落盘, 我核验 (定向+全量 5 连跑绿, diff 审读) 后代为收尾提交.
- cli 用例 _assert_no_serve_children 全局 pgrep 误伤孤儿 __serve__ 进程 (三次烧掉执行者时间) → aa9a693 收敛为只匹配本测试 tmpdir.
- ISSUE-07 审核抓到 1 阻断 B1 (见 U-009), 其余 ISSUE 审核 0 阻断; 建议级共采纳 6 项 (S1×3 场景/S2/S3/B1) 全部修复.

## 遗留

- TECHNICAL.md 数据模型 "写入方" 措辞未随 U-007 扩展 (执行中不动权威文档); 需要时补一句.
- SKILL.md 交付 url 是入口 URL (目录 listing 起步), 非文件直链 — 合规 (D011 "完整入口 URL"), 可用性细节留观察.
- sync-to-pi.py 不执行 (用户裁决 2026-08-30); 后续需要时由用户发起.
