# 设计: use-sandbox-worktree 生命周期脚本 module (最小 interface 分支)

M11 五场景抽取的设计方案. 设计立场: 五个场景 (诞生/恢复/查询/终结/换母体) 不是五个入口, 而是调用方的五种意图; 其中大量分支 (状态探测, 诞生/恢复分流, 换母体冲突) 是实现细节而非用户决策. 据此把 interface 压到 **2 个入口**, 每个入口背后是一部完整的状态机.

---

## 1. interface

### 1.1 module 形态与入口

module = host 侧生命周期编排脚本 `lifecycle.py` (单文件, 与现有四脚本同目录). 入口恰 2 个:

```
lifecycle.py up   [--repo <主仓路径>] [--branch <母体分支>] [--name <任务名>]
                  [--mode whitelist|blacklist (--allow <IP/CIDR>)... | (--deny <IP/CIDR>)...]
                  [--image <镜像ref>] [--check] [--yes <决策tag>]...
lifecycle.py down [--repo <主仓路径>] [--branch <母体分支>] [--i-am-sure]
```

参数锚定规则 (消解 M03 `/tmp/swt-m03-index.json` 遗留缺口, 不再要跨命令索引):

- `--repo` 缺省 = cwd 所属主仓 (`git rev-parse --git-common-dir` 推导); 传了必须存在且是 git 仓.
- `--branch` 缺省 = cwd 所在 linked worktree 的当前分支 (仅当 cwd 已在母体 worktree 内); 否则必填. 名字沿用 use-worktree 的 slug 规则 (母体分支名 = worktree 目录名 = 容器名, D007 一名贯穿).
- `--repo`/`--branch` 显式可查, 无隐藏全局状态, 两会话同名冲突自然消失.

### 1.2 两个入口的语义

**up = "我要一个可用的 sandbox-worktree"**. 内部先探测后分流, 调用方永不先查状态:

| 探测结果 | up 的内部行为 |
|---|---|
| 母体无, 容器无 | 完整诞生: D008 config 写入+功能校验 → 守护进程拉起 (0.0.0.0 兜底) → 镜像 match/build (见决策点) → nft 规则注入 → 容器 create/start → ssh 通路就绪 → 就绪探测 (ssh BatchMode true / clone 分支核对 / `pi --help` exit 0) → 输出 json, exit 0 |
| 容器在但停着 / 守护进程僵死 / nft 规则缺失 | fail-closed 恢复 (D011 固定序: nft 注入 → 守护进程拉起+校验 → 最后 start 容器), 先经决策点 `recover-confirm` |
| 容器健康 | no-op, 原样输出状态 json (幂等, 不重启) |
| 另一母体在本主仓活跃 (D010 冲突) | 决策点 `switch-mother`; 确认后按序执行: 停旧母体全部容器/守护进程 → 校验旧母体 ref 与工作区干净 → hideRefs 例外改指新分支 → 走诞生序列. 即换母体 = down 旧 + up 新的单次确认复合 |
| 母体 worktree 不存在 | 先建 (git worktree add, 同 use-worktree 语义), 再诞生 |

**down = "我要拆掉这个 sandbox-worktree"**. 按容器 label 发现该母体下**全部**容器 (D009 共享母体, 不只看单个), 逐容器 ssh 脏检查 (未 commit 数 + `rev-list --count origin/<分支>..HEAD` 未 push 数) → 全干净则 rm 容器, 停守护进程, **母体保留** (D012); 脏或 ssh 不可达 → exit 3 阻塞, `--i-am-sure` 才继续并登记审计 (dirty-release 落 checklist, M03 先例).

**查询不是入口**: `up --check` 只读探测, 输出同一份状态 json (含共享母体视图: 该母体下所有容器各自的脏概要, 守护进程, nft 规则在位性, 镜像 digest 与在跑容器的新旧比对), 绝不变更任何状态, 绝不 exit 3/4.

### 1.3 用户决策协议 (非交互确认回路)

