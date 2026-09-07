# 交接: use-sandbox-worktree MILESTONE-12 (swt 五子命令) AFK 实现收口

日期: 2026-09-07. 会话性质: probe 遍历 (AFK task, tdd-as-orchestra 编排). 当前仓库工作区干净, 全部已提交未推远端.

## 现状

- MILESTONE-12 已关闭: `swt.py` 五子命令 (birth/resume/status/terminate/switch) 全部实现, `tests/test_swt_m12.py` 84 用例全绿, m04/m07/m09 回归全绿.
- e2e-smoke.py 与 test_swt_m03.py 已按 D036 退役删除 (等价矩阵 13/13 落点核对在 ISSUE-11 文件内).
- 路线图前沿 = MILESTONE-10 (SKILL.md 定稿 + 全链演练), 全部阻塞项已清; 两块迷雾维持 (运行期新站点流程 / 修复原语留 M10 演练终审).
- 提交链: 7178095 (spec) → 01d6146 ISSUE-05 → e6a38a0 ISSUE-06 → 672ba51 ISSUE-07 → 23999be ISSUE-08 → d6d36e9 ISSUE-09 → c0b24f2 ISSUE-10 → 3b92b21 ISSUE-11 → 155c36c 路线图.
- 用户尚未追认 AFK 补钉; MILESTONE-10 尚未开工.

## 必读推荐

1. `docs/changes/use-sandbox-worktree/UNAUTHORIZED_DECISIONS.md` — U-001..013, 用户待逐条追认. 最重: U-004 (whitelist 自动放行容器→网关全端口, host 方向收敛失效); U-001 (M12 执行 spec 全系代理派生); U-005 (switch 目标不存在裁决).
2. `docs/changes/use-sandbox-worktree/EXECUTION-M12.md` + `docs/changes/use-sandbox-worktree/issues/ISSUE-05..11` — M12 执行 spec 与全部 TDD 切片, swt 行为契约的唯一完整落点.
3. `docs/changes/use-sandbox-worktree/DECISIONS.md` D025-D038 — 五子命令设计决策 (含反方修正), 实现的一切分歧以此为准.
4. `docs/changes/use-sandbox-worktree/roadmap/ROADMAP.md` — 前沿/迷雾/阻塞图; MILESTONE-10.md 是下一个任务书.
5. `workflow/use-sandbox-worktree/scripts/swt.py` (~2400 行) — 实现本体; 测试惯例与夹具形态见 tests/test_swt_m12.py 的 SwtBirthFixture.

## 会话内才有的人肉事实 (其他文档没有)

- 执行编排: 执行者 gpt-5.6-luna/high, 审核者 glm-5.3-flash/high (对抗对不同模型), 经 herdr 标签页驱动 (提交键 alt+\, enter 只换行); 每 ISSUE 独立执行者会话, 双轴评审 (spec/standards) 后接修复轮, 评审者用复核轮验证修复.
- glm-5.3-flash 稳定性实证: 一次复核轮原样重发旧报告 (未真复查), 一次模型网关 overloaded 中断; 教训 = 评审复核必须抽查代码实证, 不能全信报告文本.
- 执行者两次上下文耗尽 (85%+) 中途 aborted, 留半修复态 (22 红); 恢复法 = 唤醒消息指向 /tmp 上的持久任务文件让它自己核对续做. 教训 = 任务提示词与修复清单始终落盘, 不只存在对话里.
- git 门禁扩展在本机会拦截 `git restore` 类操作 (含总指挥会话); 恢复被误改文件的可用通路 = `git show HEAD:<path> > <path>` 重定向. 执行者跑 e2e-smoke 会重写 milestone-03-e2e-run.md 产物文件, 已明令禁止执行者跑 m03/e2e-smoke.
- 评审抓到的高危实缺 (均已修): status daemon 探测按主仓路径而非 base-path 误配; resume answered 粘性绕过 DECIDE gate; 冷启动 resume --confirm 无收据直通. 三者都有红证据测试钉住.
- swt.py 已知残留小债 (评审记录在案未修): switch()/birth() 函数过长拆分建议挂起; 指纹 network 字段占位; refs/swt-probe/mother 用后留容器内不清理.
- 测试运行命令: `uv run --with pytest pytest tests/test_swt_m12.py` (全量约 4.5 分钟, 真容器真 nft); 测试镜像 localhost/swt-m03:latest 已在本机 podman.

## 路线图 (整件事脉络)

1. 背景调研 + 路线侦查 (2026-09-01) → 选定路线 A 垂直切片先行.
2. M01/M02 盘问: gate → 母体模型 (主仓 linked worktree + 无 hooks config 收敛), D007-D013.
3. M03 瘦闭环 E2E 实跑验证集成咬合 (e2e-smoke.py).
4. M04 nft 双模式网络 / M05 podman 元数据 / M06 镜像策略+herdr 形态 d / M07 镜像制备 / M08 展示链 / M09 登录墙 — 逐层加固各自关闭.
5. M11 盘问五场景抽取 (D025-D038, caller 骨架 + 收据协议).
6. **本会话 M12**: swt 实现收口 (上文).
7. 剩余: M10 SKILL.md 定稿 + 全链真演练 (建→干→回流→拆 走真镜像真 skill) → 关闭即达目的地. 迷雾回访点都在 M10 演练. 距目的地: 一个 Milestone.
