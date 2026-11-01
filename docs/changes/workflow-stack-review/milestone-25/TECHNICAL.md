# codebase-map v1 Technical Spec

## 模块划分

- `workflow/codebase-map/SKILL.md` (新增): 唯一操作文档. 责任: 三子命令用法与例子 (含 `serve --port` 与 `serve --address` 用法), 地址来源与缺值出口, 交付消息必须带的说明 (层号在哪看 / 完整性未量化 / 分母口径), 失败出口清单, 状态复原步骤, 数据副本清理入口与"不自动删除"说明, 前端与分析端版本说明. 删除测试判定: 文档不承担实现复杂度, 但删掉它会让每个调用会话各自发明用法与交付话术, 所以保留.
- `workflow/codebase-map/agents/openai.yaml` (新增): codex 侧的调用策略, 内容固定为最小 `policy.allow_implicit_invocation: false`. 与 frontmatter 的 `disable-model-invocation: true` 配对, 受仓库 `tests/test_skills_codex_metadata.py` 守卫.
- `workflow/codebase-map/scripts/codebase-map.py` (新增): CLI 入口. 责任: 三个子命令的参数解析, 编排下面三个模块, 输出人类可读摘要或 `--json` 单行 JSON, 决定退出码. 藏住: 子命令之间的先后与前置检查顺序. 删除测试判定: 删掉后每个调用会话都要自己拼命令与解释错误码, 复杂度散回调用点, 保留.
- `workflow/codebase-map/scripts/codemap_common.py` (新增): 共享常量与纯函数. 责任: 数据键命名 (库名清洗 + 路径哈希), 运行时目录解析, 排除规则集合, 已确认地址读取与候选探测, JSON 输出编码, 版本与校验常量 (镜像 tag, 单架构 digest, 前端 sha256, 默认端口). 藏住: 命名与地址规则的全部细节. 删除测试判定: 这些规则被三个模块共用, 删掉会复制三份且必然漂移, 保留.
- `workflow/codebase-map/scripts/codemap_analyze.py` (新增): 分析与产出. 责任: 首次初始化 (镜像与官方前端), 构造并执行三次 `podman run`, 合并指标, 计算门禁与统计分母, 写目标库 `.codebase-map/cc.json`, 复制副本进 serve-root 并更新 `state.json` 的数据键清单. 藏住: podman 参数形状, 三个 ccsh 步骤的衔接, 统计口径与零声明文件定性. 删除测试判定: 删掉后 CLI 里会塞进 podman 调用与统计, 分析口径分散, 保留.
- `workflow/codebase-map/scripts/codemap_service.py` (新增): 常驻服务与运行时状态. 责任: 运行时目录与文件锁, `state.json` 读写与真实探活, 端口决策, HTTP 静态服务进程 (前台函数 `serve_forever` 与守护子进程启动), 显式停止. 藏住: 锁协议, 探活三步判定, 子进程回收. 删除测试判定: 删掉后单例, 探活与端口纪律要重新落到调用点, 保留.
- `workflow/codebase-map/tests/` (新增): 行为回归. 责任: 键命名与清洗, 排除集合与统计口径, 状态读写与三步探活, 端口被占与显式换端口, 单例与并发, 服务根越界与根外软链, 地址缺口, CLI 输出形状, "脚本只 import 标准库"的静态守卫, 以及"仓库内不存在 cc.json 与前端产物"的静态守卫 (BR-035).
- `general/writing-for-llm/check_skill.py` (不改, 但列入验证入口): 新增 SKILL.md 必须过一次 `check_skill.py`, 检查 name 与目录名一致, description 单行等硬约束.
- `pytest.ini` (改): `testpaths` 在 `tests` 之前追加 `workflow/codebase-map/tests`, 遵守文件内 conftest 预载顺序注释.
- `README.md` (改): 工作流技能表加一行 `codebase-map`.
- 目录边界: `workflow/codebase-map/`, `pytest.ini`, `README.md`. 不碰 `general/`, 其它 `workflow/` 子目录, 仓库根 `tests/`, `docs/changes/workflow-stack-review/roadmap/ROADMAP.json`.
- 本节点已完成、m26 不再改动: `docs/language/UBIQUITOUS_LANGUAGE.md` 的"结构地图"/"结构地图服务"/"数据键"词条与 `docs/adr/0026-codebase-map-host-resident-service.md` 的适配指针 (m25 D011).

