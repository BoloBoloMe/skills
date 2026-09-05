# ISSUE-03 镜像制备: base/项目两层镜像的分析-匹配-构建-记录闭环

## 父级

- `../roadmap/MILESTONE-07.md` (M07 本体; 状态变更归 roadmap, 本文件不改其状态)
- `../DECISIONS.md`: D014 (两层结构/门禁扩展留 host), D015 (tag=日期-序号/条目=名称+版本谓词/contents 实测), D016+D024 (记录落 ~/.agents/sandbox-worktree/<slug>/builds/<build-id>/; label 前缀 run.sandbox-worktree.*; project-id=主仓绝对路径; slug 冲突加短 hash; build-id 查重), D017 (候选匹配: project-id 过滤/digest 去重/build-id 排序/版本满足+base-digest 硬谓词/多余项容忍/旧镜像保留), D018+D023 (home 复刻: skills 全量 COPY, ~/.pi/agent 机械复制, auth.json 不烤层/sessions 不进容器, ~/AGENTS.md 与 ~/docs 不进容器), D019 (auth 风险文档明示), D020 (base 仅用户明说更新)
- `../milestone-05/MILESTONE-05-findings.md` (label/命名/digest 事实)
- M03 镜像契约: `../../../../../workflow/use-sandbox-worktree/image/Containerfile` (sshd 前台主进程/agent 用户) 与 `../TECHNICAL.md` 架构节

## 执行(Execution)

- [x] 已实现

## 要构建什么

`workflow/use-sandbox-worktree/scripts/image-prep.py` (uv run python, 单文件, 无仓库内新依赖): 三个子命令.

- `build-base`: 生成 base 层 Containerfile (D014: OS + pi CLI + skill 库全量 + fd/rg + uv; D023: 无 ~/AGENTS.md ~/docs; 门禁类扩展不进容器) → 预 build → 逐条目容器内实测版本 → contents.md → 二次 build (层缓存, 仅加 label/tag: schema-version/contents-digest/build-id) → 记录落 `<records-root>/base/builds/<build-id>/` (Containerfile/requirements.md/contents.md/build.json + context/). context staging 排除 auth.json/sessions (D018).
- `match`: project-id=主仓绝对路径 → `podman images --filter label=run.sandbox-worktree.project-id=<id>` 取候选 → digest 去重 → build-id 降序 → 逐候选判: 记录在案 + contents.md sha256 == label contents-digest + 每条需求版本满足 (含谓词) + base-digest == 当前 base (硬谓词) → 首个全过 = REUSE; 全不过 = BUILD-NEW 并列 reason. 旧镜像保留不删 (D017). 多余项容忍.
- `build`: 解析 requirements.md (条目=名称+版本谓词, 可带 install=/probe= 指令) → 解析当前 base (按 reference 取 build-id 最新, 无则退出码 2) → 生成项目层 Containerfile (FROM base@digest + install 指令按序, 稳定在前常变在后由清单作者保证, 生成器保序) → 预 build → 逐条目实测 (probe 缺省 `<name> --version`, 取首个版本 token) → 谓词全满足否则退出码 1 VERIFY-FAIL → contents.md + sha256 → 二次 build 加全部 label (project-id/schema-version/contents-digest/build-id/base-digest, D024) + tag `<prefix>/<slug>:<build-id>` → 记录 + build.json.

端口契约落镜像: 容器内端口固定 EXPOSE 22/8800/6080, 宿主端口不钉 (M07 里程碑; 宿主侧动态分配属诞生流程, 不在本 ISSUE). 容器 label (identity/worktree-path/image-digest) 属诞生流程, 本 ISSUE 不落地 (无权威容器创建输入).

## 最小接缝补钉 (权威输入未钉死, 待用户追认)

权威输入未回答处, 取最小实现并在产物报告登记, 不造大接口:

