# Spec 轴评审

Spec 来源 (下文 Spec 引用均相对 `docs/changes/verification-skills/`):
- `docs/changes/verification-skills/PRODUCT.md`
- `docs/changes/verification-skills/TECHNICAL.md`
- `docs/changes/verification-skills/EXECUTION.md`
- `docs/changes/verification-skills/DECISIONS.md`
- `docs/changes/verification-skills/issues/ISSUE-*.md` (01-15, 均已完整读取)

Diff/commit 命令:
```bash
git diff ec9d55f...HEAD -- . ':(exclude)docs/changes/verification-skills/evidence'
git log ec9d55f..HEAD --oneline
```

对象: 分支 `v2`, `ec9d55f..53e75b4`. 基准可解析, diff 非空. 以下均已读完整技能段落及必要参考材料, 是正文契约与 Spec 的差异, 不声称已复现运行事故. evidence 仅少量抽查, 不以执行者自报缺口作为结论.

## (a) 要求缺失或不完整: 2 条

1. **高: 生成/维护配方缺写入批准步骤.** `TECHNICAL.md:125-126` 要求 "默认只读" 和写入前说明 "资源/对象/操作/清理及验证并等批准"; `DECISIONS.md:214` 明确生成/维护的运行期临时数据也受独立授权约束. 但 `workflow/create-verification-skill/SKILL.md:21-32,44-51` 直接要求写操作配方并派工实跑, 未要求取得上述批准或把批准范围交给子会话. `workflow/maintain-verification-skill/SKILL.md:45-50` 同样缺失; 第 19 行的 "必要权限" 不等于业务写入批准. 应在实跑前补齐授权与范围变更检查, 生成配方也须保留这条边界.

2. **高: blast-radius 未承接一次性实验边界.** `PRODUCT.md:551-577` 要求 "实验被明确标为非正式 TC", 内部证明不能顶替成品入口, 需新正式接缝时停止交回; `issues/ISSUE-08-benchmark-bounds-baseline.md:58-61` 明确接缝包含两个方法. `workflow/blast-radius/SKILL.md:49-60` 只有真实脚本/不改源码测试/副作用先问, 缺非正式标记, 配置保护, 清理, 成品证据区分及新接缝停止规则. 这些规则只写进 benchmark-checklist, blast-radius 没有调用指针, 单独使用时不成立.

## (b) Spec 未要求的范围扩张: 0 条

未发现可确认的新增协议/平台/自动 Git 交付或部署行为. 下述例外写反归入 (c), 不重复计数.

## (c) 实现方式错误: 3 条

3. **高: 首次验收可能只复用作者日志.** `PRODUCT.md:32` 要求 "受影响的关键真实路径须由非作者实跑"; `PRODUCT.md:229-233` 明说作者日志不能单独作为通过依据. `workflow/verify-change/SKILL.md:33,73-84` 却对条件仍适用的旧观察要求 "不叫验收者重跑同一场景", 未排除关键路径. 本人实跑规则只在 `:97-104` 的修复后复验段. 首次验收拿到目标版本的作者原始日志时, 可因此跳过独立实跑. 应将关键路径例外放进通用派工/证据复核步骤.

4. **中: 粗估例外被缩小.** `TECHNICAL.md:54` 原文 "不额外强制其余五问, 异常再查". `workflow/benchmark-checklist/SKILL.md:100-108` 却说 "例外省掉的只是重复与统计", 意味着仍强制调优/限制因素/上限/端到端等检查. 应恢复只强制第 4/7 问, 非选型且无异常时允许单次量级报告.

5. **中: 微基准补测端到端被改成有条件.** `PRODUCT.md:715-720` 的 AC-030-3 要求微基准已有结果但真实路径未测时 "补测用户端到端路径以及真实数据和并发". `workflow/benchmark-checklist/SKILL.md:66-84` 尤其第 76 行却限定为 "要下整条路径的结论, 就补测". 只发布函数自身的性能结论便能绕过补测, 不满足该场景. 应恢复微结果旁必须有端到端实测及占比, 无法补齐则列缺口.
