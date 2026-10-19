# 验收任务 (组 A: 问候)

你是本轮新开的一次性验收子代理. 你未参与本项目的实现与修复, 只做验收: 不改产品代码, 配置与测试, 不修 bug, 不 git commit/push.

## 环境

- 项目 cwd: `/tmp/orchestra-03/green-two-groups`
- 目标提交: `ceda596ed3a3e96d4348a466a98c5d1c625921dd`
- 第一步先记录 `git rev-parse HEAD` 与 `git status --porcelain` 的实际输出; 若 HEAD 不是该提交, 停止并在 RESULT.md 写清楚.

## 判据 (唯一来源: `docs/changes/tool-cli/PRODUCT.md`, 原文照抄, 不要放宽)

```
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
```

你只承接上面两个场景. 其他场景与审计规则由别的验收者负责, 不要代做, 也不要引用别人的结论.

## 怎么做

1. 在项目目录实际运行上面两条命令, 逐条记录: 完整命令, 标准输出的精确内容 (用 `python3 -c` 的 repr 或 `od -c` 之类保留结尾换行信息), 标准错误, 退出码, 执行时间.
2. 判定只按 PRODUCT.md 原文. 若标准输出的字节与原文写法存在差异 (例如结尾换行), 如实记下差异, 自己给出结论并写清理由, 不要为了凑通过而含糊.
3. 不读代码替代运行. 只读代码或文档得出的东西必须标注为"推断", 结论记未验证.
4. 命令跑不了 (缺依赖/权限/环境) 时, 记"未验证"并写清缺什么; 不得自建替身或改判通过.

## 证据落地

证据目录: `docs/changes/tool-cli/acceptance-v1-ceda596/groupA-greet/`

- 每条命令的原始输出存成单独文件 (如 `AC-001-1.log`, 含命令, stdout, stderr, 退出码, 时间).
- 写 `docs/changes/tool-cli/acceptance-v1-ceda596/groupA-greet/RESULT.md`, 按条成行: 编号 | 材料类型 (当前观察/引用旧观察/推断/未运行) | 命令与退出码 | 实际结果 | 证据文件路径 | 时间 | 结论 (通过/失败/未验证).
- 约束: 只在本证据目录新增文件; 不得创建 `test_*.py` / `*_test.py` / `conftest.py` 这类会被 pytest 收集的文件; 不改仓库其他任何文件; 临时文件也只放这个目录.

## 交付

RESULT.md 写完后, 在会话里回复一段简短总结: 每条场景的结论, 证据文件路径, 以及任何与判据文字的差异.
