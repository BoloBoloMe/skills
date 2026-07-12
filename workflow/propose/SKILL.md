---
name: propose
description: 处理我的提案.
disable-model-invocation: true
---

使用 `grill-with-docs` skill 处理我的提案. 盘问中的每次回答都使用 `present-information` skill, 直至盘问结束.
盘问会话结束后, 询问我是否生成 spec. 如果我说不用, 就跳过本行内容; 如果我说要, 那么依次执行后面这些 skills, 一个完成后, 再执行下一个: to-product-spec, to-technical-spec, to-execution-spec.
