# 第二轮 Spec 评审

## 来源与命令

Spec 路径均相对 `docs/changes/verification-skills/`:
- `PRODUCT.md`: BR-003/005/008/010/011, AC-007/024/028/030/031.
- `TECHNICAL.md`: 五个模块接口, 两项复刻共同交付要求, 安全策略.
- `DECISIONS.md`: D009, D021-D024, D034.
- `issues/ISSUE-16..20` 对应文件的完整 TDD 切片与验收标准.
- 首轮 `evidence/code-review/SPEC.md` 与 `STANDARDS.md` 仅作待验证线索, 不作为修复证明.

```bash
git rev-parse --verify 5c21b0b^{commit}
git diff 5c21b0b...HEAD -- . ':(exclude)docs/changes/verification-skills/evidence'
git log 5c21b0b..HEAD --oneline
```

对象: 分支 `v2`, HEAD `f6cde3910507a8edf6131e1d62a58d7f1ec2fb4f`. 基准有效, diff 非空. 已完整读取改动技能及相关参考文件, 并核对对应完整 Spec 段落. 以下是正文契约复核, 不宣称演练已通过, 不采信执行者自报代替原始证据. 未启动会话或运行演练.

## 第一轮发现 1-5

1. **已修复.** `TECHNICAL.md:126` 要求写前说明 "资源/对象/操作/清理及验证并等批准". `workflow/create-verification-skill/SKILL.md:25-40,63` 与 `workflow/maintain-verification-skill/SKILL.md:38-53,65` 均补齐写前批准, 运行期独立授权, 同范围复跑及向子会话传递批准范围, 符合 ISSUE-17 TS-001.

2. **已修复.** `PRODUCT.md:552-577` 要求 "实验被明确标为非正式 TC", 需要新正式接缝时 "停止并交回既有用例确认流程". `workflow/blast-radius/SKILL.md:64-76` 已承接非正式标记, 源码/测试/配置保护, 清理, 成品入口证据区分及停止规则.

3. **已修复.** `PRODUCT.md:32` 原文 "受影响的关键真实路径须由非作者实跑". `workflow/verify-change/SKILL.md:33,38,78,105` 将首次验收和复验统一为关键路径本轮实跑; 作者日志仅作对照, 非关键旧观察才可按适用条件复用.

4. **部分修复.** `TECHNICAL.md:54` 原文 "不额外强制其余五问, 异常再查". `workflow/benchmark-checklist/SKILL.md:102-110` 已恢复只强制第 4/7 问, 单次声明, 异常检查与选型排除; 但第 105 行又扩大豁免, 见 N1.

5. **已修复.** `PRODUCT.md:716-720` 要求 "补测用户端到端路径以及真实数据和并发" 并报告占比. `workflow/benchmark-checklist/SKILL.md:78,86` 已取消只在声称整条路径收益时才补测的条件; 无法补齐则明列缺口并限制结论, 符合 ISSUE-19 TS-002.

## 新发现

### N1 中: 粗估例外越界豁免规划/固定脚本检查

位置: `workflow/benchmark-checklist/SKILL.md:105` 新增 "粗估不动用 ... `## 基线与脚本固定前` 的完成标准".

依据: `TECHNICAL.md:54` 只豁免七问中的其余五问; 第 55 行另要求 "基线用于规划前及后续数字均检查; 持续优化脚本固定前须检查并自带错误数和工作量". `PRODUCT.md:744-755` 同样要求先审基线方法/适用条件, 且 "补好后该脚本才被认可固定".

这两项不是七问中的可省检查. 粗估数字同时用于规划, 或其脚本准备固定时, 新句却允许把对应检查从完成条件中剔除, 与前一节的强制条件冲突. 应只豁免其余五问, 保留规划/固定场景触发的独立检查; 不必因此恢复粗估的全套测量要求.

除此之外, 未发现可确认的新功能/协议/平台/部署或自动 Git 行为扩张. 结论: 1/2/3/5 闭合, 4 需按 N1 收口; 新发现 1 条, 中优先级. 本轮不审文风或坏味道, 除本报告外不修改文件.
