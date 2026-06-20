# AFK lightweight test-only flow

本文件定义 `test-only-light` 路径. 只有无生产代码变更的小型测试 issue 才能使用该路径. 正常主流程见 `RUNBOOK.md`, 产物契约见 `CONTRACTS.md`.

## 进入条件

进入 `test-only-light` 需要预声明和真实 diff 双门禁.

预声明满足其一:

- issue/PLAN 明确写 `review: skip` 或 `review: lightweight`.
- issue/PLAN 明确写仅测试变更, coverage only, regression test only 等同义意图.

预声明只是意图, 不能单独跳过 review. 最终必须由真实 diff 机械验证.

## review-policy.md

父会话在预检阶段写入 `afk-running/<issueKey>/review-policy.md`:

```md
issueExecutionMode: test-only-light
reviewPolicy: skip-with-verification
changedLinesThreshold: 50
testFilePatterns:
- src/test/**
- test/**
- tests/**
- **/*Test.java
- **/*Tests.java
- **/*.test.*
- **/*.spec.*
productionFilePatterns:
- src/main/**
- app/**
- lib/**
- build.gradle
- pom.xml
- package.json
```

如果项目无法明确区分测试文件和生产文件, 不启用 `test-only-light`, 走完整 review.

## worker 规则

`test-only-light` worker:

- 只允许修改测试文件.
- 不要求 RED 证据.
- 必须运行聚焦 GREEN 验证.
- 如果新增或修改的测试必须修改生产代码才能通过, 立即停止并报告.
- 不得修改生产代码, 构建脚本, 配置, fixture 生成器或测试基础设施, 除非这些文件被明确归类为测试文件并列入允许文件清单.

## 差异检查

worker 结束后, 父会话必须确认:

- diff 只匹配 `testFilePatterns`.
- 无生产代码, 配置, 构建脚本, fixture 生成器等变更.
- changed lines 小于等于 `changedLinesThreshold`, 默认 50 行 added+deleted.
- 聚焦 GREEN 验证通过.
- 无 staged 文件.

任一条件不满足, 不按轻量路径继续. 父会话应转完整 review, 启动恢复 worker, 或询问用户.

## 跳过 review 条件

如果满足以下条件, 跳过 3 reviewer 和综合判定, 写入 `review-skipped.md`, 直接进入最终验证:

- `reviewPolicy == skip-with-verification`.
- 真实 diff 只涉及测试文件.
- changed lines 小于等于阈值.
- 聚焦验证通过.
- 无 staged 文件.

## review-skipped.md

`review-skipped.md` 必须记录:

- issueKey.
- 跳过原因.
- diff 文件列表.
- changed lines 统计.
- 命中的测试文件规则.
- 验证命令和结果.
- 是否有生产代码变更: no.
- 是否有 staged 文件: no.

## 回退到 normal 的情况

出现以下任一情况, 停止轻量路径:

- 测试变更暴露了需要修改生产代码的问题.
- diff 超出测试文件规则.
- changed lines 超过阈值.
- GREEN 验证无法运行或失败.
- 用户要求完整 review.

回退后不能静默继续. 父会话必须说明原因, 并询问用户是转 normal issue, 启动恢复 worker, 还是停止.