脚本不读 stdin. 需要用户拍板时:

- up: exit 4, stderr 首行 `DECISION-NEEDED <tag>` + 人话详情; 用户决定后调用方带 `--yes <tag>` 重入. 决策 tag:
  - `recover-confirm` — 已有停着的容器, 按 fail-closed 序列重启? (D011 询问义务)
  - `image-build` — 镜像 match 判 BUILD-NEW, 展示推导清单后构建? (D014 用户确认)
  - `image-fresh-keep` / `image-fresh-rebuild` — 在跑容器镜像 digest 落后于最新可用镜像, 保留还是终结重建? (D013, 绝不自动拆)
  - `switch-mother` — 同仓已有另一活跃母体, 换过去? (D010)
- down: exit 3, stderr 首行 `TERMINATE-BLOCKED` + 脏概要; `--i-am-sure` 重入 (M03 已实测的先例, 语义原样).

每次重入**重新探测**, 状态变了就给新的 tag, 决策永不过期生效. mother 工作区脏 (跟踪文件未暂存改动, 会阻塞推送落地) 不是决策点: exit 1 tag `mother-dirty`, 脚本绝不代改母体内容, 用户手动处理 (母体是用户审阅现场).

### 1.4 exit code 全表

| code | 含义 | stderr 首行 |
|---|---|---|
| 0 | 成功 (up 含 already-up/--check; down 含幂等已消失) | — (json 走 stdout) |
| 1 | 断言/环境失败, fail-closed, 现场保留可重入 | `ASSERT-FAIL <name>` |
| 2 | 用法/环境错误 (参数缺, 非 git 仓, 拿不到并发锁) | `USAGE-ERROR <原因>` |
| 3 | 终结被阻塞, 待 `--i-am-sure` | `TERMINATE-BLOCKED` |
| 4 | 待用户决策, 待 `--yes <tag>` | `DECISION-NEEDED <tag>` |

exit 1 的 name 至少含: `mother-dirty` / `config-verify` (D008 `!` 例外语法本机 git 版本重验失败) / `port-in-use` (F006: podman 原生 125 透传, 不自动换端口) / `state-corrupt` (运行时状态文件损坏, 指引人工查看) / `read-face-leak` (诞生校验发现守护进程读面广告了母体分支以外的东西).

### 1.5 输出契约

stdout 单行 JSON (机器可读, llm 消费); 人类可读进度走 stderr. JSON 稳定字段: `action` / `mother{branch,dir,reused}` / `daemon{pid,addr,port}` / `container{name,image_digest,state}` / `ssh{host,port,user,key,command}` (用户下一步直接照抄的 ssh 命令) / `network{mode,rules_present}` / `containers[]` (共享母体全景, 各含 `uncommitted`/`unpushed` 计数) / `pending_decision{tag,detail}`. 实现可加字段 (M03 已验证 schema 超集可行), 稳定字段不删不改名.

### 1.6 不变量 (调用方可依赖的承诺)

1. **单活动母体** (D010): up 成功返回后, 该主仓恰有一个活跃母体; 违反它的路径全部经 `switch-mother` 决策点, 无静默并存.
2. **fail-closed 顺序** (D011): 容器工作负载启动前, nft 规则与守护进程必已就绪且经校验; 恢复路径同序.
3. **母体不可侵犯**: up/down 绝不删除母体, 绝不改写母体工作区内容; 母体存删用户自决 (D012).
4. **非交互**: 一切用户确认走 exit 3/4 + 重入 flag.
5. **幂等可重入**: 每步状态转移落盘 (运行时状态文件, M03 先例); 硬中断后重跑 up/down 要么续走要么 fail-closed 停住, 不留半启用态.
6. **原生报错透传** (D006 降级精神): git/podman/ssh 原文不吞不译, 脚本只加标签与人话摘要; 译解表留 SKILL.md 文档 (脚本与文档不重复维护, 反方审查第 3 点采纳).

### 1.7 顺序约束与禁止操作

