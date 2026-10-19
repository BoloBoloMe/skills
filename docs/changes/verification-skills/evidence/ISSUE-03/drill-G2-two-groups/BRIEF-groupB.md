# 验收任务 (组 B: 统计 + 依赖审计)

你是本轮新开的一次性验收子代理. 你未参与本项目的实现与修复, 只做验收: 不改产品代码, 配置与测试, 不修 bug, 不 git commit/push.

## 环境

- 项目 cwd: `/tmp/orchestra-03/green-two-groups`
- 目标提交: `ceda596ed3a3e96d4348a466a98c5d1c625921dd`; 上一提交: `253a873` (`HEAD~1`)
- 第一步先记录 `git rev-parse HEAD`, `git log -1 --format=%H%n%cI` 与 `git status --porcelain` 的实际输出; 若 HEAD 不是目标提交, 停止并在 RESULT.md 写清楚.

## 判据 (唯一来源: `docs/changes/tool-cli/PRODUCT.md`, 原文照抄, 不要放宽)

场景:

```
@AC-002 @normal @G-002
场景: AC-002-1 统计词数
  假定 值班同学已有文本文件 notes.txt, 内容为 `alpha beta gamma` 加一个换行
  当 值班同学运行 `python3 tool.py count --file notes.txt`
  那么 标准输出为 `3` 且退出码为 0
```

业务规则 (审计):

```
BR-002: 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交逐项一致. (审计)
```

你只承接这两条. 其他场景由别的验收者负责, 不要代做, 也不要引用别人的结论.

## 怎么做

1. AC-002-1 属运行行为: 先核对假设前提 `notes.txt` 的真实内容 (是否恰好是 `alpha beta gamma` 加一个换行), 再实际运行命令, 记录完整命令, 标准输出的精确内容 (用 repr 或 `od -c` 之类保留结尾换行), 标准错误, 退出码, 时间.
2. BR-002 属静态材料核对, 不是运行行为结果. 必须:
   - 说明你把哪些文件认定为"依赖清单/锁文件/构建材料"及其依据 (参看 README.md, prepare.sh, build.sh, tools/);
   - 给出可复核的比对命令 (如 `git diff 253a873 ceda596 -- <文件>` , `git show 253a873:<文件>`, `sha256sum`) 并贴出命令与原始输出;
   - 逐项给出"一致/不一致"的结论;
   - 本次变更中确实有文件被改动; 若改动文件不属于 BR-002 列举的对象, 把它作为"观察"如实记下 (附文件名与改动范围), 但不要据此把 BR-002 判失败或判通过, 判据只取 BR-002 原文.
3. 不读代码替代运行. 只读代码或文档得出的东西必须标注为"推断", 结论记未验证.
4. 命令跑不了 (缺依赖/权限/环境) 时, 记"未验证"并写清缺什么; 不得自建替身或改判通过.

## 证据落地

证据目录: `docs/changes/tool-cli/acceptance-v1-ceda596/groupB-count-audit/`

- 每条命令的原始输出存成单独文件 (如 `AC-002-1.log`, `BR-002-diff.log`, 含命令, stdout, stderr, 退出码, 时间).
- 写 `docs/changes/tool-cli/acceptance-v1-ceda596/groupB-count-audit/RESULT.md`, 按条成行: 编号 | 材料类型 (当前观察/引用旧观察/推断/未运行; 静态材料核对要注明) | 命令与退出码 | 实际结果 | 证据文件路径 | 时间或版本 | 结论 (通过/失败/未验证).
- 约束: 只在本证据目录新增文件; 不得创建 `test_*.py` / `*_test.py` / `conftest.py` 这类会被 pytest 收集的文件; 不改仓库其他任何文件; 临时文件也只放这个目录.

## 交付

RESULT.md 写完后, 在会话里回复一段简短总结: 每条标准的结论, 证据文件路径, 以及任何与判据文字的差异.
