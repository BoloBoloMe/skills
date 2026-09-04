# use-sandbox-worktree 瘦闭环 (MILESTONE-03) Technical Spec

## 技术目标

- TG-001: E2E 编排器雏形 (birth/smoke/cleanup 三阶段) 可执行, 每阶段带日志与断言, 失败即非零退出. 覆盖: G-002, AC-001, AC-005, AC-006.
- TG-002: 母体拓扑落地: 主仓 config 按 D008 模板写入并校验, git 守护进程随容器生灭, 写面收敛为仅母体分支 ff-only. 覆盖: AC-001, AC-003, AC-004, G-001.
- TG-003: 最简容器 (git + pi CLI + openssh-server) 可起, ssh 可入, 容器内克隆检出母体分支, push 推送落地母体目录. 覆盖: AC-001, AC-002.
- TG-004: 拆解幂等可重跑: cleanup 后环境回到可再次 birth 的状态, 母体留存. 覆盖: AC-005, G-002.

## 架构与组件

新建 `workflow/use-sandbox-worktree/` skill 目录, 本变更只含 `scripts/` 编排器雏形与镜像定义, SKILL.md 不在本变更 (M10 定稿).

- **编排器** `scripts/e2e-smoke.py` (uv run python, 单文件): 三阶段子命令, 逐阶段日志行 `[STAGE] ...`, 断言失败即 `SystemExit(非零)` 并打印失败断言名. 所有外部进程调用经 `subprocess.run(..., capture_output=True)`, 错误原样透传 (原生英文报错不翻译, 译解表是文档职责, D008).
- **母体管理**: 母体目录名经 `uv run workflow/use-worktree/scripts/slug.py <project> main <分支名原文>` 生成, 解析其 stdout 的 `dir=` 行取值 (三参数形式输出 project=/source_slug=/target_slug=/dir= 等行; `slug=` 仅一参数形式输出, 不可用). 母体目录名 = 母体分支名 = `dir=` 值 (一名贯穿, D007); `git worktree add -b <dir值> <dir路径>` 建 linked worktree (编排器无人值守, 直接 git 命令).
- **git 守护进程**: `git daemon --enable=receive-pack --base-path=<夹具 srv 根> --listen=<地址> --port=<预选端口>` 派生进程; 端口选择协议: 编排器先用 socket bind 0 预选空闲端口, 关闭后拉起 daemon, 拉起后探测该端口可连, 失败重选至多 3 次 (TOCTOU 竞态在单机演练可接受); 不使用 daemon 自身的 --port=0 (无可靠发现手段). 主仓固定位于 `<夹具>/srv/<reponame>/`, base-path = `<夹具>/srv` 且该目录只允许存在主仓一个 git 仓 (母体 worktree/运行时产物/客户端克隆全部在 srv 之外) — TC-001 枚举断言. 主仓 `.git/git-daemon-export-ok` 空文件由 birth 创建 (无 `--export-all` 时缺它 clone 被拒, findings §1 实测前置). 监听地址与端口落运行时 JSON. 监听地址见安全策略节的探测顺序.
- **容器镜像契约**: `image/Containerfile` build context 为 `image/` 目录; 基座 `docker.io/library/node:24-bookworm-slim` (自带 node/npm); `apt-get install git openssh-server`; `npm i -g @earendil-works/pi-coding-agent`; 建用户 `agent` (workdir `/home/agent`); build 时 `ssh-keygen -A` 生成 host key 并 `mkdir /run/sshd`; 入口 `CMD ["/usr/sbin/sshd", "-D", "-e"]` (前台 sshd 即容器长驻主进程); 授权公钥由 birth 在容器 start 后经 `podman exec` 写入 `/home/agent/.ssh/authorized_keys` (属 agent, 0600) 并随后断言 BatchMode 连通.
- **容器**: `podman create --name swt-<dir值> --label ... -p 22 <最简镜像>`, 动态宿主端口, `podman port` 事后发现 (F006).
- **测试夹具**: `/tmp/swt-m03-<rand>/` 布局: `srv/<reponame>/` (主仓, main 初始提交, 无 origin — BR-001 物理排除真远端泄露源), 其余运行时产物与客户端克隆在 srv 之外; 主仓 `.git/swt-m03-fixture` 标记文件由自建时创建 (夹具标识). cleanup 不删夹具仓本身 (供事后审计), 只归还资源.