- up 必须先于一切 ssh 入容器使用; down 之后 ssh 通路作废.
- 同主仓的 up/down 互斥 (文件锁, M03 fcntl 先例); 并发第二者 exit 2, 不排队.
- down 以母体为粒度 (拆全容器), 单容器手术不在此 interface 内 — SKILL.md 容器命令独立一节留文档级扩展点 (D022).
- 容器内 git 操作 (clone/commit/fetch 解冲突/push) 不属本 interface; 本 interface 只做就绪探测与脏检查两类只读 ssh.

### 1.8 考察点覆盖对照 (M11 全部六项)

| 考察点 | 藏在哪 |
|---|---|
| 母体身份与复用 / 单活动母体检查 (D010) | up 的探测分流表 + `switch-mother` 决策点 (1.2/1.3) |
| 恢复状态机: stale daemon / readiness / 可重入 (D011) | up 恢复行 + 不变量 2/5 (1.2/1.6) |
| 终结数据保护: 脏检查 / 参照 ref / 强拆确认 (D012) | down 语义: 未 push 参照 = `origin/<母体分支>`, exit 3 + `--i-am-sure` + 审计登记 (1.2) |
| 共享母体多容器 (D009) | down 逐全部容器脏检查; `--check` 输出 `containers[]` 全景 (1.2/1.5) |
| 全局 config: 既有配置 / 回滚 / git 版本重验 (D008) | 诞生序列内: 写前读既有值, 写后读回核对 + 经守护进程 ls-remote 功能校验 (只广告母体分支), 失败即 `config-verify`/`read-face-leak` exit 1, config 留存不回滚 (与 M03 一致, 对用户日常 push 真远端无影响 F007(8)) (1.4/3 节) |
| 镜像版本 digest 比对 (D013) | up 诞生/健康两分支都比对, `image-fresh-*` 决策点, 绝不自动拆 (1.3) |

---

## 2. 使用示例

调用方 = host llm (照 SKILL.md 敲命令) + 用户 (最终决策). 全程无 stdin.

### 2.1 主链: 诞生 → 干活回流 → 终结

```text
用户: 帮我开个沙盒, 在 proj 仓库搞 feature-x.
llm:  lifecycle.py up --repo ~/Workspace/proj --branch proj-main-feature-x \
        --mode whitelist --allow <盘点出的IP段>
      ← exit 0, stdout json:
        {ssh:{command:"ssh -i ~/.swt/ssh/proj-main-feature-x.ed25519 -p 42329 agent@127.0.0.1"},
         mother:{dir:"~/Worktree/proj-main-feature-x",reused:false}, ...}
llm:  把 ssh 命令给用户. 用户 ssh 入容器, 驱动容器内 pi 干活, 容器内 commit + push.
      推送落地 (updateInstead) → 母体目录文件即时更新, 用户在 host 直接审阅/试跑.
用户: 差不多了, 拆掉吧.
llm:  lifecycle.py down --repo ~/Workspace/proj
      ← exit 0 (全容器干净), 容器删, 守护进程停, 母体保留.
llm:  告知: 母体目录还在, 要留要删你自己在 host 上定 (脚本不管).
```

### 2.2 失败路径 A: 宿主重启后的恢复

```text
用户: 重启完, 接着昨天的沙盒干活.
llm:  lifecycle.py up --repo ~/Workspace/proj   (cwd 已在母体 worktree, --branch 省略)
      ← exit 4, stderr: DECISION-NEEDED recover-confirm (容器在, 停着; 守护进程已死)
llm:  问用户: 要按安全序列重启吗 (先网络规则和 git 通道, 最后起容器)?
用户: 重启吧.
llm:  lifecycle.py up ... --yes recover-confirm
      ← exit 0, json 就绪, 新 ssh 端口照旧 (F006: 端口跨重启稳定, 由 podman port 现查)
```

### 2.3 失败路径 B: 终结撞上未 push 工作

