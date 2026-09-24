## 父级
- `../EXECUTION.md`, `../DECISIONS.md` D019

## 执行
- [x] 已实现

## 要构建什么
拉窗文档单源化: workflow/use-sandbox-worktree/reference/pull-window.md 中与 mailbox skill reference/pull-window.md 重叠的设备侧模板内容 (chromium --user-data-dir 强制, 音频 -R 可选与退化写法, waypipe 版本组合) 改为一句指向 mailbox skill 文档 (部署路径 ~/.agents/skills/mailbox/reference/pull-window.md); swt 独有内容 (三态选路, 容器侧编排, STATE 变量代换, 残尸纪律) 原样保留. agent-prompts 与 SKILL.md 里对 use-sandbox-worktree/reference/pull-window.md 的既有引用不失效, 不需要改它们.

## 覆盖依据
- DECISIONS.md D019 (用户批准); D011 E4/E5 (加固内容已在 mailbox 侧, ISSUE-09 落笔)

## 允许范围
- `workflow/use-sandbox-worktree/reference/pull-window.md`
- `tests/test_mailbox_pullwindow.py` (追加一条文档指针 grep 断言)

## 禁止范围
- mailbox skill 侧 pull-window.md 内容 (已是权威源, 不动)
- swt SKILL.md 与 agent-prompts (引用路径不变)
- 三态选路/容器侧编排等 swt 独有内容的实质改写

## 代码定位提示
- 先 diff 两份文档, 逐段判定: 重叠 → swt 侧改指针; swt 独有 → 保留; mailbox 独有 → 不动
- swt 文档现有读者: SKILL.md 第 82 行, agent-prompts 三母本 (读 ~/.agents/skills/use-sandbox-worktree/reference/pull-window.md)

## TDD 切片
- TS-001:
  接缝: 文档 grep.
  先写的失败测试: test_swt_pull_window_doc_points_to_mailbox — swt 侧 pull-window.md 含指向 mailbox skill 参考文档的指针且不再复述 --user-data-dir 模板细节; 现未指向, 失败.
  最小绿色实现范围: swt 文档改写 + 断言.

## 验证入口
/home/bolo/Workspace/skills/.venv/bin/python -m pytest tests/ -k "pullwindow" -q -m "not e2e" 全绿.

## 风险提示
swt 文档是 agent 实际消费面, 改写时保住它独有的操作信息, 只删重叠; 链接用部署后仍成立的相对表述 (两个 skill 目录同在 ~/.agents/skills/ 下).

## 停止条件
发现两文档重叠判定需要改 mailbox 侧内容 (即 D019 单源选择反转) 时停止.

## 验收标准
- [ ] swt 侧无重叠复述, 有有效指针
- [ ] swt 独有内容无损
- [ ] grep 测试过
