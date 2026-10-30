# milestone-05 流中断工具派发补核

任务 `workflow-stack-review/milestone-05-review`, 独立会话/信箱 `01a18c58-8d8c-7542-b650-365bc3d03d8a`. 本轮只补 `REVIEW-02.md` 留下的一条派发状态疑点, 不改判据, 不覆盖旧报告.
目标仍为 `6d0c4b25b4b8e84bd45c43549d442dd8cfb29395`, 基线/标准仍为 `57e93dce741f343ec45b567b8eec6ba6a1e684c9` 的 ACCEPTANCE.md, AC-05-01 至 AC-05-07.
本轮起始 HEAD 为 `541c6ef081e6d92720a265772c08bc0c3ee89e4a`, 补查时间为 `2026-10-30T11:04:37Z` 至 `11:11:19Z`, 仅作只读补证.

## 不变观察的引用

- 首轮原件: `c8a2f9a2ef5ec1bcf67e6f822e454c203e09b92c:docs/changes/workflow-stack-review/milestone-05/REVIEW.md`.
- 返修复核原件: `541c6ef081e6d92720a265772c08bc0c3ee89e4a:docs/changes/workflow-stack-review/milestone-05/REVIEW-02.md`.
- 2026-10-30T11:08:59Z 再比新目标与当前五个被核文件及 SAFETY.md, verification-contract/SKILL.md, check_skill.py, ACCEPTANCE.md, `git diff --exit-code` 实际退出码 0. 两份旧报告各与上述报告提交比较也均退出码 0.
- 沿用第二轮 AC-05-01 至 AC-05-06 的结果与 `2026-10-30T10:54:32Z` 三次校验原件, 各退出码 0. 输入/校验器未变, 本轮没有重跑或把旧结果冒充新结果.

## 日志直接观察

原件为 `/home/bolo/.pi/agent/sessions/--home-bolo--/2026-10-30T07-30-44-526Z_01a18bb7-daad-71ad-b7ab-ba6b1373fc72.jsonl:110`. 2026-10-30T11:11:19Z 再次只抽取该条元数据与工具 id:

```text
record_id=3052970e
timestamp=2026-10-30T10:46:40.208Z
role=assistant
stopReason=error
errorMessage=stream error: stream disconnected before completion: stream closed before response.completed
name=codemode
id=call_QxPYS2ZJl0xxN0N7OtufMrMj|fc_09f248a61447fd21016ae47448f74887d092f02705c195e66c
```

按该 id 在完整现有原件中匹配 `role=toolResult` 和 `toolCallId`, 结果仍为零条. 这是日志事实, 本身既不证明成功执行, 也不单独证明未派发. 没有运行截断代码或重发旧命令.

## 实际运行入口与所查版本

不是只读一份同名的未打包源码就假定它在运行. 本轮只读核对了以下入口链:

```text
/usr/local/bin/pi
-> /opt/swt-agent-config/launch.py
-> /opt/swt-agent-config/agent_config/launch.py:28,35, runtime.py:21
-> /opt/swt-agent-bin/pi
-> /usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js
-> dist/bundle/cli-runtime.js:3
-> dist/bundle/chunks/chunk-TJXZSVTD.js
```

`/usr/local/bin/pi` 实际通过 uv 启动固定 launch.py; launch 的 main 按 REAL_BIN_DIR 选 pi 并 execve. `/opt/swt-agent-bin/pi` 的实际符号链接抵达上述 bundle/cli.js, 后者加载 cli-runtime.js; cli-runtime.js 实际从上述 chunk 导入 main. 这里是入口读取记录, 不是本轮重新执行这串启动命令.
原日志 `:82` 的工具返回中, mailbox 状态把会话 `01a18bb7-daad-71ad-b7ab-ba6b1373fc72` 对应到容器 pi 进程 `21151`. 当前 `/proc/21151/exe` 为 `/usr/local/bin/node`, 父进程 `21146` 为 uv, 其 cmdline 仍含 `/opt/swt-agent-config/launch.py` 和 `pi`. 从 /proc 的启动计数换算, 父进程启动约为 `2026-10-30T07:30:43.35Z`, 早于该错误. 该 pi 进程的 NODE_OPTIONS 非空值检测为 false. 这些是入口绑定依据, 不是仅采信协调方对源码的说明.

当前安装包 `@earendil-works/pi-coding-agent` 与其依赖 `@earendil-works/pi-agent-core` 的 package.json 均为 `1.2.0`. 具体文件指纹如下, 不把版本号当成所有构建内容恒同的保证:

| 文件 | 位置与 SHA-256 |
| --- | --- |
| 实际入口导入的 `dist/bundle/chunks/chunk-TJXZSVTD.js` | 第 550 行, `3aced1320c6c7a36ff53be75b539099310971e9b54b15df5b1efba3d2be75c10` |
| 可读对照 `node_modules/@earendil-works/pi-agent-core/dist/agent-loop.js` | 第 141-165 行, `4d56e5352826e0dbe324eedd2b632d19867aff8844d1f010b3cdcd34069da7fb` |

两条路径均相对 `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/`. 两文件当前均为 root 所有, mode 0644, mtime 为 `2026-10-14T10:10:28Z`, ctime 也在当日, 早于该运行进程启动. 本轮未修改安装源码/配置.

## 源码判断, 与工具执行观察分开

独立读取 agent-loop.js 全文并核对实际 bundle 中的同一段控制流:

- 可读源码 `:141` 等待 streamAssistantResponse 完成; `:143-154` 在 stopReason 为 error/aborted 时设置空 toolResults, 调用完成回调并发出 turn_end/agent_end, 随即 return.
- 只有越过该返回分支才在 `:156` 收集 toolCall, 并在 `:165` 到达 executeToolCalls.
- 实际 bundle 的 `chunk-TJXZSVTD.js:550` 也逐项保留上述顺序: error/aborted 条件, 空 toolResults, 事件, return, 然后才过滤 toolCall 和执行工具. 不是把未打包源码的结论直接套给另一个构建.

因此, 按已绑定入口和所查源码控制流, 第 110 行的 error 响应没有由正常模型工具调度派发其中的 codemode. 这属于源码判断, 不是一条工具成功/失败的实跑结果. JSONL 留有部分 toolCall 参数并不意味着已派发; 在这一分支没有对应 toolResult 是符合调度逻辑的结果, 不需要补造一个执行结果.

## 补核结论与边界

第二轮留出的这条疑点现已获得入口/源码补证, 按所查调度路径判断未派发, 不再保留该路径下是否派发的未知状态. 旧报告当时保留疑点的观察仍原样保留, 本报告只追加后续证据.
结合 `REVIEW-02.md` 对其余实际调用/结果的核对, AC-05-07 在指定两会话, 指定时段及可见操作范围内满足. 这不是豁免, 不是声称这条 codemode 成功执行, 也不是对其他进程或整个系统历史的全面证明.
尚未验证的范围保持不变: LLM 实际遵从率, 安装/同步效果, 产品行为与正式终点验收. 本轮没有取进程内存或历史安装快照, 也未审计任意扩展/其他进程的独立副作用; 未派发判断限上述已核入口/构建的调度路径, 不外推为全局运行行为实测.
本轮只新增本报告, 不重跑截断调用, 不改标准/被核文件/旧报告/ROADMAP 数据, 不同步或新增测试脚本. 不关闭 milestone-08, 不宣称正式验收通过.