```text
llm:  lifecycle.py down --repo ~/Workspace/proj
      ← exit 3, stderr: TERMINATE-BLOCKED + 容器 proj-main-feature-x:
        未 push 2 个 commit, 未提交改动 1 处 (porcelain 摘要)
llm:  原样转告用户: 容器里有没回流的活, 强拆就没了.
用户: 那些不要了, 拆.
llm:  lifecycle.py down --repo ~/Workspace/proj --i-am-sure
      ← exit 0; 脏放行决定已登记进审计 checklist (谁/何时/脏概要), 容器删, 母体保留.
```

### 2.4 失败路径 C: 镜像出了新版 (D013)

```text
llm:  lifecycle.py up ... (第二轮)
      ← exit 4, DECISION-NEEDED image-fresh-rebuild (在跑容器 digest=aaa, 最新可用 digest=bbb)
llm:  转告: 镜像有新版. 要拆了重建吗 (绝不自动拆)?
用户: 先不折腾, 用旧的.
llm:  lifecycle.py up ... --yes image-fresh-keep
      ← exit 0, 原容器续用.
```

### 2.5 失败路径 D: 换母体 (D010)

```text
llm:  lifecycle.py up --repo ~/Workspace/proj --branch proj-main-fix-y
      ← exit 4, DECISION-NEEDED switch-mother (活跃母体 proj-main-feature-x 还在)
用户: 换到 fix-y.
llm:  lifecycle.py up ... --yes switch-mother
      ← exit 0; 内部: 停旧容器/守护进程 → 旧母体 ref 与干净校验 (脏则停手报错) →
        hideRefs 例外改指 fix-y → 诞生 fix-y. 全程一次确认, 无中间裸奔窗口.
```

---

## 3. seam 背后藏了什么

seam 就是这两个 CLI 入口. implementation 的组成与来源:

- **状态分类器**: 探测 cwd/主仓/worktree, 按容器 label 发现容器 (全部, 非单个), 按守护进程命令行模式发现进程对 (launcher+worker 记一个实例, M03 实现复用), 读运行时状态文件, 查 nft 表在位性 (经 net-firewall show). 分类结果驱动 1.2 的分流表. 藏它的理由: 正确探测一条要 5-8 条系统命令, 且满是陷阱 (receive.hideRefs 与 uploadpack.hideRefs 一字之差效果全异, F007(4)(5); 守护进程是进程对不是单进程) — llm 现场即兴正是漏项重灾区.
- **次序引擎**: D011 fail-closed 固定序与 D008 config 写入/读回/功能校验 (经守护进程 ls-remote 只见母体分支, 兼作 git 版本重验) 直接函数级复用 e2e-smoke.py 已实跑验证的实现. 藏它的理由: 顺序写错 = 网络裸奔窗口 (F008), 这是整个脚本化方向的原点, 必须钉死在代码里.
- **决策协议**: exit 3/4 + 重入 flag + 重入时重新探测 + 脏放行审计登记. 藏它的理由: 这是 "脚本非交互" 与 "决策权在用户" 两条约束合取产生的编舞, 散在文档里每个调用方都要自己排一遍, 收进 module 一次写对处处生效 (locality).
- **镜像与防火墙不吞并**: up 经 subprocess 调 image-prep.py (match/build, D017 匹配规则在那里) 与 net-firewall.py (apply/show). 它们是各自 seam 后的现成 module, interface 已稳定且各有测试; 生命周期脚本只消费其输出, 不复制其逻辑 (login-wall build 薄封装同一先例). login-wall 不统辖 — VNC 验证属登录墙场景, 生命周期对它无感知.
- **不做的抽象**: 无容器 provider 多态 (D022), 无内部插件层. 深度来自状态机与硬约束, 不来自层次.

为何值得藏 (depth 判定): 调用方学习面 = 2 个动词 + 5 个 exit code + 1 份 json; 触发面 = 完整生命周期 6 类状态分支 + 4 类用户决策 + 全部硬约束. 删除测试: 若删掉此 module, 上述复杂性会在 SKILL.md 的 checklist 和每次调用的即兴发挥中整体重现 — 复杂度真实存在且必然 N 处重现, module 有价值.