## 模块接口

### CLI `scripts/codebase-map.py`

- `build <目标目录> [--exclude <glob>]... [--json]`: 分析与产出. 前置: 不在容器内 (`/run/.containerenv` 不存在), 目标目录存在且是目录, `podman` 可用. 成功输出并返回 0; 失败输出错误码并返回 1.
- `serve [--port <N>] [--address <IP>] [--json]`: 起或复用常驻服务并交付 URL. `--port` 指定本次端口: 没有存活实例时生效 (首次运行也可以), 有存活实例时返回 `instance_running` 要求先 `stop`. `--address` 把用户确认过的局域网地址传入本次调用, 只影响本次 URL 组装与交付文案, 不落盘. 前置: 状态清单与磁盘副本的交集非空 (否则 `no_data_keys`, 区分"还没 build"与"副本已删"); 地址来源解析不出且未传 `--address` 时给 `address_missing`, 服务照常起, 不返回 `url`.
- `stop [--json]`: 停整个服务并清 `state.json`; 没有实例时幂等成功.
- 输出形状: 默认 stdout 为人类可读多行摘要; `--json` 时 stdout 只有一行 JSON. 两种形态字段一致, 便于测试与人工共用同一份数据. `--json` 与具体字段名是为可核对而定的实现选择, 可调整, 但字段语义不得丢.
- 全局环境变量: `CODEMAP_RUNTIME_DIR` 覆盖运行时基目录 (默认 `~/.agents/codebase-map`, 供测试隔离); `CODEMAP_PORT` 覆盖首选端口 (默认 8090, 只供隔离测试). 两者都是实现选择, 可调整; `CODEMAP_PORT` 不构成 BR-004 的换端口入口, 换端口只走 `serve --port`.
- 调用式 (写进 SKILL.md): `python3 <skill 目录>/scripts/codebase-map.py <build|serve|stop> ...`; 宿主有 uv 时 `uv run python ...` 等价.
- 错误码 (成功为 `success: true`): `container_not_supported`, `target_missing`, `podman_missing`, `image_unavailable`, `image_digest_mismatch`, `frontend_unavailable`, `frontend_hash_mismatch`, `gate_failed`, `no_data_keys`, `port_in_use`, `instance_running`, `state_mismatch`, `stop_failed`, `internal_error`.
- 不变式: 单次调用只有一个进程改动运行时状态 (文件锁); 除 `build` 写的 `.codebase-map/cc.json` 外不改目标目录; 所有错误都在退出前落到 stderr 摘要或 JSON 的 `error` 字段, 不静默成功.

`build --json` 字段: `{success, command:"build", target, key, cc_json_path, serve_copy_path, gate:{passed, edges, level_kinds, reason?}, stats:{scanned_files, files_in_tree, excluded:{tests, build_dirs, custom, dot_codebase_map, tool_defaults}, zero_declaration:[{path, reason}], unsupported_extensions:[{ext, count}], cyclic_edges, upward_edges}, initialization:{performed, notice?, steps:[...]}, duration_seconds}`. 门禁失败时 `stats` 与 `initialization` 照常完整输出, 不因失败而省掉分母与零声明清单. `initialize.notice` 在 `performed` 为真时必须存在, 内容说明拉镜像与取官方前端属首次初始化的慢操作.

