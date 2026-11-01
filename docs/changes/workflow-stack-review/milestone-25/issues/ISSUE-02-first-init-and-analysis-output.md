## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已完成
- [ ] 派工前复核并记录 (写在本行下方): HEAD 提交号; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数; `workflow/codebase-map/` 当前存在哪些文件.

## 要交付什么
让 `build` 真的能把目标库分析成数据原件:

- `workflow/codebase-map/scripts/codemap_analyze.py`: 首次初始化 (只在缺失时做) 与三步分析, 产出写进目标库 `.codebase-map/cc.json`.
  - 初始化: `podman pull` 镜像 (本地已有则跳过) -> 校验 `RepoDigests` 含单架构清单 digest `sha256:286b0a54...`, 不含则 `image_digest_mismatch`, 多架构清单 digest `sha256:6402a87f...` 只记录进 `cache/cache.json` 不阻断 -> 下载官方 `web.zip` (`vis-2.9.1`) 到 `cache/frontend/vis-2.9.1/`, 校验 sha256 `18b6377f...`, 不过则 `frontend_hash_mismatch`; 下载不到则 `frontend_unavailable` -> 解包到 `unpacked/` 再整体同步进 `serve-root/` (版本升级整体替换, 不叠加旧产物).
  - 三步分析, 每条一次 `podman run`, 各自一份日志: 1 `ccsh dependencyparser /proj -o /out/deps.cc.json -nc -e <排除正则>`; 2 `ccsh unifiedparser /proj -nc -o /out/metrics.cc.json`; 3 `ccsh merge /out/metrics.cc.json /out/deps.cc.json -o /out/cc.json -nc`. 固定参数 `--rm --network=none --userns=keep-id -v <target>:/proj:ro -v <cache/work>:/out`, 不用 `--privileged`, 不挂 docker socket, 不映射端口. 中间产物留 `cache/work/` 供复查, 下次运行覆盖.
  - 产出: 写 `<target>/.codebase-map/cc.json` (内容即 merge 产物, 不改字段, 不注入自造指标); 同库重跑覆盖同一路径, 不保留历史版本.
  - `cache/cache.json` 字段: `{image:{tag, single_arch_digest, multi_arch_digest, verified_at}, frontend:{version, zip_sha256, unpacked_at}, excluded_globs:[...], written_at}`; 前端版本或镜像变更时整体重写.
- `codebase-map.py` 的 `build` 接上分析流水线: `--json` 输出补 `initialization:{performed, notice?, steps:[...]}`, `duration_seconds`, `cc_json_path`, `target`, `key`; `performed` 为真时 `notice` 必须存在, 内容说明拉镜像与取官方前端属首次初始化的慢操作. 门禁与统计字段由 ISSUE-03 补.
- 新测试树补本 issue 用例 (含本地 stub `podman` 脚本, 只在测试临时目录里, 不入仓库).

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-25/PRODUCT.md`, AC-001 (首次初始化说明字段 + 目标库出现 `.codebase-map/cc.json`), AC-007 (单架构 digest 不匹配时停下; 环境不足报错停下); BR-016, BR-017, BR-021, BR-026 (Java 目标库), BR-027 (build 负责初始化), BR-028, BR-031; G-001, NG-003, NG-005.
- Technical: `docs/changes/workflow-stack-review/milestone-25/TECHNICAL.md`, 模块划分 (`codemap_analyze.py`), 模块接口 (`build` 前置与 `build --json` 字段, 分析与产出 全节, 首次初始化与 digest 口径), 接缝与依赖 (进程接缝 stub 的边界, 网络接缝, 文件接缝), 安全策略 (分析隔离, 目标库完整性).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-25/DECISIONS.md`: D009, D012, D013, D016, D019, F001, F004, F005.
- `docs/changes/workflow-stack-review/milestone-24/DECISIONS.md`: U002, F001, F002, F003, F004, F006.
- `docs/changes/workflow-stack-review/milestone-13/DECISIONS.md`: D003, D005, D030.

## 允许范围
同全局, 增量: 本 issue 只落 `codemap_analyze.py` 的初始化与分析两段与 `build` 的接线, 以及相应测试.

## 禁止范围
- 不实现门禁判定, 统计, 副本复制与 `state.json` 更新 (留给 ISSUE-03); 本 issue 的 `build --json` 里这几项字段先不出现, 不写假值.
- 不降级: 镜像取不到, digest 不符, 前端取不到, sha256 不符一律停下, 不拿旧产物冒充当前版本, 不用本机已有的其它前端产物顶替.
- 不自算层号, 环, 向上依赖, 不改 merge 产物字段, 不注入自造指标.
- 不写 `--privileged`, 不挂 docker socket, 不映射端口, 不把源码目录挂成可写.
- 不在仓库内留任何 `.cc.json`, `web.zip`, 前端解包产物与私有库路径 (证据放 `/tmp/m25-02/`).