---

## 4. 依赖与测试策略

按 DEEPENING.md 依赖类别:

- **进程内**: 决策协议状态机, 探测结果的分类逻辑, json 组装. 经 internal seam (模块内函数) 单测; internal seam 不进 interface (接缝纪律), 不对外承诺.
- **本地可替代**: git 仓本体 — 用夹具仓 + 真 git daemon + 临时 ssh 目录 + 动态端口替身 (M03 先例原样沿用, 替身是夹具而非 fake 框架); 运行时状态文件落临时目录.
- **环境本体**: podman/rootless netns/nft 不做替身 — 运行环境就是宿主机本机, 且硬约束长在 rootless podman 特性上 (D022), 抽替身必漏. 集成测试真跑, 断言打在 interface 可观察面: exit code + stdout json + `git config --get-all` + net-firewall show + 容器可达性.
- **真正外部**: 无. 宿主机本机, 无网络服务, 脚本不触碰 LLM 凭据.

测试怎么打在 interface 上 (替换, 不叠加): 场景 → 命令序列 → 期望 exit code + json 字段断言 的用例表. 必备用例: 诞生全链 / already-up 幂等 no-op / 恢复 (stop 后 up, 断言 net-firewall show 规则在位且容器 running) / mother-dirty exit 1 / down 脏 exit 3 → --i-am-sure 后审计登记存在 / down 容器已消失幂等 / D010: 活跃母体下 up 他支 exit 4 → --yes 后旧容器尽, hideRefs 例外已改指 (config --get-all 断言) / D013: 伪出新 digest → exit 4 image-fresh-* / read-face 探测: ls-remote 经守护进程恰见母体分支一个 ref / 并发锁 exit 2. M03 的 test_swt_m03 场景改写为 up/down 调用后归入此表; 与新 interface 重叠的旧 e2e-smoke 入口级断言删除, 不留双层.

---

## 5. 权衡

- **leverage 高处**: 2 个动词承载 5 场景; 每次调用都是一次状态机转移加全套硬约束执行, 不是命令透传 (非 shallow). SKILL.md 从 "几十步操作序列" 缩为 "2 个入口 + 决策点应答表 + 容器命令附录", llm 即兴面收到最窄.
- **locality 高处**: D008 模板, D011 顺序, D010 不变量, F003 拓扑铁律全部单点固化. 拓扑修订 (如 hideRefs 键名再变) 落一处, 全部调用方与测试自动跟随.
- **seam 位置的代价**: seam 定在 CLI, 测试必须真跑容器与守护进程, 秒级到分钟级, 且依赖本机环境 — 换来的是测试面与调用面完全同形 (接口即测试表面), 不存在 "测过的不是用过的". internal seam 保留了可单测的纯逻辑, 但刻意不承诺稳定.
- **查询并入 up 的代价**: `--check` 必须守绝对只读纪律, 否则 "看一眼" 会带副作用; 收益是状态分类器只有一份, 不会出现查询与实作各养一套探测逻辑然后漂移.
- **换母体并入 up 的代价**: up 的实现分支最多, 单入口风险是长成巨物; 缓解是镜像/防火墙外委给既有 module, 生命周期脚本只做编排与决策协议. 收益是调用方意图单一 ("我要母体 X 可用"), 分支纯属实现细节 — 这正是 deep module 的形状.
- **对反方审查的回应**: 不冻结未验证的接口 — 本方案每件钉进代码的东西 (exit 3 + --i-am-sure, fail-closed 序, config 校验, 脏检查参照 ref, 端口不自动换) 都有 M03/M04 实跑日志背书; 无实跑背书的部分 (换母体复合, 镜像决策点) 全部落在决策点协议之后, 用户点头才执行, 错了也只是多一次确认而非错误的全局状态.
