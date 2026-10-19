# 验收结果 (组 B: AC-002-1 统计 + BR-002 依赖审计)

- 验收对象: 提交 `ceda596ed3a3e96d4348a466a98c5d1c625921dd` (上一提交 `253a873`)
- 判据唯一来源: `docs/changes/tool-cli/PRODUCT.md` (原文照抄, 未放宽)
- 验收人: 本轮一次性验收子代理, 未参与实现与修复; 未改产品代码/配置/测试, 未 commit/push
- 证据目录: 本目录 (`docs/changes/tool-cli/acceptance-v1-ceda596/groupB-count-audit/`), 所有日志文件含命令, stdout, stderr, 退出码, 时间
- 时间: 2026-10-19T20:35 至 20:36 (+08:00), 详见各日志内时间戳

## 环境前提

| 编号 | 材料类型 | 命令与退出码 | 实际结果 | 证据文件路径 | 时间或版本 | 结论 |
|---|---|---|---|---|---|---|
| ENV-1 | 当前观察 | `git rev-parse HEAD`, rc=0 | `ceda596ed3a3e96d4348a466a98c5d1c625921dd`, 与目标提交一致 | 00-git-state.log | 2026-10-19T20:35:45+08:00 / ceda596 | 环境符合, 继续验收 |
| ENV-2 | 当前观察 | `git log -1 --format=%H%n%cI`, rc=0 | `ceda596...1dd`; 提交时间 `2026-10-19T20:27:16+08:00` | 00-git-log.log | 同上 | - |
| ENV-3 | 当前观察 | `git status --porcelain`, rc=0 | 仅 `?? docs/changes/tool-cli/acceptance-v1-ceda596/` (本验收证据目录, 未跟踪); 无其他改动 | 00-git-status.log | 同上 | 工作区干净, 跟踪文件等于 HEAD |

## AC-002-1 统计词数

判据原文 (PRODUCT.md):

```
@AC-002 @normal @G-002
场景: AC-002-1 统计词数
  假定 值班同学已有文本文件 notes.txt, 内容为 `alpha beta gamma` 加一个换行
  当 值班同学运行 `python3 tool.py count --file notes.txt`
  那么 标准输出为 `3` 且退出码为 0
```

| 编号 | 材料类型 | 命令与退出码 | 实际结果 | 证据文件路径 | 时间或版本 | 结论 |
|---|---|---|---|---|---|---|
| AC-002-1-前提 | 当前观察 (运行行为的前提核对) | `od -c notes.txt; stat -c %s notes.txt; sha256sum notes.txt`, rc=0 | 17 字节, 字节序列 `alpha beta gamma\n` (16 字符 + 1 个 `\n`), sha256 `adf7157c...3ff96`; 与判据假定 "内容为 `alpha beta gamma` 加一个换行" 恰好一致; 文件在两提交间未改动 (见 BR-002-name-status.log 全量对照) | AC-002-1-premise.log | 2026-10-19T20:35:45+08:00 / ceda596 | 前提成立 |
| AC-002-1 | 当前观察 (运行行为) | `python3 tool.py count --file notes.txt` (cwd=仓库根), rc=0 | stdout 精确字节 `b'3\n'` (od -c: `3 \n` 共 2 字节, 可见输出行恰为 `3`); stderr 为空; 退出码 0 | AC-002-1-run.log | 2026-10-19T20:35:53+08:00 / ceda596 | 通过 |

AC-002-1 说明 (与判据文字的差异): 判据写 "标准输出为 `3`", 实测 stdout 为 `3` 后跟一个换行 (`b'3\n'`). 判据未要求 "无换行"; 行结束换行是该命令正常输出行为 (同文件里 AC-001 的 `Hello, Ada!` 同理). 按输出行内容为 `3` 解读, 与判据一致, 判通过; 字节级细节已如实用 od -c 与 repr 记录在 AC-002-1-run.log. 未运行其他任何 AC 场景, 不引用其他验收者结论.

## BR-002 依赖审计

判据原文 (PRODUCT.md): `BR-002: 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交逐项一致. (审计)`

### 对象认定 (哪些文件算 "依赖清单/锁文件/构建材料")

| 认定对象 | 认定为 | 依据 | 材料类型 |
|---|---|---|---|
| `deps.txt` | 依赖清单 | 文件名即依赖列表; 内容为 `python-stdlib` | 推断 (依据文件名与内容自述, README 未直接点名该文件) |
| `deps.lock` | 锁文件 | 文件名带 `.lock`; 内容自述 "本工具只用 Python 标准库, 无第三方依赖." | 推断 (同上) |
| `prepare.sh`, `build.sh`, `tools/build_manifest.py` | 构建材料 | README "构建检查" 一节: `bash prepare.sh` 生成 `dist/app.txt` 构建清单; `bash build.sh` 为构建检查命令; prepare.sh 内容为调用 `python3 tools/build_manifest.py`; build_manifest.py 自述 "生成构建清单" | 推断 (依据 README 与脚本内容) |