关键 seam: 编排器 ↔ git/podman CLI — 全部断言经 CLI 输出观察, 无内部函数级断言.

## 接口契约

编排器 CLI (唯一公开接口):

```text
uv run scripts/e2e-smoke.py birth   --repo <主仓路径> --name <分支名原文>   # 建母体+config+daemon+容器+克隆
uv run scripts/e2e-smoke.py smoke   --repo <主仓路径> --name <分支名原文>   # 干活+回流+拒绝矩阵断言
uv run scripts/e2e-smoke.py cleanup --repo <主仓路径> --name <分支名原文> [--i-am-sure]   # 拆容器+停 daemon+断言母体留存
```

- `--i-am-sure`: cleanup 脏放行明示开关 (D012 非交互形态); 缺省时脏容器阻塞.

- `--name`: 母体分支名原文 (未 slug 化); slug 化只发生在编排器内部, 经上述 slug.py 契约.
- `--repo` 缺省时编排器自建 /tmp 夹具主仓 (含 `.git/swt-m03-fixture` 标识).
- **--repo 边界** (防越界写真实仓): 提供的 `--repo` 必须含 `.git/swt-m03-fixture` 标识文件, 否则退出码 2 (`stderr` 首行 `NOT-A-FIXTURE <路径>`), 不执行任何写操作.
- 退出码: 0 = 阶段含断言全过; 1 = 断言失败 (stderr 首行 `ASSERT-FAIL <断言名>`); 2 = 环境/参数错误; 3 = cleanup 脏阻塞 (资源全保留, stderr 含脏内容摘要; ssh 不可达/容器已退出致状态不可判定时按脏处理, fail-closed).
- 状态发现: birth **每创建一个资源即增量更新** `<repo>/.swt-m03-<slug>.json` (母体/daemon/容器逐段落盘), 而非末尾一次写; smoke/cleanup 读它, 不各自重新探测.
  - JSON schema: `{version, name, repo, srv, mother_dir, mother_branch, daemon: {pid, addr, port} | null, container: {name, host_port} | null, stage}`; 写入原子化 (临时文件 + `os.replace`).
  - **cleanup 兜底发现与 fail-closed**: JSON 缺失或缺段时, 按 `podman ps -a --filter label=sandbox-worktree.repo=<repo>` 与 `pgrep -f 'git daemon.*<srv 根>'` 发现残留; JSON 与兜底发现结果不一致 (PID 对不上/多 daemon 匹配/容器名不符) → 中止并打印两侧事实, 交人工处理, 不猜. 容器内克隆目录不登记不删 (留 /tmp 夹具供审计).
  - **cleanup 成功收尾时删除该 JSON**; birth 开头发现 JSON 残留视为上次未清理干净, 提示先 cleanup.
- 缺省 `--repo` 的跨命令定位: 编排器维护 `/tmp/swt-m03-index.json` (name → repo 绝对路径); birth 自建夹具成功后原子注册 (临时文件 + rename) 并 stdout 打印路径; smoke/cleanup 省略 `--repo` 时按 `--name` 查索引 — 索引缺失/损坏/name 不存在/登记路径已失效 → 退出码 2 并提示显式传 `--repo`; birth 遇同名登记冲突 → 退出码 2 拒绝, 不覆盖; cleanup 成功收尾时原子注销.
- 幂等: cleanup 可对部分诞生的残留反复执行, 不报错于 "已不存在".
- 重跑验证母体复用路径时, 第二轮 birth 必须显式传同一 `--repo` (cleanup 已注销索引, 省略 `--repo` 会新建夹具, 验证不到复用); 手动流程: 首个 birth 从 stdout 或索引取夹具路径, 后续命令显式携带.

## 数据模型与状态

- 主仓 config (D008 模板, `<母体分支>` 为唯一变量):
  ```ini
  [receive]
      denyCurrentBranch = updateInstead
      denyNonFastForwards = true
      denyDeletes = true
      hideRefs = refs/heads
      hideRefs = !refs/heads/<母体分支>
      hideRefs = refs/tags
  [uploadpack]
      hideRefs = refs/heads
      hideRefs = !refs/heads/<母体分支>
      hideRefs = refs/tags
  ```
