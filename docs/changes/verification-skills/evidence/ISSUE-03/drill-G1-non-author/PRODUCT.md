# 工具集 Product Spec

## 背景

值班同学需要一个小的命令行工具集, 覆盖问候生成, 文本统计与报告导出. 本次变更只给问候增加全大写开关.

## 目标

- G-001: 值班同学能按姓名生成问候, 并可切换全大写输出.
- G-002: 值班同学能统计文本文件的词数与字符数.
- G-003: 值班同学能把问候导出为 JSON 报告.

## 非目标

- NG-001: 不做多语言. (理由: 当前只有中文团队使用.)

## 业务规则

- BR-001: 问候语以 `Hello` 开头, 后接分隔符与姓名, 以 `!` 结尾; 全大写模式下整体转为大写.
- BR-002: 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交逐项一致. (审计)

## 验收标准

<!-- confirmed-flow: v1 -->
```gherkin
# language: zh-CN
功能: 工具集

@AC-001 @normal @G-001 @BR-001
场景: AC-001-1 默认问候
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py greet --name Ada`
  那么 标准输出为 `Hello, Ada!` 且退出码为 0

@AC-001 @edge @G-001 @BR-001
场景: AC-001-2 全大写问候
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py greet --name Ada --shout`
  那么 标准输出为 `HELLO, ADA!` 且退出码为 0

@AC-002 @normal @G-002
场景: AC-002-1 统计词数
  假定 值班同学已有文本文件 notes.txt, 内容为 `alpha beta gamma` 加一个换行
  当 值班同学运行 `python3 tool.py count --file notes.txt`
  那么 标准输出为 `3` 且退出码为 0

@AC-002 @edge @G-002
场景: AC-002-2 统计字符数
  假定 值班同学已有文本文件 notes.txt, 内容为 `alpha beta gamma` 加一个换行
  当 值班同学运行 `python3 tool.py count --file notes.txt --chars`
  那么 标准输出为 `17` 且退出码为 0

@AC-003 @normal @G-003
场景: AC-003-1 JSON 导出
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py export --name Ada`
  那么 标准输出为 `{"name": "Ada", "greeting": "Hello, Ada!"}` 且退出码为 0
```

## 决策引用

- 无.
