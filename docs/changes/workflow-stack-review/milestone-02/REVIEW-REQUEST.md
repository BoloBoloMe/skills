# milestone-02 独立复核请求

状态: 待派工, 尚未执行. 本文件是工作输入, 不是独立复核报告.

请由未参与本次修改的另一位代理检查本里程碑. 用 Herdr 在本容器当前仓库创建会话, 按 use-herdr 的启动/选型规则操作. 仅写本目录的 `REVIEW.md` 和检查原始记录, 不改实现或标准, 不提交其他文件或推送.

## 目标与依据

- 仓库: 当前 `refactor-skill-around-verification` 工作目录.
- 目标提交: `dcf06358c9a9ecff600228fa5eb300a65deec46e`.
- 变更起点: `8b39649715f1aa4930e69004b0d9c706e08b7553`, 范围包括 domain-awareness 的前置删除和主体实施.
- 标准: `docs/changes/workflow-stack-review/ACCEPTANCE.md` 的 AC-02-01 至 AC-02-08.
- 当前有效决策: `docs/changes/workflow-stack-review/milestone-01/DECISIONS.md` 的 D001/D002/D004-D008/D010/D013-D015. D014/D015 已替代 D009/D011, 不据旧方案要求指向新 skill 或增加正文复用规则.
- 原始迁移依据: 起点提交中的 `workflow/domain-awareness/WORKFLOW_VOCABULARY.md`.

直接核对目标提交中的实际文件和差异, 不以作者的 IMPLEMENTATION.md 自检结论代替检查. 若当前版本与目标提交在受查文件上不同, 先列版本差异, 不把其他版本的结果套用到目标上.
ROADMAP.json 的内容只经 `uv run python workflow/navigate/scripts/roadmap.py query <file> <path>` 读取, 不直接读写该文件.

## 检查范围

逐项覆盖全部 AC-02 条目, 尤其完整迁移定义/避免项和适用范围, 两类收录规则, 四个概念的责任与验证边界, 用户新确认的两项删除要求, README 入口, 三处称谓修正及原数据留存要求. 区分活跃文档与历史证据, 区分泛用流程叫法与生成器/算法/代码注释的技术意义.

独立执行三个 SKILL.md 的 `check_skill.py`, 保留命令, 完整实际输出, 退出码和 UTC 时间:

```bash
uv run python general/writing-for-llm/check_skill.py workflow/software-engineering-consensus/SKILL.md
uv run python general/writing-for-llm/check_skill.py workflow/domain-awareness/SKILL.md
uv run python general/writing-for-llm/check_skill.py workflow/maintain-verification-skill/SKILL.md
```

本次只改文档, 检查范围以已确认标准为准. 不执行会修改已安装 skills 的同步或修改全局配置, 不把静态格式与文本检查扩大为模型触发率, 安装效果或 token 收益的实测结论.

## 输出

`REVIEW.md` 写明复核者身份, 目标提交和标准版本, 实际执行的命令与记录位置. 按 AC 编号逐项记录通过/失败/未检查及可复核依据, 指出判断属于静态观察还是运行结果. 列出所有发现和缺口; 有问题直接报告, 不替用户改决策或标准.
结束时把报告路径交回协调方. 协调方收到并处理全部发现后, 才能经守门脚本更新里程碑状态. 本次独立复核不代替 milestone-08 的人工逐项验收.