- **config 写入语义** (TC-002 故障注入契约):
  - 标量键 (`denyCurrentBranch`/`denyNonFastForwards`/`denyDeletes`): 不存在则 `git config <key> <值>` 写入; 存在且符则跳过; 存在且不符则 `ASSERT-FAIL config` 中止, 不覆盖.
  - 多值键 (`receive.hideRefs`/`uploadpack.hideRefs`, 模板各三值): `git config --get-all` 取当前多重集; 为空则按模板顺序依次 `git config --add` 全部三值; 非空且多重集 (长度 + 各值计数) 恰等于模板则跳过; 否则 `ASSERT-FAIL config` 中止, 不改写. (重复值会使多重集不等, 不得放过.)
  - 测试故障注入 = 预写错误键值.
- 容器 label: `sandbox-worktree.name=<slug>`, `sandbox-worktree.repo=<主仓绝对路径>`, `sandbox-worktree.branch=<母体分支>` (M05 结论: 身份入容器 label).
- 母体分支名 = worktree 目录名 slug (一名贯穿, D007).
- birth 重入状态机:
  - 无 JSON, 无同名母体, 无存活 daemon (按 srv 根 pgrep) → 全新诞生.
  - 无 JSON, 存在同名母体 worktree 且工作区干净, 无存活 daemon → 复用母体 (D010), config 按写入语义重校验, daemon/容器重建.
  - 无 JSON, 存在同名母体但工作区脏 → 中止, 提示人工处理 (不自动清).
  - 存在 JSON 或同名存活容器 → 中止, 提示先 cleanup; 不自动强拆.
  - 无 JSON 但按 srv 根 pgrep 发现存活 daemon → 中止, 提示先 cleanup (由 cleanup 兜底发现并回收); 不得重复拉起.

## 关键流程

birth 顺序 (硬约束, BR-002):
1. `--repo` 夹具标识校验 (无标识退出码 2) / 夹具自建 → 2. 重入状态机判定 (见上) → 3. slug 契约生成 dir 值 + 建/复用母体 → 4. `touch <主仓>/.git/git-daemon-export-ok` → 5. config 按写入语义处理 → 6. config 逐键校验 (断言: `--get-all` 比对模板, 含 srv 根枚举仅主仓一仓; 失败中止, 后续步骤不可达) → 7. 守护进程拉起 (监听地址探测: 先试 pasta 网关接口地址, 不可行则 0.0.0.0, 结果记产物) → 8. 镜像存在性检查 (无则 build) → 9. `podman create` + `start` → 10. `podman port` 发现 → 11. 临时 ssh key 注入 + BatchMode 连通断言 → 12. 容器内 `git clone -b <dir值> git://<daemon地址>:<port>/<reponame>` → 断言检出分支 = 母体分支 → 13. JSON `stage` 字段更新为 born (各资源已随创建增量落盘, 此步仅收尾).

smoke: 容器内 commit 新文件 → push → 断言母体目录文件内容; 拒绝矩阵 (新分支/tag/non-ff/删除) 逐条断言被拒; `git remote -v` 与 `ls-remote` 断言读面; 脏树拒绝断言 (先制造后还原); **负向用例收尾: 容器内 `git reset --hard origin/<母体分支>` 复原未 push 的本地提交, 保证后续干净 cleanup 可走通** (脏阻塞路径由专测覆盖).

cleanup (完整终结语义归 M11/12, 本变更实现 D012 的非交互形态): ssh 入容器查 git 状态 (未 commit 改动数/未 push commit 数) → **脏则中止, 提示脏内容摘要, 不删任何东西** (D012 阻塞语义); 用户明示的形式 = 显式传 `--i-am-sure` 重跑, 此时脏状态记入产物与 checklist 的**脏放行登记**字段 (状态值/夹具路径/时间/依据) 后继续 → `podman rm -f` → kill daemon PID (含兜底发现) → 断言容器/daemon 灭, 母体目录与 ref 留存 → 删运行时 JSON 与索引项 → 写产物文件 (逐阶段日志/结果事实/中间态声明/checklist).

## 边界与异常处理

- 端口占用: 容器 start 失败 (exit 125, pasta `Address already in use`, F006) 原样透报, 不自动换端口.
- 母体脏树: smoke 脏树场景由编排器先制造未暂存改动再 push, 断言 `[remote rejected]` 前缀 (不做字符串精确匹配), 断言后 `git checkout --` 还原.
- clone 游离 HEAD: clone 必须带 `-b <母体分支>` (F007: HEAD 广告不可隐藏); 断言 `git branch --show-current` = 母体分支.
- 重入: 见数据模型节状态机.
- 中途失败: 断言失败即停, JSON 留存, 残留由 cleanup 幂等回收.

