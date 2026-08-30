# present-web-server EXECUTION

拆分依据: TECHNICAL.md Seam 1-6 与 TC-001..TC-028 权威清单. 每 ISSUE 独立可提交.
执行规则: 执行者逐 TC 先红后绿, 一次一个切片; 只运行受影响测试; ISSUE 全绿后 review, 修复明确发现项, 勾选并本地提交 `feat: ISSUE-<NN>: <描述>`.

测试命令 (仓库根执行): `uv run python -m pytest general/present/tests -q`, 单文件: `uv run python -m pytest general/present/tests/test_web_server.py -q`

## ISSUE-01 CLI 骨架与参数校验 (Seam 1)

范围: 新建 `general/present/scripts/web_server.py` 骨架: `main()` 薄适配器 + `run_start/run_status/run_stop/run_add_dir` 桩 + 错误码体系 + `_sanitize_error` 脱敏 + 平台判定 (非 POSIX `not_supported`). 本 ISSUE 不实现真实服务启动, run_* 可返回 `internal_error` 桩, 仅让 TC-001..TC-004 绿.
用例: TC-001, TC-002, TC-003, TC-004.
新测试文件: `general/present/tests/test_web_server_cli.py`.
依赖: 无.
- [x] 已实现 (commit 04d359d + 8847461, 审核无阻断)

## ISSUE-02 生命周期: start/status 冷启动 (Seam 2 前半)

范围: 运行时状态簇 (server.json 读写/ping 探活/flock) + 后台化簇 (`__serve__` re-exec, Popen start_new_session, 等 ping ≤10s) + HTTP 服务簇最小闭环 (绑定端口, ping 端点, 静态内容提供, server.json/server.log 写入, 0600, log>10MB 截断) + host 探测 (D011 全优先级, 本 ISSUE 只要求输出字段存在正确). run_start/run_status 真实实现.
用例: TC-005, TC-007, TC-008, TC-009.
依赖: ISSUE-01.
- [x] 已实现 (commit f0159e9 + 63efbb8 审核修复, 审核 1 阻断 S1 已修)

## ISSUE-03 生命周期: stop/add-dir (Seam 2 后半)

范围: run_stop (ping 指纹比对 + `ps -o args=` 校验 + SIGTERM + 删 server.json), run_add_dir (校验 + POST 控制端点), 服务端 `/__control__/add-dir` 端点 (loopback-only, 锁保护 append, 幂等), 权限断言, 日志断言.
用例: TC-012, TC-013, TC-014, TC-015, TC-026.
依赖: ISSUE-02.
- [x] 已实现 (含审核建议修复 R1-R3)

## ISSUE-04 复用/冲突/host 探测 (Seam 2 扩展)

范围: run_start 复用路径 (probe 存活 + 属主/bind 校验 + add-dir 挂载 + 端口差异告警), `bind_conflict`, `instance_conflict` (属主非本人判定逻辑, 异 uid 场景仅实现代码路径, 自动化不测), host 探测完整实现 (`SSH_CONNECTION` 第 3 字段 > 默认路由接口 IP > 主机名, bind 127.0.0.1 时 `ssh -L` 指引).
用例: TC-006, TC-025, TC-027.
依赖: ISSUE-03.
- [x] 已实现 (审核 0 阻断 0 建议)

## ISSUE-05 status 重建 (Seam 2 收尾)

范围: run_status 死则重建: 按 roots 保序重 spawn, 先试原端口, 被占则 49152-65534 随机换 ≤10 次, 更新 server.json, 报告新端口 (`rebuilt` 字段).
用例: TC-010, TC-011.
依赖: ISSUE-04.
- [x] 已实现 (含审核修复 R1: 重建就绪 pid 指纹)

## ISSUE-06 内容访问 (Seam 3)

范围: 扁平并集查找 (首挂载命中), 顶层 listing 并集去重, 子目录 listing, resolve+containment 路径防护, symlink 越界 404, `../` 逃逸 404, 流式发送 (shutil.copyfileobj).
用例: TC-016, TC-017, TC-018, TC-019, TC-020, TC-021.
新测试文件: `general/present/tests/test_web_server_content.py`.
依赖: ISSUE-02 (服务可起).
- [x] 已实现 (含审核修复 R1/R2 与 U-008 语义)

## ISSUE-07 控制面安全 (Seam 4)

范围: `/__control__/*` 仅 loopback, 经本机 LAN IP 访问控制面一律拒绝, 静态内容经 LAN IP 正常; 探测不到非 loopback 接口时 skip 不 fail.
用例: TC-022, TC-023.
依赖: ISSUE-03 (add-dir 端点存在).
- [ ] 已实现

## ISSUE-08 TTL 空闲自退 (Seam 6 增补)

范围: 服务空闲 TTL 自退, 每次请求刷新计时, `PI_PRESENT_WEB_TTL_SECONDS` 注入点.
用例: TC-028.
依赖: ISSUE-02.
- [ ] 已实现

## ISSUE-09 SKILL.md 远程模式段 + 契约断言 (Seam 5)

范围: 修改 `general/present/SKILL.md` 增加远程 (ssh) 模式段 (D003/D004/D007 验收第 7 条全部条款: 远程检测 SSH_TTY/SSH_CONNECTION+用户明示覆盖, web 服务器完全替代 Chromium, 端口 49152-65534 随机选+被占重试 ≤10 依据 `port_in_use`, 成功交付可点 URL, bind 127.0.0.1 时 ssh -L 指引, 失败出口本地路径+摘要, 远程降级纯展示无 state 回读); 扩充 `general/present/tests/test_skill_contract.py` 断言.
用例: TC-024.
依赖: ISSUE-01..08 全部 (契约须与已实现行为一致).
- [ ] 已实现