## 代码定位提示
- 从零新建 `workflow/codebase-map/scripts/codemap_analyze.py`; 子命令接线在 `codebase-map.py` 的 `build` 分支.
- 既有形状参照: `workflow/navigate/scripts/web_server.py` 的子进程启动与日志落盘写法; `workflow/navigate/scripts/roadmap.py` 的 `--json` 单行输出; 上一 issue 的 `codemap_common.py` (排除集与正则转换, 版本常量, 运行时目录) 必须复用, 不另写一份.
- 运行配方事实来自 `docs/changes/workflow-stack-review/milestone-23/PROBE.md` 6.1 (uid 映射与 `--userns=keep-id`), 6.2 (dependencyparser 实测), 6.3 (官方管道损坏, 改用 unifiedparser 出文件再 `ccsh merge`).
- 测试接缝: `codebase-map.py` 带连字符不能 import, CLI 层用 `subprocess`; stub `podman` 脚本放 `tmp_path` 并只通过 `PATH` 注入子进程环境.

## 验证契约
- 变更类型: 行为变更.
- 对应范围: `build` 的初始化与分析流程, `podman run` 参数构造, 中间产物与原件落点, 失败出口.
- 验证要求/证据: 用本地 stub `podman` 覆盖参数形状与流程接线 (证据里必须写明是 stub, 不得当作分析可用证据); 真实分析, 真实 digest inspect, 真实首次初始化 (拉镜像与下载) 只能在宿主执行, 由 ISSUE-07 承接, 缺环境记未验证.

## 验证入口
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests`; 通过标准 退出码 0 且无 failed. 本 issue 新增用例:
  - TC-02-01 (BR-017 观察点): stub `podman` 记录 argv, 断言三次调用都带 `--rm`, `--network=none`, `--userns=keep-id`, 源码挂 `:ro`, 出目录挂 `cache/work`, 且没有 `--privileged`, 没有 docker socket 挂载, 没有 `-p`/`--publish`.
  - TC-02-02: 三次 ccsh 步骤顺序与参数 (第一步带 `-e <排除正则>`, 第二步 `unifiedparser -o`, 第三步 `merge` 两个输入顺序为 metrics 在前 deps 在后), 中间产物落在 `cache/work/` 且第二次运行覆盖.
  - TC-02-03: 本地镜像与前端产物齐备时不进初始化 (`initialization.performed == false`, 无 `notice`), `steps` 为空或标明跳过; `cache/cache.json` 字段齐全且 `frontend.version == "vis-2.9.1"`, `image.tag` 与两个 digest 为题目给定值.
  - TC-02-04: 同一目标库连跑两次, `.codebase-map/cc.json` 被覆盖且路径不变, `key` 不变, `cache/work/` 不出现历史版本文件.
  - TC-02-05: 跑完整 build (stub) 后对目标库做全量文件名与内容哈希比对, 只多出 `.codebase-map/cc.json`, 其它文件未变 (BR-031 的容器内部分).
  - TC-02-06: digest 口径纯函数, `RepoDigests` 含单架构 digest 时通过; 只含多架构 digest 时阻断并返回 `image_digest_mismatch`; 两者都含时通过且多架构值只进 `cache/cache.json`.
  - TC-02-07: 预置伪前端产物 (文件接缝本地可替换) 且 sha256 与常量不符 -> `frontend_hash_mismatch` 且停下; 断言此时不写目标库, 不把旧产物复制进 `serve-root`.
- 未自动化的部分与理由: `initialization.performed == true` 与 `notice` 文案需要真实拉镜像与下载 `web.zip` (网络接缝), 容器内没有出网也不该造替身, 由 ISSUE-07 宿主首次运行证据承接; `podman_missing`/`image_unavailable` 同理属宿主构造场景.
- 通过标准 (整体): 上述每条成立; stub 用例的输出里能看到完整 argv; 原件字段与 merge 产物逐字节一致 (不解包改写).

## 交付证据

## 风险提示
- stub `podman` 只能证明参数构造与流程接线, 不能证明分析可用; 证据里若混写会被判为伪造通过.
- 首次初始化要整体替换 `serve-root` 里的前端产物, 直接叠加会留下旧版本文件; 测试用两版伪产物覆盖这条.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 需要为通过失败出口而放宽 digest/sha256 校验时停止并上报.

## 验收标准
- [ ] 有本地镜像与前端产物时 `build` 不走初始化, `initialization.performed` 为 false.
- [ ] 三次 `podman run` 参数与隔离要求逐条符合 BR-017, 不含提权与端口映射.
- [ ] 目标库只多出 `.codebase-map/cc.json`, 内容未被改写或注入自造指标.
- [ ] 单架构 digest 不符与前端 sha256 不符都阻断并停下, 不降级.
- [ ] 同库重跑覆盖同一路径, 不留历史版本.

## 被阻塞于
- `ISSUE-01-shared-rules-and-cli-contract.md`