仓库全量文件清单 (git ls-tree -r, 两提交) 中不存在其他疑似依赖/锁/构建文件 (无 requirements.txt, pyproject.toml, package-lock.json 等); 该 "不存在其他对象" 本身也是清单比对的当前观察. 依据原文见 BR-002-classify.log, 两提交全量清单见 BR-002-filelist.log (253a873) 与 BR-002-filelist-head.log (ceda596), 两者文件集合完全相同.

### 逐项比对

| 编号 | 材料类型 | 命令与退出码 | 实际结果 | 证据文件路径 | 时间或版本 | 结论 |
|---|---|---|---|---|---|---|
| BR-002-1 | 静态材料核对, 当前观察 | `git diff 253a873 ceda596 -- deps.txt deps.lock prepare.sh build.sh tools/build_manifest.py`, rc=0 | diff 输出为空, 5 个文件均无任何改动 | BR-002-diff.log | 2026-10-19T20:36:18+08:00 / 253a873 vs ceda596 | 逐项一致 |
| BR-002-2 | 静态材料核对, 当前观察 | `git diff --exit-code 253a873 ceda596 -- <同上5文件>`, rc=0 | `--exit-code` 返回 0, 即逐项无差异 | BR-002-diff-exit.log | 同上 | 逐项一致 |
| BR-002-3 | 静态材料核对, 当前观察 | 对每文件: `git show 253a873:<f> \| sha256sum` 与 `git show ceda596:<f> \| sha256sum` 与工作区 `sha256sum <f>` | 5 个文件三个来源 sha256 全部相同, 逐项判定 "一致": deps.txt `f37d7a06...d4806`; deps.lock `28cc4586...5f50`; prepare.sh `d763bb6f...fac75e`; build.sh `ae45fcf9...5aad`; tools/build_manifest.py `4c304ef9...4aee2` (完整哈希见日志) | BR-002-hash.log | 2026-10-19T20:36:32+08:00 | 逐项一致 |
| BR-002-4 | 静态材料核对, 当前观察 | 工作区复核: `git diff --exit-code ceda596 -- <同上5文件>`, rc=0; `git status --porcelain` | 跟踪文件与 ceda596 无差异, 工作区仅未跟踪的证据目录; 即比对基于真实提交内容, 不受本地改动影响 | BR-002-worktree.log | 2026-10-19T20:36:32+08:00 | 逐项一致 |
| BR-002-5 | 静态材料核对, 当前观察 + 推断 | `git ls-tree -r --name-only 253a873` 与 `git ls-tree -r --name-only ceda596`, rc=0 | 两提交全量文件集合相同 (12 个文件, 一一对应), 变更未新增任何文件, 故不存在新增依赖文件; "无第三方依赖" 另据 deps.lock 与 deps.txt 内容自述 | BR-002-filelist.log, BR-002-filelist-head.log, BR-002-classify.log | 同上 | 不新增第三方依赖, 逐项一致 |

### BR-002 总结论: 通过 (逐项一致)

### 观察记录 (不属 BR-002 列举对象, 不据此改判)

| 编号 | 材料类型 | 命令与退出码 | 实际结果 | 证据文件路径 | 时间或版本 | 结论 |
|---|---|---|---|---|---|---|
| OBS-1 | 当前观察 | `git diff --name-status 253a873 ceda596`, rc=0 | 本次变更确实改动了 2 个文件: `M tool.py` (约 +5/-3 行), `M tests/test_tool.py` (+6 行, 详 BR-002-observation.log). 两者不属于 BR-002 列举的依赖清单/锁文件/构建材料对象, 属产品代码与测试, 由对应场景的验收者负责 | BR-002-name-status.log, BR-002-observation.log | 2026-10-19T20:36:19+08:00 | 观察: 改动范围与 BR-002 对象不重叠 |

## 未验证 / 未运行项

- BR-002 按任务要求为静态材料核对, 本次未运行 `prepare.sh` / `build.sh` (运行构建脚本属另一性质验证, 且会产生 `dist/`, `__pycache__/` 等仓库内产物); 构建材料 "能正常运行" 不在 BR-002 判据文字内, 结论不受影响, 特此注明.
- 无因缺依赖/权限导致跑不了的命令; AC-002-1 已实际运行.

## 汇总

| 编号 | 结论 |
|---|---|
| AC-002-1 | 通过 (stdout `3\n`, stderr 空, 退出码 0; 前提 notes.txt 内容核对一致) |
| BR-002 | 通过 (deps.txt, deps.lock, prepare.sh, build.sh, tools/build_manifest.py 与 253a873 逐项一致; 未新增第三方依赖) |
