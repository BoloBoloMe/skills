---
name: to-product-spec
description: 将已确认产品方案整理为 AI 使用的 Product Spec.
disable-model-invocation: true
---

开始前, 调用 `domain-awareness` skill 只读感知当前工作目录的领域模型.

目标: 编写 Product Spec: `PRODUCT.md`. 它将作为当前变更的产品结果基线. 文档只供 AI 使用.

从可靠信源处收集 PRODUCT.md 需要的信息, 如果发现存在缺口/冲突 就调用 `grilling` skill 盘问我. 
使用下方模板写 `PRODUCT.md`. ID 在 feature 内稳定且连续. 输出为 `docs/changes/<feature-slug>/PRODUCT.md`.

<product-spec-template>

# <变更标题> Product Spec

## 背景
当前问题, 真实受益者, 需求来源和现在处理的理由.

## 目标
- G-001: 可衡量或可观察的产品结果.

## 非目标
- 不做 X, 它不在本变更范围内.

## 用户故事
- US-001: 作为 <actor>, 我想要 <capability>, 以便 <benefit>.

## 业务规则
- BR-001: 产品必须遵守的规则.

## 验收标准
- AC-001: 给定 <前提>, 当 <行为>, 则 <可观察结果>. 覆盖: G-001, US-001.

## 成功指标
- 指标, 观察窗口和目标值. 不设指标时写已确认理由.

## 产品决策引用
- `DECISIONS.md` 中相关产品决策 ID. 无则写"无".

## 待验证事实
- 事实:
  影响:
  验证方式:
没有则写"无".

</product-spec-template>

完成标准: 固定章节齐全; 每个验收标准可观察且至少关联一个目标或用户故事; 每项产品结论都能追溯到源头. 无阻塞产品缺口或冲突; 每项非阻塞未知都有影响和验证方式.
编写完成后, 在会话中告诉我: 已生成的路径, 是否存在待验证事实, 是否发现来源冲突. 不复述文档, 不让我阅读后确认.