`serve --json` 字段: `{success, command:"serve", url?, base_url?, port, bind:"0.0.0.0", reused, pid?, serve_root, port_changed?, previous_url?, address_source?, keys:[{key, url?, built_at, bytes}], delivery_notes:{level_hint, integrity_note, denominator_note}, address_missing?:{code, message}, candidates:[addr...]}`.
- 地址解析成功 (含通过 `--address` 传入的确认值): 给 `url`/`base_url`, `keys` 每项带完整可点 URL, `address_source` 标记取自记录文件还是本次参数.
- 地址解析失败且未传 `--address`: 不给 `url`/`base_url`, `keys` 每项只给 `key`; stdout 为人类可读模式时首行写 `BLOCKED: 缺已确认局域网地址`, 退出码仍为 0 (服务已起, 阻断的是交付而不是启动).
- `delivery_notes` 是交付消息的唯一内容来源: `level_hint` = 层号/环/向上依赖在官方依赖视图看; `integrity_note` = 依赖抽取完整性未量化; `denominator_note` = 本次依赖树文件数与分母口径. 调用会话原样转述, 不自己改写数字.
- `port_changed` 与 `previous_url` 只在本次通过 `serve --port` 显式换端口时出现, 用于报告旧地址已失效.
- `keys` = `state.json.data_keys` 与 `serve-root` 里实际 `.cc.json` 文件的交集, 输出前逐个核文件存在; 记录里有而磁盘缺失的键不进 `keys` 并提示; 磁盘上有而记录里没有的 (手工放入) 只提示存在未登记文件, 不自动收编 (m25 D020).
- `no_data_keys` 文案分两种: 清单与磁盘都空 = 还没执行过 build; 清单有条目但副本全缺 = 副本已被删, 建议重新 build.

`stop --json` 字段: `{success, command:"stop", stopped, pid?, port?}`.

### 数据键与命名 `codemap_common.py`

- `data_key(target_dir) -> str` = `<库名>-<哈希8>.cc.json`. 库名 = `realpath(target).name`, 空白与 `[^A-Za-z0-9._-]` 逐个替换为 `-`, 连续 `-` 折叠, 去首尾 `-`, 空则 `repo`; 哈希 = `sha256(realpath(target) 的 utf-8 字节).hexdigest()[:8]`. 不变式: 同一目标目录恒得同一键; 不同 realpath 键不同; 键只含 `[A-Za-z0-9._-]`.
- 排除集合: 默认 `node_modules`, `.git`, `dist`, `build`, `target`, `vendor`, `.codebase-map`; 用户 `--exclude` 追加. 同一集合同时喂给 ccsh (`-e` 正则) 与宿主侧目录树扫描, 两处口径必须来自同一份数据.
- 版本常量: 镜像 `docker.io/codecharta/codecharta-analysis:2.3.0`; 单架构清单 digest `sha256:286b0a54f947c412b7c290a57312ac2c4327352531e046ad4ab834c13b2ddc36`; 多架构清单 digest `sha256:6402a87f6823c8123de6c8706ffc7b68ae75ce2c2c58aa8b3fcab59e97d1f7a4` (只记录); 前端 `vis-2.9.1` 的 `web.zip` sha256 `18b6377f9f482c3e34dd9a3ab8a716d6a7171ad68fa2d6670a516761b0be3682`; 默认端口 8090; 绑定地址 `0.0.0.0`.
- 运行时目录: `runtime_dir = $CODEMAP_RUNTIME_DIR or ~/.agents/codebase-map`; 子目录 `serve-root/`, `cache/`, `logs/`; 文件 `state.json`, `lock`, `cache/cache.json`. 目录 0700, 文件 0600.

### 地址解析 `codemap_common.py`