1. requirements.md 行格式: `<name>[<op><version>] [key=value...]`, shlex 切分, `#` 注释; 谓词集 = `>= <= > < ==` + 裸名称 (存在性); install=/probe= 值可加引号含空格. 依据: D015 例 `node>=20`; install= 是 "Containerfile 由分析结果生成" 的最小机械通道 (清单作者=host llm).
2. 探测缺省 `probe="<name> --version"`, 解析输出首个 `v?\d+(\.\d+)*` token, 不看退出码 (sshd -V 式).
3. 版本比较: 点分整数元组, 缺位补 0, `v/V` 前缀剥离; 不可解析 = 不满足.
4. 镜像 reference 前缀 `--prefix` (缺省 `localhost/sandbox-worktree`, M05 推荐), base `--base-ref` (缺省 `<prefix>/base`); 测试经前缀隔离用户镜像存储.
5. build-id = tag 同格式 `YYYY.MM.DD-<当日序号>` (D015), 分配在 records-root 锁内查重即建目录占位 (D024 防并发同号).
6. build.json (kind/project-id/slug/build-id/image-ref/digest/base-ref/base-digest/contents-digest/label-keys/created) 是记录目录的机器可读索引 — D024 未禁额外文件, slug 冲突判定 (D024) 需要它.
7. slug 复用 use-worktree slug.py 单参数形态 (M03 已验证契约); 冲突后缀 = slug + `-` + sha1(project-id)[:8]; `base` 为保留 slug.
8. contents.md 行格式 `<name>: <version>`, `#` 头部; contents-digest = 文件字节 sha256. 二次 build 利用层缓存仅改 config (M05: label 不可原地改).

## 允许范围

- 新建 `workflow/use-sandbox-worktree/scripts/image-prep.py`, `tests/test_swt_m07.py`
- 本 ISSUE 文件与产物 `../milestone-07-image-prep-run.md`
- /tmp 测试夹具; 测试经 `--prefix localhost/swt-m07-*` 与 `--records-root /tmp/...` 隔离用户存储
- 只读调用 `workflow/use-worktree/scripts/slug.py`

## 禁止范围

- 不改 M03 契约: `e2e-smoke.py`, `image/Containerfile`, `tests/test_swt_m03.py` 不动
- 不改 roadmap 任何状态文件; 不触碰其他 skill 与用户真实仓库
- 不做容器创建/容器 label/动态宿主端口分配 (无权威输入, 诞生流程属 M11)
- 门禁类扩展 (filesystem-operation-gate/git-operation-gate/python-operation-hook/repetition-guard) 与 ~/AGENTS.md ~/docs 不进任何生成产物 (D014/D023)
- 不删任何旧镜像 (D017); base 不自动重建 (D020)

## TDD 切片

- TS-001 谓词与清单解析 (单元): 满足矩阵/指令引号/坏行报错.
- TS-002 build-id 分配与 slug/project-id (单元, /tmp): 序号递增/占位/冲突加 hash/base 保留.
- TS-003 Containerfile 生成审计 (单元): base 含 pi/fd/rg/uv/EXPOSE 22 8800 6080/sshd 契约/uv sync; staging 排除 auth.json/sessions; 无门禁扩展名; project 层 FROM base@digest + install 保序.
- TS-004 match (端到端, scratch 镜像): REUSE 最新/base-digest 硬谓词/谓词不满足/多余项容忍/记录篡改跳过.
- TS-005 build 流 (端到端, alpine 伪 base): 全链成功 + 记录四件套 + label 一致 + 再 match REUSE; 谓词失败退出码 1 不打 tag.
- TS-006 build-base 真构建 (端到端, 网络重): 真实 skills/pi-agent 目录 staging, pi 实测, sshd/EXPOSE 契约, auth.json 不落 context.

## 验证入口

`uv run --with pytest pytest tests/test_swt_m07.py` 全绿; `uv run --with pytest pytest tests/test_swt_m03.py` 回归全绿 (M03 契约未破坏).

## 停止条件

需要改动 D014-D024 语义或扩大允许范围时停止上报.
