# ISSUE-08 证据索引

本目录是 ISSUE-08 `benchmark-checklist` 收益上限, 端到端, 基线与脚本固定, 一次性实验边界切片的原始材料.

三份切片记录: `TS-001.md` (AC-030), `TS-002.md` (AC-031), `TS-003.md` (AC-024). 交付报告: `HANDOFF.md`. 机械检查日志: `machine-checks.log`.

## 环境

- 宿主: Ubuntu 26.04.1 LTS, 内核 7.0.0-31-generic, 16 核 (`nproc`).
- herdr 0.9.4, pi 1.3.0.
- 演练模型: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 启动参数: `pi --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`; `-a` 只做本次项目信任, 未改任何全局配置.
- 加载方式: 把待测技能源目录复制到临时项目 `.agents/skills/benchmark-checklist/`, 在该项目 cwd 开新会话, 用 `/skill:benchmark-checklist <任务>` 点名加载. 会话启动横幅 `[Skills]` 列出 `benchmark-checklist`.
- 来源核对: 演练期间 `find /home/bolo/.agents /home/bolo/.pi /tmp/orchestra-08 -maxdepth 6 -type d -name benchmark-checklist` 只命中临时项目里的那一份, 全局 `~/.agents/skills/` 没有同名技能, 所以加载来源是临时项目里的待测副本, 不是全局部署.

## 待测源与版本

待测源文件: `workflow/benchmark-checklist/SKILL.md`.

| 版本 | 仓库提交 | 内容 |
| --- | --- | --- |
| v0 | `47ca0bf` (开工基线) | ISSUE-06 合并后的现有文本, 无本 ISSUE 三节 |
| v1 | `6dbdd11` | 加 "收益上限与端到端" |
| v2 | `590f9cd` | 再加 "基线与脚本固定前" |
| v3 | `2828254` | 再加 "一次性实验的边界" (交付版) |

## 临时项目

- 路径: `/tmp/orchestra-08/lab`, 练完抄完证据后已删除.
- 提交序列: `a36278b` (初始材料 + 技能 v0) -> `2f89d4a` (v1) -> `86d5a0d` (v2) -> `28adf14` (v3).
- 内容: `src/` 冻结产品源码 (报表导出流水线, 权限判定, 请求流程, 老同步入口), `bench/` 授权的独立实验脚本, `docs/` 记录与旧基线.
- 数字性质: 用 `time.sleep` 与 CPU 忙等模拟的受控材料, 只证明方法, 不代表任何真实产品性能.
- 重建方式: 各脚本全文都在本目录 (`red-round/bench-diff/`, `green-ts001/bench/`, `green-ts002/bench/`, `green-ts003/bench/`), 按 README 布局放回即可复现.
- v3 轮的材料里残留了上一轮 `docs/green2.md` (未删), 已在 TS-003 缺口里注明; 它与 AC-024 场景无关.

## 会话

| 会话名 | 技能版本 | 任务 | 原始转录 |
| --- | --- | --- | --- |
| `bm-red` | v0 | 红轮任务 1-3 (收益结论, 40% 复核, 脚本固定, 基线) | `red-round/sessions/bm-red.jsonl` |
| `bm-red` | v0 | 红轮任务 4-7 (分析器, 限流对比, 压测平台, 降级路径) | 同上 |
| `bm-red2` | v0 | 红轮任务 5 (只从微基准算收益上限) | `red-round/sessions/bm-red2.jsonl` |
| `bm-g1` | v1 | 绿轮 AC-030 六个场景 | `green-ts001/sessions/bm-g1.jsonl` |
| `bm-g2` | v2 | 绿轮 AC-031 三个场景 | `green-ts002/sessions/bm-g2.jsonl` |
| `bm-g3` | v3 | 绿轮 AC-024 四个场景 | `green-ts003/sessions/bm-g3.jsonl` |

- 提交渠道: `herdr pane send-text <pane> '<任务>'` + `herdr agent send-keys <名> "alt+\\"`; 状态用 `herdr agent get <名>` 与 `herdr agent read <名>` 核对.
- 收尾: 六个演练会话所在的 tab 全部关闭, 关闭后 `herdr agent list` 里只剩编排者和其他执行者的会话.

## 上游来源 (只读)

- 地址: `https://raw.githubusercontent.com/cursor/plugins/4382e687a50b8d2c5ce4d141d001186589cff8d5/pstack/skills/benchmark-checklist/SKILL.md`.
- 命令: `curl -sS -m 20 -o /tmp/pstack-bench-issue08.md -w "http=%{http_code}\n" <地址>`; 结果 HTTP 200, 5002 字节, `sha256=ba109e96c8f6c1c391baccf19e5d11e14370df7b3f2605e1572cd565a6c0fca0`, 与 ISSUE-06 记录一致.
- 只读获取, 未执行原版技能任务, 未复制源文正文.

## 借用范围 (对应 F013 / F014 与本 ISSUE 的 AC)

- 借上游第 3 问 "算物理上限, 删除占 10% 的段最多快约 11%, 超过上限说明测到了缓存, 空操作或 bug": 覆盖 AC-030-1, AC-030-2.
- 借上游第 6 问 "微结果旁测用户端到端路径, 真实数据规模与并发, 报微优化占比": 覆盖 AC-030-3.
- 借上游第 1 问 "分析器在不上报的运行里用, 找限制因素, 数字没变先找限制因素, 留意负载生成器先饱和": 覆盖 AC-030-4, AC-030-5, AC-030-6.
- 借 "Other perf material" 两条接入要求 (规划前审基线; 固定 harness 前审并让它输出错误数与工作量): 覆盖 AC-031-1, AC-031-2, AC-031-3.
- 一次性实验边界按 D034 与 AC-024 写成本仓库规则, 不是上游条目; 影响调查类脚本的边界指向 `workflow/blast-radius/SKILL.md`, 不重复实现那套方法.
- 未借: 粗估单次例外与 PR 主数字 (属 ISSUE-09), 提交/发布/自动合并流程.
- 许可: 完整 MIT 版权与许可文本按 ISSUE-13 统一补齐; 补齐前该副本不对外发布.
