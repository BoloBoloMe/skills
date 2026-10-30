# milestone-02 实施与自检记录

状态: 仓库文档实施和作者自检完成, 独立复核未进行. milestone-02 保持进行中, 本记录不构成独立复核或终点验收通过.
实施提交: `dcf06358c9a9ecff600228fa5eb300a65deec46e`.
前置修正提交: `3cd5ee3`, 直接删除 domain-awareness 的两处旧词汇要求.
整体复核范围: `8b39649715f1aa4930e69004b0d9c706e08b7553..dcf06358c9a9ecff600228fa5eb300a65deec46e`.
标准: 根目录 `ACCEPTANCE.md` 的 AC-02-01 至 AC-02-08. 我在本轮对 wtf 重新列明的其余六项回复 "确认" 后, 标准已先于本次主体实施落盘.

## 实际修改

| 文件 | 结果 |
| --- | --- |
| workflow/software-engineering-consensus/SKILL.md | 新建参考型 skill, description 为 `涉及软件工程时调用.`, 省略 disable-model-invocation, 正文全部内联. 写入 MVP/PoC/demo/迭代的交付与验证边界, 两条旧定义及避免项, 本仓库适用范围和 D013 的两类收录规则. |
| workflow/domain-awareness/SKILL.md | 前置提交已直接删除旧词汇读取要求和恒定引用, 不加新 skill 指针. |
| workflow/domain-awareness/WORKFLOW_VOCABULARY.md | 定义迁入后删除. 旧版本仍可从 git 历史追溯. |
| README.md | 工作流技能表增加新 skill 入口. |
| workflow/maintain-verification-skill/SKILL.md | 两处 "失败迭代" 改为 "失败尝试", 保留原数据留存和复跑要求. |
| workflow/maintain-verification-skill/reference/drift-classification.md | 混淆样例的 "失败迭代" 改为 "失败尝试", 其余处理和证据要求不变. |

正文不另写首次读取, 相同正文复用或更新后重读规则. 本次未变更 PUBLIC, 其他历史记录或技术意义的迭代用语.

## 作者实际检查

时间: 2026-10-30 UTC, 14:07:55 前完成. 以下均为本次作者的实际终端结果, 不是独立检查结论.
执行目录: 仓库根目录. 下列 `<repo>` 在本次执行中为 `/home/bolo/Workspace/refactor-skill-around-verification`.

| 命令 | 实际输出 | 退出码 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py <repo>/workflow/software-engineering-consensus/SKILL.md` | `<repo>/workflow/software-engineering-consensus/SKILL.md: OK` | 0 |
| `uv run python general/writing-for-llm/check_skill.py <repo>/workflow/domain-awareness/SKILL.md` | `<repo>/workflow/domain-awareness/SKILL.md: OK` | 0 |
| `uv run python general/writing-for-llm/check_skill.py <repo>/workflow/maintain-verification-skill/SKILL.md` | `<repo>/workflow/maintain-verification-skill/SKILL.md: OK` | 0 |
| `uv run python /home/bolo/.codex/skills/.system/skill-creator/scripts/quick_validate.py <repo>/workflow/software-engineering-consensus` | `Skill is valid!` | 0 |
| `git diff --check` | 无输出 | 0 |
| `rg -n 'WORKFLOW_VOCABULARY\|失败迭代' workflow general README.md agent-prompts --glob '!ROADMAP.json'` | 无匹配 | 1, 表示未找到 |

对活跃工作流及其参考材料的迭代命中逐项核对: 新 skill 中保留已确认概念的定义和反例; benchmark-checklist 的生成器遍历示例及来源说明, mailbox.py 的队列遍历代码注释均属技术意义, 保持原样.
与 `8b39649` 的差异可核对 PUBLIC 和其他历史文件未改. 未执行安装同步, 未修改已安装 skills 或全局配置. 本次检查不证明安装效果, 模型触发/漏触发/正文重读行为或 token 节省幅度.

## 独立复核阻塞

2026-10-30 14:07:55 UTC 前后, 已确认 `HERDR_ENV=1`, 目标为本容器和当前工作目录. `herdr status client` 成功返回客户端版本 0.9.3, 但 `herdr status` 和后续 `herdr agent list` 均报:

```text
Error: Os { code: 1, kind: PermissionDenied, message: "Operation not permitted" }
```

因此没有创建或提交独立复核会话, AC-02-07 的独立复核部分尚未完成, 不写 REVIEW.md 或假定其他代理已检查.
尝试按容器纪律通知已登记宿主会话时, mailbox presence 返回退出码 3, 提示在线查询失败; status 确认信箱服务不可达. 未能发送宿主请求.
恢复 Herdr 连接后, 按同目录 `REVIEW-REQUEST.md` 派给未参与修改的另一位代理. 独立复核及发现处理完成前不关闭本节点; 终点人工验收前不推送本次变更.