- 输入: `~/.agents/sandbox-worktree/lan-address` (只读; 路径按 swt 默认 records_root 规则解析, 不新建来源), 网卡枚举 (`ip -o -4 addr show scope global`, 过滤隧道/虚拟接口前缀).
- 顺序: `--address` 参数 (本次显式传入的确认值) → 已确认文件有值就用它 → 否则枚举非隧道全局 IPv4 作为 `candidates` 返回 `address_missing.code=no_confirmed_address`, 由调用会话请用户确认 → 用户确认后调用会话重跑 `serve --address <IP>`, URL 仍由 serve 组装并输出. `--address` 只作用于本次调用, 不写 `state.json`, 不新建配置文件, 不回写 swt 的 lan-address (m25 D017).
- 明确不采: `SSH_CONNECTION`, 主机名, `localhost`, 服务自报地址.
- 错误模式: 解析失败不是启动失败; 服务照常监听, 只给缺口与候选.

### 分析与产出 `codemap_analyze.py`

- 首次初始化 (仅缺失时): `podman pull` 镜像 (有本地镜像则跳过) → 校验 `RepoDigests` 含单架构清单 digest, 不含则 `image_digest_mismatch` → 下载官方 `web.zip` 到 `cache/frontend/vis-2.9.1/`, 校验 sha256, 解包到 `cache/frontend/vis-2.9.1/unpacked/` 再整体同步进 `serve-root/` (版本升级时整体替换, 不叠加). 任何一步失败 (含无网络) 都停下, 不降级, 不拿旧产物冒充; `serve` 与 `stop` 不做网络动作.
- digest 口径: 阻断项是单架构清单 digest `sha256:286b0a54...`; 多架构清单 digest `sha256:6402a87f...` 只记录进 `cache/cache.json`, 不阻断. 这是对 m24 U002 "以 manifest digest 为准" 的字段细化, 不是取消该要求 (m25 D016).
- `cache/cache.json` 字段: `{image:{tag, single_arch_digest, multi_arch_digest, verified_at}, frontend:{version, zip_sha256, unpacked_at}, excluded_globs:[...], written_at}`. 前端版本或镜像变更时整体重写.
- 分析三步, 每条一次 `podman run` (各自一份日志):
  1. `ccsh dependencyparser /proj -o /out/deps.cc.json -nc -e <排除正则>`
  2. `ccsh unifiedparser /proj -nc -o /out/metrics.cc.json`
  3. `ccsh merge /out/metrics.cc.json /out/deps.cc.json -o /out/cc.json -nc`
  固定参数: `--rm --network=none --userns=keep-id -v <target>:/proj:ro -v <cache/work>:/out`. 不用 `--privileged`, 不挂 docker socket, 不映射端口. 中间产物留 `cache/work/` 供复查, 下次运行覆盖.
- 门禁 (在写副本前判定): `edges = len(lenses.dependency.edges.dependencies)`; `level_kinds = 文件节点 (type=File) 上 level 的取值种数`. 通过条件: `edges > 0` 且 `level_kinds >= 3`. 不通过时仍写目标库 `.codebase-map/cc.json`, 不复制副本, 返回 `gate_failed` 并在 `gate.reason` 写明是边为 0 还是层号种数不足.
- 统计: `scanned_files` = 宿主侧按排除集合扫出的受支持源码文件数; `files_in_tree` = cc.json 中 `type=File` 节点数; `zero_declaration` = 落在扫描范围但不在依赖树的文件及原因 (测试目录, build 目录, 自定义排除, 零声明); `unsupported_extensions` = 扫描到但 ccsh 不产出依赖的扩展名及计数; `cyclic_edges`/`upward_edges` = `isCyclic` / `isPointingUpwards` 为真的边数.
- 产出: 写 `<target>/.codebase-map/cc.json` (内容即 merge 产物, 不改字段, 不注入自造指标) → 复制到 `serve-root/<key>` (先写临时文件再 `os.replace`) → 更新 `state.json.data_keys` (锁内). `build` 不删除任何其它库的副本.
- 幂等: 同库重跑覆盖同一路径与同一键; 不保留历史版本.

