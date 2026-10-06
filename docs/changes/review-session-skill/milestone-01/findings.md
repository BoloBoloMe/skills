# milestone-01 调查结论

## 1. 结论摘要

- pi 默认把会话保存到 `~/.pi/agent/sessions/<cwd 编码目录>/*.jsonl`.
- 目录名不是任意 slug. 源码按 `--${绝对 cwd 去掉开头的 /, 再把 /,\\,: 替换成 -}--` 生成.
- 文件名是 `<ISO 时间戳中的 : 和 . 替换为 ->_<session id>.jsonl`. 文件首行是 `type: "session"` 的 header, 含 `id`, `timestamp`, `cwd`, `version`.
- 最可靠的定位键是 `cwd + session id`, 或用户给出的会话文件完整路径. 时间戳可辅助定位, 内容关键词只适合在候选已经缩小后检索.
- 本版本的 JSONL 不使用顶层 `thinking`, `tool_use`, `tool_result` 类型. `thinking` 和 `toolCall` 是 `message.content[]` 的 block type, 工具结果是 `type: "message"` 且 `message.role: "toolResult"`. 模型切换和思考级别切换是顶层 entry.
- 30 天是任何会话文件的硬清理上限. `session-prune` 用 `fs.rm` 永久删除, 不进回收站, 不写清单日志. 找不到文件时只能报告未找到/可能已被清理, 不能伪造复盘结果.

## 2. 会话定位

### 2.1 存储路径和编码

证据:

- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/core/session-manager.js:287-300` 的 `getDefaultSessionDirPath`.
- 同文件 `:695-714` 的 `newSession`.

源码规则可还原为:

```text
safePath = -- + cwd 去掉开头的 / 后, 将 /,\\,: 替换为 - + --
sessionDir = ~/.pi/agent/sessions/safePath
sessionFile = <ISO 时间戳中 : 和 . 换成 ->_<session id>.jsonl
```

本仓库真实目录:

```text
/home/bolo/.pi/agent/sessions/--home-bolo-Workspace-review-old-sessions--/
```

实际样本文件:

```text
2026-10-06T14-12-21-560Z_01a1118e-ebb7-705a-80e8-22d98174c098.jsonl
```

文件名中的时间戳和 id 只能作为候选信息. 定位后仍要解析首行 header, 核验 `cwd` 和 `id`, 因为用户可能使用 `--session` 指定了非默认路径, 也可能存在 fork/continue 关系.

### 2.2 推荐定位顺序

1. 用户给出完整路径时直接核验文件存在, 解析首行 `session` header.
2. 用户给出会话 id 时, 先按当前仓库的 cwd 编码目录查找文件名后缀 `_id.jsonl`, 再核验 header.id.
3. 用户只给时间范围时, 在对应 cwd 编码目录按文件名和 header.timestamp 缩小候选.
4. 用户只给自然语言关键词时, 先按 cwd/时间缩小, 再对 JSONL 做关键词搜索. 不把关键词命中当成会话身份确认.
5. 所有候选最后都核对 header 的 `cwd`, `id`, `timestamp`, `version`.

一次复盘应在报告中记录: 选中的绝对文件路径, header id, header cwd, header timestamp, 文件 mtime 和定位依据. 找不到时记录搜索过的 cwd 编码目录和筛选条件.

### 2.3 实际定位命令

先列候选:

```bash
D="$HOME/.pi/agent/sessions/--home-bolo-Workspace-review-old-sessions--"
find "$D" -maxdepth 1 -type f -name '*.jsonl' -printf '%f %s bytes\n' | sort
```

用关键词只做候选筛选:

```bash
rg -n -i -e '关键词1' -e '关键词2' "$D"/*.jsonl
```

当前环境没有 `jq`, 所以实际统计使用 Node 的 JSON 解析器. 这比按字符串猜字段可靠:

```bash
node - <<'NODE'
const fs = require('fs');
const file = process.argv[2];
for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
  if (!line) continue;
  const entry = JSON.parse(line);
  // 按 entry.type / entry.message.role / content block type 处理
}
NODE
```

`rg` 适合先缩小文件和关键词范围, Node/Javascript 解析器适合做 JSONL 的结构化统计. 不建议用正则把整段 JSON 当成模型上下文.

## 3. JSONL 结构和字段含义

### 3.1 真实样本

样本:

```text
/home/bolo/.pi/agent/sessions/--home-bolo-Workspace-review-old-sessions--/2026-10-06T14-12-21-560Z_01a1118e-ebb7-705a-80e8-22d98174c098.jsonl
```

实测结果:

```text
文件大小: 479272 bytes
行数: 187
JSON 解析错误: 0
时间范围: 2026-10-06T14:12:21.560Z 到 2026-10-06T14:41:02.420Z
session: 1
message: 170
model_change: 7
thinking_level_change: 9
```

`message` 内的 role:

```text
system: 1
user: 12
assistant: 78
toolResult: 79
```

`message.content[]` block:

```text
text: 104
thinking: 72
toolCall: 79
```

这说明复盘器不能只读取 `message.content[].text`. 至少要分别处理普通文本, thinking, toolCall, 以及 `toolResult` role 的结果内容. 对工具调用的顺序, 要用 id/parentId 和文件顺序关联, 不要把同一轮的多个 block 当成独立会话.

### 3.2 顶层 entry 和实际表示

- `session`: 文件 header. 主要身份字段是 `id`, `timestamp`, `cwd`, `version`, 可能还有 parent session 信息.
- `message`: 对话消息. `message.role` 区分 system/user/assistant/toolResult 等.
- `message.content[].thinking`: assistant 的思考内容. 是否纳入最终复盘取决于用户授权和 skill 的隐私边界, 不能默认把它当用户可见答案.
- `message.content[].toolCall`: assistant 发起的工具调用, 应提取工具名和参数摘要.
- `message.role === "toolResult"`: 工具执行结果. 本样本没有顶层 `tool_result` 类型.
- `model_change`: 模型或 provider 的切换记录. 复盘 token 和行为时要按时间切分模型配置.
- `thinking_level_change`: thinking 档位变化. 同样按时间切分, 不能只看会话当前档位.
- 本样本没有顶层 `thinking`, `tool_use`, `tool_result` 类型. skill 文案应以实际 schema 为准, 不要套用其他 agent 的 JSONL 名称.

会话文件是追加写入的 JSONL, 但逻辑上是带 `id`/`parentId` 的消息树. 本样本的实测结构为 186 个非 header entry, 1 个 root, 0 个缺失 parent, 0 个分支点, 0 个压缩/分支摘要; `SessionManager.buildSessionContext()` 重建出同样 170 条消息. 因此复盘器必须说明自己读的是原始文件全量, 还是沿当前 leaf 重建的活动分支.

## 4. Token 和扫描开销

### 4.1 样本 token 使用量

从每条 message 的 provider usage 汇总得到:

```text
input:      63361, 占记录的 totalTokens 1.18%
output:     59810, 占记录的 totalTokens 1.11%
cacheRead: 5243392, 占记录的 totalTokens 97.70%
cacheWrite: 0
reasoning:  44804, 占记录的 totalTokens 0.83%
totalTokens: 5366563
```

这些是 provider usage 字段, 不是文件字节占比. `reasoning` 与 output 可能存在供应商定义上的包含关系, 不能把各百分比简单相加当成独立 token 总和. 复盘 skill 应优先报告要读的消息数量和抽取后的字符/token 开销, 不把 cacheRead 误报成新增可见内容.

按 JSONL 文件字节统计:

```text
message:             99.49%
session:               0.03%
model_change:         0.23%
thinking_level_change:  0.25%
```

字节占比显示完整 message 占绝大多数, 但不能据此跳过 model_change 和 thinking_level_change, 因为它们决定上下文中的模型和行为解释.

### 4.2 实测抽取命令和开销

对当前 cwd 会话目录执行关键词粗筛:

```bash
F="$HOME/.pi/agent/sessions/--home-bolo-Workspace-review-old-sessions--"
TIMEFORMAT='rg_elapsed=%3R sec, user=%3U sec, sys=%3S sec'
time rg -n -i -e 'session-prune' -e 'review-session-skill' -e 'milestone-01' -e 'jsonl' -e 'token' "$F"/*.jsonl >/tmp/review-session-rg.out
wc -c -l /tmp/review-session-rg.out
head -n 3 /tmp/review-session-rg.out | cut -c1-220
```

真实结果:

```text
rg_elapsed=0.004 sec, user=0.005 sec, sys=0.003 sec
255 lines, 2105842 bytes
```

这个结果说明直接把所有命中行塞回模型会明显放大上下文. 推荐流程是 `rg` 先定位文件/行, 再用 Node 解析目标文件, 只输出 header, entry type/role, tool name, 文本摘要, 时间范围和 usage 汇总.

## 5. 30 天清理上限和缺失会话

证据:

- `pi/extensions/session-prune.ts:36-40`: `EMPTY_SESSION_DAYS = 14`, `STALE_SESSION_DAYS = 30`, 根目录为 `~/.pi/agent/sessions`.
- `pi/extensions/session-prune.ts:50-58`: 任意会话文件 mtime 超过 30 天即命中规则 b.
- `pi/extensions/session-prune.ts:153-160`: 非 dry-run 直接 `fs.rm(file)`.
- `pi/extensions/session-prune.ts:202-224`: 启动时异步清理, 也提供 `/delete-old-sessions`, 默认真删, `--dry-run` 只列清单.
- `tests/pi/session-prune.test.mjs`: 当前 7 项测试全部通过, 覆盖当前会话保护, 旧空会话删除, 空目录处理和 dry-run.

清理不是只有 30 天规则. 当前实现还会处理: 超过 14 天且无 assistant 的空会话, 首行解析失败/缺 cwd 且超过 14 天, header.cwd 目录确认返回 ENOENT, 以及满足条件的空项目目录. 当前活动会话文件和目录有保护逻辑.

复盘时的如实报告规则:

- 文件不存在且目录仍存在: 报告"在指定 cwd 编码目录未找到匹配文件", 列出实际扫描路径和筛选条件.
- 文件和目录都不存在, 且没有清理日志或备份: 报告"会话当前不可用, 可能已被 session-prune 永久清理, 无法恢复和确认原文". 不要声称"已删除", 因为也可能是用户移动, 换了 agentDir, 使用了自定义 `--session` 路径或目录编码不对.
- 能看到文件 mtime 超过 30 天但仍未删除, 只说明当前清理没有覆盖它或清理未运行, 不从阈值倒推删除事实.
- `rg` 没命中关键词不等于会话不存在. 先核验 header 身份, 再说内容没有命中.
- 若用户要求的会话超过清理窗口, 只交付上述缺失事实和搜索证据, 不用相邻会话冒充目标会话.

## 6. 交付给 review-session 的直接规则

1. 先确定 cwd 编码目录和候选文件.
2. 解析 header, 用 `cwd + id + timestamp` 确认身份.
3. 按 entry type 和 message role 抽取, 识别 `thinking`/`toolCall` block 和 `toolResult` role.
4. 用 `rg` 做粗筛, 用 JSON 解析器做结构化抽取, 只把摘要和数字交给模型.
5. 报告原始文件行数/字节数, 抽取行数/字节数, 以及 token usage. 区分 cacheRead 和新生成 token.
6. 目标文件缺失时明确报告搜索边界和不确定性, 不能用关键词命中或邻近会话替代目标会话.
