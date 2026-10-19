# 验收记录 acc-g5b-1

## 目标提交

- HEAD (完整): `5d3765e9b0d8228b8738a75ea69baef048402c45`
- 工作区: `/tmp/orchestra-03/micro2/micro-groups`
- 验收人角色: 本轮产品验收执行者 (未参与实现/修复)
- 判据来源: `docs/changes/tool-cli/PRODUCT.md` 的 验收标准 节 (gherkin), 共 3 条, 全部分配给本记录
- 验收时间: 2026-10-19 20:53:54 ~ 20:54:52 CST (2026-10-19T12:53:54Z ~ 12:54:52Z)
- 原始材料: `acc-g5b-1-raw.txt` (命令原文 / 真实输出 / 退出码 / 时间戳)

## 逐条结果

| 标准编号 | 材料类型 | 命令与原始输出摘要 | 实际结果 | 证据文件路径 | 时间 | 结论 |
|---|---|---|---|---|---|---|
| AC-001-1 | 当前观察 | 前提: `bash prepare.sh` (exit 0, 22.26s, stdout `built dist/app.txt`) 生成 85 字节 `dist/app.txt`; 判据: `sed -n '1p' dist/app.txt` (exit 0) -> `>>>tool-cli 1<<<`; `cat -A` -> `tool-cli 1$` 无尾部空白; hex `74 6f 6f 6c 2d 63 6c 69 20 31`; `cmp` (含换行) 与期望字面量 `tool-cli 1` IDENTICAL | 第一行内容逐字节等于 `tool-cli 1` | `docs/changes/tool-cli/verify-5d3765e-r1/acc-g5b-1-raw.txt` (STEP 1, STEP 3 AC-001-1 段) | 2026-10-19 20:54:24 CST | 通过 |
| AC-002-1 | 当前观察 | 同一份 `dist/app.txt` (STEP 1 产物); 判据: `sed -n '2p' dist/app.txt` (exit 0) -> `>>>commands=greet,count,export<<<`; `cat -A` -> `commands=greet,count,export$`; hex 20 字节 `63 6f 6d 6d 61 6e 64 73 3d 67 72 65 65 74 2c 63 6f 75 6e 74 2c 65 78 70 6f 72 74`; `cmp` (含换行) 与期望字面量 IDENTICAL | 第二行内容逐字节等于 `commands=greet,count,export` | 同上 (STEP 1, STEP 3 AC-002-1 段) | 2026-10-19 20:54:24 CST | 通过 |
| AC-003-1 | 当前观察 | 同一份 `dist/app.txt` (STEP 1 产物); 判据: `sed -n '3p' dist/app.txt` (exit 0) -> `>>>greet-shout=yes<<<`; `cat -A` -> `greet-shout=yes$`; hex 16 字节 `67 72 65 65 74 2d 73 68 6f 75 74 3d 79 65 73`; `cmp` (含换行) 与期望字面量 IDENTICAL | 第三行内容逐字节等于 `greet-shout=yes` | 同上 (STEP 1, STEP 3 AC-003-1 段) | 2026-10-19 20:54:24 CST | 通过 |

严格性说明: 三条都用 `cmp` 把 "整行含行尾换行" 与 "期望字符串 + `\n`" 做字节级比较, 全为 IDENTICAL; 另用 `cat -A` 确认无行尾空格/制表符/`\r`, 用 `od -c`/hex 确认无隐藏字符. 行号按原文 1/2/3.

前置条件落实: 验收开始时 `dist/` 不存在 (从未生成), 本轮由验收人亲自执行 `bash prepare.sh` 生成, 属"当前观察", 非引用旧产物.

## 附注 (不属于产品判据, 不判通过/失败)

1. **第 4 行**: `dist/app.txt` 共 4 行, 第 4 行为 `greet-digest=aa6fe618e31999db` (见 STEP 2/4). 三条 gherkin 均未涉及该行, 不影响判据.
2. **稳定性**: 同一提交下第二次执行 `bash prepare.sh` (exit 0, 22.28s) 后 `dist/app.txt` 的 sha256 前后一致 (`b6a670b3e2fd0e6b5e22ec35cd4c37548c3ad23f42d2bef7125f987adde00324`), 前 4 行逐字节相同. 仅作稳定性观察.
3. **执行耗时**: 两次 prepare 均约 22.3s, 与 README 所述 "约 25 秒" 同一量级.
4. **未运行项**: 未跑 `python3 -m pytest -q` 与 `bash build.sh`. 它们出现在 README/TECHNICAL 的"检查/验证入口", 但不在 PRODUCT.md gherkin 内, 不是产品通过条件. 按规则只记操作线索.
5. **调用方式**: `prepare.sh` 内部直接 `python3 tools/build_manifest.py` (未用 `uv run`). 属工程约定事项, 不作为产品判据.
6. **仓库状态**: 验收过程只读源码/配置/测试/PRODUCT.md, 未 `git add/commit/checkout/clean`, 未删除 `dist/`. `git status --porcelain` 仅显示本证据目录未跟踪项 `?? docs/changes/tool-cli/verify-5d3765e-r1/`; `dist/` 被 `.gitignore:3:dist/` 忽略 (见 STEP 5).
7. 本轮未做代码评审, 未改产品.

## 结论

三条场景 AC-001-1 / AC-002-1 / AC-003-1 全部 通过, 无失败, 无未验证.