### 常驻服务与状态 `codemap_service.py`

- `state.json` 字段: `version` (当前 1), `port`, `last_port`, `last_url`, `pid` (停机后为 null), `bind` ("0.0.0.0"), `started_at` (UTC ISO8601), `stopped_at` (停机时间, 未停为空), `command_path` (脚本绝对路径), `serve_root`, `log_path`, `runtime_dir`, `data_keys` (每项 `{key, source_cc_json, built_at, bytes}`). 原子写 (临时文件 + rename), 0600. `last_port`/`last_url` 与 `stopped_at` 让"已知停机"和"实例死掉的残留"可区分, 也是换端口时报告真实旧地址的依据 (m25 D018).
- 探活 (三步全过才算存活): `os.kill(pid, 0)` 不抛错 → 能连上 `127.0.0.1:<port>` → `GET /` 返回 200. 任一步失败即判死; `state.json` 存在本身不算存活.
- 判定分支: pid 不存在 = 旧实例已死, 可按原端口重起; pid 存活但端口无人应答, 或端口上的监听者不是本服务 = 状态不一致 (`state_mismatch`), 报错不接管也不重起.
- 端口决策: 目标端口 = `--port` 实参, 否则 `state.json.last_port`, 否则首选 8090 (m25 D018). 判定顺序: `pid` 为 null 且有 `stopped_at` = 已知停机, 直接按目标端口起; 探活通过则复用 (不换端口, 不再起进程; 此时传了不同的 `--port` 返回 `instance_running`); `pid` 存活但端口不通, 或端口上的监听者不是本服务 = `state_mismatch`, 报错不接管; `pid` 不存在 = 旧实例已死, 目标端口空闲就按它重起并报告"旧实例已死", 被别的程序占用则 `port_in_use` 报错交用户裁决, 不静默顺延.
- 换端口: 目标端口与 `last_port` 不同且成功启动时, 输出 `port_changed=true` 与 `previous_url` (由 `last_url` 或旧端口加当前地址拼出), 并写明旧地址已失效; 新端口写入 `port` 与 `last_port`.
- 文件锁: `runtime_dir/lock` 的 `flock(LOCK_EX)`, 覆盖 serve 启动/复用, build 的副本复制与 `data_keys` 更新, stop 全过程. 拿不到锁时等待上限 30 秒, 超时 `internal_error`.
- HTTP 面: `ThreadingHTTPServer` 绑定 `0.0.0.0:<port>`, 只读静态服务 `serve_root`; 路径先 `resolve()` 再判 `relative_to(serve_root)`, 根外路径与根外软链一律 404; 不做目录 listing; 不做 HTML5 回退 (官方前端是 hash 路由); 不提供上传/写接口.
- 子进程: 守护进程以 `python3 <脚本> _serve-daemon` 形式 `start_new_session=True` 启动, stdout/stderr 追加到 `logs/service.log`; 父进程轮询端口就绪 (上限 10 秒) 后写 `state.json`. `_serve-daemon` 是内部隐藏入口, 不是对外子命令, 不写进 SKILL.md 用法. 锁等待上限 30 秒, stop 等 10 秒后仍活着则报 `stop_failed` (不自动 SIGKILL); 这几个时长都是实现选择, 可调整.
- `stop`: 锁 → 读 state → 探活 → `SIGTERM` → 等 10 秒 → 仍在则 `stop_failed` (不自动 SIGKILL) → 把 `pid` 置 null, 写 `stopped_at` 保留 `port`/`last_port`/`last_url`, 清除锁文件; 保留 `serve-root/` 与 `cache/`. 不清整个 `state.json`, 否则换端口时无从知道旧地址 (m25 D018).
- 复原: 删除 `runtime_dir` 等于放弃当前实例; 文档写明复原 = 重新 `serve` (数据副本若还在则原地复用) 或重新 `build` (数据副本重建).