## 安全策略

- 真远端: 编排器断言容器内无真远端 remote 与凭据 (BR-001); 夹具仓不设 origin, 物理排除泄露源.
- 守护进程无认证: 已接受取舍 (D008).
- **守护进程监听地址**: rootless 容器经 pasta 网关访问 host, host 的 loopback 监听对容器不可达 (2026-09-01 调研实测). M03 全通网络中间态下, 监听地址按 "pasta 网关接口地址优先, 0.0.0.0 兜底" 探测; 0.0.0.0 兜底时 LAN 可到达收敛写面 (仅母体分支 ff), 属中间态风险, 必须写入产物中间态声明与 checklist; 最终收敛属 MILESTONE-04 (nft 双模式).
- 主仓 config 常驻: 本变更 config 只写 /tmp 夹具仓, 不触碰用户真实仓库.
- ssh 入容器: 演练用临时 key 对, 私钥落 /tmp 夹具目录, 不复用用户既有 key.

## 非功能要求

- NFR-001 可观测: 每阶段 stdout 至少一行 `[STAGE] <ok|fail> <摘要>`; 产物文件含完整命令/输出附录. 验证口径: AC-006 场景.
- NFR-002 可重跑: cleanup 后再次 birth 全过. 验证口径: AC-005 边界场景.

## 测试接缝与用例

测试统一落 `tests/test_swt_m03.py` (pytest 发现, unittest.TestCase 风格与仓库既有 `tests/test_sync_to_pi.py` 一致); 验证命令 `uv run pytest tests/test_swt_m03.py`. 环境依赖 (podman/网络拉镜像) 缺失时测试失败并打印缺失项, 不静默 skip.

- TC-001:
  接缝: 编排器 CLI 退出码 + `git config --get-all` 输出 + 文件系统.
  公开接口: `e2e-smoke.py birth`.
  用例类型: 正常.
  Given: 夹具主仓无活动母体. When: birth. Then: 退出码 0, 母体 worktree/分支存在, config 与 D008 模板逐项一致, `git-daemon-export-ok` 存在, daemon 进程存活且 srv 根目录枚举仅主仓一个 git 仓.
  预期值来源: D008 模板字面量 + findings §1 实测前置.
  测试层级: 端到端.
  允许的 mock/fake: 文件系统夹具仓 (系统边界).
  覆盖: AC-001, TG-001, TG-002.
- TC-002:
  接缝: 编排器 CLI 退出码与 stderr.
  公开接口: `e2e-smoke.py birth`.
  用例类型: 异常.
  Given: 测试预写一个与模板不符的 config 键 (故障注入, 见 config 写入语义). When: birth. Then: 退出码 1, stderr 含 `ASSERT-FAIL config`, 无 daemon 进程, 错误键未被覆盖.
  预期值来源: BR-002 + config 写入语义契约.
  测试层级: 端到端.
  允许的 mock/fake: 文件系统夹具仓.
  覆盖: AC-001 (失败分支), TG-002.
- TC-003:
  接缝: 容器内 `git branch --show-current` / `git remote -v` / `git ls-remote` 输出.
  公开接口: `e2e-smoke.py birth` 后编排器 ssh 断言.
  用例类型: 正常.
  Given: birth 完成. When: smoke 的读面断言. Then: 当前分支 = 母体分支; remote 仅 daemon URL; `ls-remote` 除 HEAD 行外 (HEAD 广告不可隐藏, F007 已知泄露) refs 仅含母体分支, 且容器内 remote-tracking refs 仅母体分支.
  预期值来源: D007/D008 与 F007 实测 (HEAD 广告行为).
  测试层级: 端到端.
  允许的 mock/fake: 无新增.
  覆盖: AC-001, AC-004, TG-003.
- TC-004:
  接缝: 母体目录文件内容 + push 输出.
  公开接口: `e2e-smoke.py smoke`.
  用例类型: 正常.
  Given: birth 完成, 容器内已克隆. When: 容器内 commit 新文件并 push. Then: push 接受, 母体目录对应文件内容 = 提交内容.
  预期值来源: F004/F007 推送落地实测.
  测试层级: 端到端.
  允许的 mock/fake: 无新增.
  覆盖: AC-002, TG-003.
