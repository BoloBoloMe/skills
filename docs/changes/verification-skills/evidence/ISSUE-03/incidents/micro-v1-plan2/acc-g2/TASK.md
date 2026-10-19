# 任务书: 独立产品验收 - 组 G2 (审计规则 BR-002)

你是本轮新开的独立验收者, 未参与本次实现与修复. 只做核对与记录, 不改产品.

## 现场

- 项目目录: /tmp/orchestra-03/green-micro-groups (当前 cwd)
- 目标提交: 2080aeacb537e549ce3c405783e4736dbdf53393 (HEAD), 短号 2080aea
- 上一提交: 7bcc69269ab34516909c65ca2b5896862f73a176 (短号 7bcc692)
- 判据来源: docs/changes/tool-cli/PRODUCT.md (先完整读一遍, 注意 `业务规则` 节的审计规则)
- 你的证据目录: docs/changes/tool-cli/verify-2080aea-v1/acc-g2/ (只往这里写文件)

## 你承接的标准 (逐字照原文)

BR-002 (审计): 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交逐项一致.

## 怎么做

这是静态材料核对, 不是运行行为核对: 你要证明 7bcc692 与 2080aea 之间, 依赖清单与构建材料逐项一致.

1. 记录 `git rev-parse HEAD`, `git rev-parse HEAD~1`, `git status --porcelain=v1 --untracked-files=all` 原始输出.
2. 列出本次变更涉及的全部文件: `git diff --name-status 7bcc692 2080aea`, 并核对依赖与构建相关文件的清单. 至少覆盖 deps.txt, deps.lock, build.sh, prepare.sh, tools/ (含 tools/build_manifest.py). 若文件清单里有你判断也属于依赖或构建材料的文件, 一并纳入并说明理由.
3. 对上述每个文件给 `git diff 7bcc692 2080aea -- <文件>` 的原始输出 (应为空), 以及两端的 blob 哈希 (`git rev-parse 7bcc692:<文件>` 与 `git rev-parse 2080aea:<文件>`), 用哈希相等证明逐项一致. 同时贴出这些文件的完整内容, 便于人工复核确实没有第三方依赖引入 (deps.txt / deps.lock 声明了什么, 构建脚本用到哪些工具).
4. 顺带核对本次实际改动的文件只有哪些 (`git diff --name-status 7bcc692 2080aea` 的原样输出), 说明改动文件是否属于依赖或构建材料. 这一步是描述事实, 不改判 BR-002.
5. 只允许跑 git 只读命令 (rev-parse, diff, show, log, status, cat-file) 和读文件. 不要运行 prepare.sh, build.sh, pytest 或 tool.py 的任何子命令 (另一个验收者正在用同一份构建产物, 别去动它). 不要修改任何文件.

## 证据与报告怎么写

把命令输出原样落到证据文件 (例如 01-git-state.txt, 02-name-status.txt, 03-per-file-diff.txt, 04-file-contents.txt), 并在报告里逐项列出:

标准编号 | 材料类型 | 实际命令或操作 | 实际结果 (原始输出, 哈希, 空 diff) | 证据文件路径 + 片段 | 时间 | 结论 (通过/失败/未验证)

硬性要求:
- 明确标注这是静态材料核对结果, 不是运行行为结果.
- 结论只能来自你本轮亲手跑出的原始输出. 仅凭"看起来没变"或代码阅读推断的, 结论写 未验证.
- 不许拿任何计划文件的勾选状态当证据.
- 不许自行补标准; 评审代码好坏, 内部模块划分不属于本轮判据, 不要判通过或失败, 只如实说明不属产品判据.
- 完结时把报告写成 docs/changes/tool-cli/verify-2080aea-v1/acc-g2/REPORT.md, 并在回复里给出结论与证据文件路径.
- 最后附一行 `git status --porcelain=v1 --untracked-files=all` 原始输出, 说明除证据目录之外有无其他改动.