## 接缝与依赖

- 内部接缝: `codebase-map.py` → `codemap_analyze` / `codemap_service` / `codemap_common` 的函数调用, 分类: 内部. 测试可直接 import 三个 `codemap_*.py` 模块并注入临时目录与假参数; 入口脚本 `codebase-map.py` 带连字符不能当模块名, CLI 层用 subprocess 调用.
- 进程接缝: `podman` 命令行, 分类: 真正外部 (镜像内容与 ccsh 行为不可替身). 测试可用本地可替换的 stub 脚本核对参数构造 (排除集, `--userns=keep-id`, `--network=none`, `:ro`, `--rm`), 这份 stub 测试就是 BR-017 的观察点, 但它不是"分析可用"的证据; 分析结果类验收只能由宿主真实运行提供.
- 验证分工 (m25 D016): 容器内可执行的是不需要 podman 的那部分: 键命名与清洗, 排除集合, 地址解析, 状态读写与三步探活, 单例与并发, 端口被占与显式换端口, 服务根越界, CLI 输出形状, 两道静态守卫. 只能在宿主执行的是: 真实库 build 与门禁统计, 真实 3D 与依赖视图渲染, 局域网设备打开, 长期常驻. 后者缺环境时记未验证, 不用 stub, 截图或本机 curl 顶替; 具体的 issue 与证据形式在 m25 `EXECUTION.md` 的验证策略与各 issue 验证入口里定.
- 网络接缝: 首次初始化拉镜像与下载 `web.zip`, 分类: 远程但自有 (官方 registry 与 GitHub release). 只在 build 首次初始化时触碰; 失败即停.
- 文件接缝: `~/.agents/sandbox-worktree/lan-address` (只读, 分类: 本地可替换), 被分析目标目录 (分类: 本地可替换), 运行时目录 (分类: 本地可替换, 测试用 `CODEMAP_RUNTIME_DIR` 隔离), `cache/frontend/` 里的 `web.zip` (分类: 本地可替换, 测试可放伪产物并预置 sha256 期望值).
- 用户设备访问: 分类: 真正外部, 无法替身. 证据必须是局域网设备的真实请求.
- 跨 skill 依赖: 无. 本 skill 不被任何 skill 调用, 也不 import 其它 skill 的代码.

## 安全策略

- 传输与访问: 无认证, 无 TLS, 绑定 `0.0.0.0`, 已接受; 局域网内主体可读 `serve-root` 全部内容 (官方前端与本次结构数据). 不做访问控制, 以"只分析愿意公开的库"这条使用纪律守住暴露范围, 写在 SKILL.md.
- 分析隔离: 源码只读挂载 (`:ro`), `--network=none`, `--userns=keep-id`, `--rm`, 不提权, 不挂 docker socket, 不映射端口; 容器只写宿主的 `cache/work/`.
- 目标库完整性: 除 `.codebase-map/cc.json` 外不写目标库; 不执行目标库里的任何脚本; 不读取目标库的 `.env`, 密钥文件等非源码内容.
- 越界防护: 静态服务先规范化再判归属, 根外路径与根外软链 404; 不提供写接口.
- 数据与隐私: 运行日志含库名与相对文件名, 不含源码内容; `state.json` 与日志 0600, 运行时目录 0700; 仓库内不写被分析库的完整路径 (证据脱敏).
- 停止与清理: 只由显式 `stop` 停止; 不停止或接管其它 skill 的服务 (present 与 navigate 各有自己的运行时目录); 测试一律用隔离运行时目录与独立端口.

## 非功能要求

