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

## 验收标准

<!-- confirmed-flow: v1 -->
```gherkin
# language: zh-CN
功能: 工具集

@AC-001 @normal @G-001 @BR-001
场景: AC-001-1 构建清单第一行
  假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`
  当 值班同学读取 `dist/app.txt` 的第一行
  那么 内容为 `tool-cli 1`

@AC-002 @normal @G-002
场景: AC-002-1 构建清单第二行
  假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`
  当 值班同学读取 `dist/app.txt` 的第二行
  那么 内容为 `commands=greet,count,export`

@AC-003 @normal @G-003 @BR-001
场景: AC-003-1 构建清单第三行
  假定 值班同学已运行 `bash prepare.sh` 生成 `dist/app.txt`
  当 值班同学读取 `dist/app.txt` 的第三行
  那么 内容为 `greet-shout=yes`
```

## 决策引用

- 无.