- TC-005:
  接缝: push 拒绝输出.
  公开接口: `e2e-smoke.py smoke`.
  用例类型: 异常.
  Given: birth 完成. When: **容器内**依次 push 新分支/新 tag/non-ff 强推母体分支/删除分支. Then: 全部 `[remote rejected]`, 拒绝信息为 git 原生英文.
  预期值来源: F007 拒绝矩阵.
  测试层级: 端到端.
  允许的 mock/fake: 无新增.
  覆盖: AC-003, TG-002.
- TC-006:
  接缝: push 拒绝输出.
  公开接口: `e2e-smoke.py smoke`.
  用例类型: 边界.
  Given: 母体目录跟踪文件被编排器制造未暂存改动. When: 容器内 push 新提交. Then: `[remote rejected]`; 断言后母体还原干净.
  预期值来源: F001 实测.
  测试层级: 端到端.
  允许的 mock/fake: 无新增.
  覆盖: AC-002 (失败分支), TG-002.
- TC-007:
  接缝: 编排器 CLI 退出码 + `podman ps`/`git worktree list` 输出.
  公开接口: `e2e-smoke.py cleanup` 后再次 `birth` + `smoke`.
  用例类型: 边界.
  Given: 完整跑过一轮. When: cleanup 后再次 birth + smoke. Then: cleanup 后容器与 daemon 灭, 母体目录与 ref 留存, JSON 已删; 再次 birth 走复用母体路径, 退出码 0 且断言全过.
  预期值来源: BR-003, NFR-002, birth 重入状态机.
  测试层级: 端到端.
  允许的 mock/fake: 无新增.
  覆盖: AC-005, TG-001, TG-004, NFR-002.
- TC-008:
  接缝: 编排器 CLI 退出码与 stderr.
  公开接口: `e2e-smoke.py birth`.
  用例类型: 异常.
  Given: `--repo` 指向无 `.git/swt-m03-fixture` 标识的目录 (模拟真实仓). When: birth. Then: 退出码 2, stderr 首行 `NOT-A-FIXTURE`, 该目录与其 git 仓零写操作.
  预期值来源: EXECUTION.md 全局禁止范围 (真实仓保护).
  测试层级: 端到端.
  允许的 mock/fake: 文件系统.
  覆盖: TG-002 (边界), 全局禁止范围.

## 技术决策引用

- docs/changes/use-sandbox-worktree/DECISIONS.md: D007, D008, D009, D010 (母体复用状态机), D013 (digest 比对本变更不实现, 归 M07/M11)
- docs/adr/0007-gate-daemon-not-ssh.md; docs/adr/0008-mother-worktree-direct-receive-no-hooks.md
- 边界声明: 本变更 cleanup 实现 D012 的非交互形态 (脏则阻塞, 退出码 3, `--i-am-sure` 放行并登记脏放行字段); 完整交互式终结语义归 MILESTONE-11/12. roadmap 的 checklist 是记录要求, 不替代 `--i-am-sure` 的放行条件.

## 依赖与风险

- git 版本须支持 hideRefs `!` 否定例外 (2.53.0 实测, F007); 部署机重验属 M11 考察点, 本变更固定本机.
- rootless podman + pasta; 镜像首次 build 需网络拉取基础镜像.
- 容器到达 daemon 的地址与 daemon 监听地址配对是 M03 待实锤项 (见待验证事实), 不影响接口契约.
- 风险: 容器内 sshd 首次配置 (用户/密钥) 细节未实测 — 防护: 镜像 Containerfile 最小化, 失败即修镜像不改编排.

## 代码边界提示

- 新建: `workflow/use-sandbox-worktree/scripts/e2e-smoke.py`, `workflow/use-sandbox-worktree/image/Containerfile`, `tests/test_swt_m03.py`.
- 复用 (只读调用): `workflow/use-worktree/scripts/slug.py` (契约见架构节).
- 不触碰: 其他 skills, 用户真实仓库, `docs/` 下既有产物 (除本变更产物目录).

## 待验证事实

- 事实: pi CLI 在容器内首次实际运行 (二进制依赖/启动行为未实测)
  影响: 最简镜像 Containerfile 可能需补运行依赖
  验证方式: birth 后容器内 `pi --help`, 结果记入产物文件
- 事实: 容器到达 daemon 的地址与 daemon 监听地址配对 (pasta 网关接口地址可用性)
  影响: birth 步骤 7 的探测实现; 兜底 0.0.0.0 有 LAN 可达中间态风险
  验证方式: birth 实现时探测并记录实际地址入产物; 兜底即触发 checklist 声明
