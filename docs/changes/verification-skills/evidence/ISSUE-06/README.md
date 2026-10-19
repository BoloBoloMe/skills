# ISSUE-06 证据索引

本目录是 ISSUE-06 `benchmark-checklist` 测量基础切片的原始材料. 三份切片记录在 `TS-001.md`, `TS-002.md`, `TS-003.md`; 会话原始输出在 `sessions/`; 演练用的受控测量脚本在 `fixtures/`; 交付报告在 `HANDOFF.md`.

## 环境与加载方式

- 宿主: Ubuntu 26.04 LTS, 16 核 (`nproc`=16).
- Herdr 0.9.4, pi 1.3.0.
- 演练模型: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 启动参数 `pi --model ... --thinking high -a` (一次性项目信任, 未改任何全局配置).
- 加载方式: 把待测技能源目录复制到临时项目的 `.agents/skills/benchmark-checklist/`, 在项目 cwd 用 `/skill:benchmark-checklist <任务>` 点名加载; 会话启动横幅的 `[Skills]` 行出现 `benchmark-checklist`, 证明加载来源是临时项目而不是全局部署.
- 待测源文件: `workflow/benchmark-checklist/SKILL.md` (工作树 ISSUE-06 分支). 三个版本分别复制到临时项目并提交:
  - v1 (只含测量前主张与工具检查): 临时项目提交 `48d5ee1`.
  - v2 (加公平调优与重复统计): `52229c9`.
  - v3 (加错误计数, 工作发生与判定): `a018313`, 与仓库交付内容一致.

## 临时项目

- 路径: `/tmp/orchestra-06/`.
- 起始提交: `48cec44` (`lab: export 演练项目初始提交`), 之后 `f55074f`, `2b7f6dd` 为夹具修正与运行方式说明, 演练开始时的干净基线是 `2b7f6dd`.
- 内容: 用 sleep 与 CPU 空转模拟新旧两版导出的受控材料; `src/` 与 `vendor/` 演练期间只读, `bench/` 为授权可改的实验脚本. 脚本原始内容见 `fixtures/`, 与会话期间工作树逐字节一致.
- 这些数字只是方法演练, 不代表任何真实产品性能.
- 演练会话自己新增的脚本与记录 (例如 `bench/verify_ab.py`, `docs/export_compare.md`) 原样留在 `sessions/attachments-round*`, 未被当成夹具.

## 上游源文获取 (只读)

- 地址: `https://raw.githubusercontent.com/cursor/plugins/4382e687a50b8d2c5ce4d141d001186589cff8d5/pstack/skills/benchmark-checklist/SKILL.md`.
- 命令: `curl -sS -m 20 -o /tmp/pstack-bench.md -w "%{http_code}" <地址>`; 结果 HTTP 200, 5002 字节, `sha256=ba109e96c8f6c1c391baccf19e5d11e14370df7b3f2605e1572cd565a6c0fca0`.
- 同 SHA 的 `pstack/LICENSE` 也是 HTTP 200.
- 只读获取, 未执行原版技能任务. 本次写入范围按 DECISIONS F014 记录的借用项取舍, 未复制源文正文; 随附完整 MIT 许可文本与逐项差异记录由 ISSUE-13 统一补齐.

## 借用范围 (对应 F014 与本 ISSUE 的 AC)

- 借 "运行前先写准备对外给出的结论, 读脚本看计时/计数/忽略什么, 查负载与核心数": 覆盖 AC-025.
- 借 "分析器单独运行且那次的数字不作报告": 覆盖 AC-025 的 TS-001 范围.
- 借 "每侧按生产方式调优, 单侧默认是在比配置, 无法调优不得选赢家": 覆盖 AC-026.
- 借 "每边至少 5 次交替, 报中位数与极差, 差距小于波动为无可测差异, 接近时用秩和检验": 覆盖 AC-026.
- 借 "计失败与非成功响应并核对输出正确性, 证明工作在计时区发生且结果被使用": 覆盖 AC-027.
- 未借: PR 主数字限制 (AC-029), 粗估单次例外 (AC-028), 收益上限与端到端占比 (AC-030), 基线与脚本固定前检查 (AC-031), 提交/发布/自动合并流程. 这些属于其他 ISSUE 的范围.