- 单例与并发: 同一运行时目录下并发两次 `serve` 只产生一个实例, 只有一个进程在听端口, 两次输出同一个 `port` 与同一个 `url`. 验证口径: 并发调用后的 `state.json` pid 唯一, `pgrep -f _serve-daemon` 计数为 1, 两次调用 `reused` 一次为 false 一次为 true.
- 常驻性: 调用返回后服务持续可用; 不设空闲退出. 验证口径: 隔一段真实时间后再次 `GET /` 仍 200, 且 `serve` 复用它而不是新起.
- 状态真实性: 伪造的 `state.json` (pid 不存在 / 端口无人听 / HTTP 无响应) 必须判死并按复原流程处理, 不能因为 JSON 在而认为存活.
- 交付一致性: 输出 `url` 的端口等于 `state.json.port` 等于实际监听端口; `keys[].key` 等于 `serve-root` 里实际存在的文件名; `keys[].url` 拼的是同一地址与同一键.
- 口径归因: 分析用的排除集与统计扫描用的排除集来自同一份数据且同一套 glob→正则转换; 因分析端还有自带忽略规则, 不宣称逐文件相等, 改要求差值能逐类归因 ( `stats.excluded` 五类与 `zero_declaration` 之和能与 `scanned_files` 对账).
- 可诊断: 每个失败都有稳定错误码, 非 JSON 模式下 stderr 说清下一步动作 (先 build / 处理端口占用 / 装 podman / 补网络); build 记录耗时与三步日志路径.
- 验证分工: 上一条的容器内/宿主分工为硬约束 (m25 D016); 在容器里拿不到真实验证入口的项, 结论一律写未验证, 不得用替身材料凑数.
- 观察代价: v1 不设性能指标; 首次初始化耗时与 build 耗时只记录不判定 (m23 实测单库单步约 26 秒, 只是量级参考, 不是承诺).

## 关键流程

serve 启动/复用: 取锁 → 读 `state.json` (无文件则新起) → 三步探活 → 存活: 直接组装 `url` 与 `keys` 返回 (`reused=true`) → 判死: 检查端口是否被别的程序占用 → 被占 `port_in_use` 报错交用户裁决 (不换端口不接管) → 未被占: 按原端口起守护子进程 → 轮询端口就绪 (上限 10 秒) → 写 `state.json` (含当前 `data_keys`) → 释放锁 → 解析地址并输出 → 地址缺失时仍返回服务信息并带 `address_missing` 与 `candidates`.

build 与运行中的服务: 取锁 → 初始化 (缺失时) → 三次 `podman run` → 合并 → 门禁 → 写目标库原件 → (门禁通过时) 复制副本到 `serve-root` (`os.replace`) → 更新 `state.json.data_keys` → 释放锁 → 输出摘要. 服务不需要重启, 页面刷新即可看到新数据; 副本复制与页面读取之间靠 rename 保证不会读到半个文件.

stop: 取锁 → 无 `state.json` 则幂等成功 → 探活 → `SIGTERM` → 等 10 秒 → 清 `state.json` 与锁文件 → 保留 `serve-root/` 与 `cache/`. 旧 URL 立即失效, 输出里说明这一点.

## 决策引用

- `docs/changes/workflow-stack-review/milestone-25/DECISIONS.md`: D001-D016, F001-F008 (D016 细化 m24 U002 的 digest 字段并定验证分工).
- `docs/changes/workflow-stack-review/milestone-13/DECISIONS.md`: D001, D003, D004 (页面标注条款由 m25 D004 收窄), D005, D008, D009, D010, D017, D020, D021, D022, D023, D024, D025, D027, D029 (保留项见 m24 U001), D030.
- `docs/changes/workflow-stack-review/milestone-24/DECISIONS.md`: U001, U002, U003, F001-F006.
- `docs/changes/workflow-stack-review/milestone-23/PROBE.md`: 6.1-6.6 (运行配方, uid 映射, 合并替代方案, 零声明与分母, 门禁统计), 7 (前端行为与 `height=level` 实测), 9 (缺口).
- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D007 (无认证开放的取舍), D011 (已确认地址来源与缺值出口), D012 (真实访问证据口径).
