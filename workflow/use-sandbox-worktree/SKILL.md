---
name: use-sandbox-worktree
description: 管理 sandbox-worktree (host git worktree 母体 + sandbox 容器绑定对) 的生命周期 — 诞生/存续/恢复/换母体/终结, 镜像制备, 网络黑白名单, 展示链与登录墙.
disable-model-invocation: true
---

# use-sandbox-worktree

**术语**:
- **sandbox-worktree**: 一个 host 上的 git worktree (**母体**) + 一个 sandbox 容器的绑定对, 本 skill 管理的生命周期单元.
- **母体**: 主仓在 host 上的一个 worktree 目录, 身兼两职: 容器诞生时从它克隆代码; 容器 push 的成果直接落进它, 打开就能审阅/试跑.
- **推送落地**: 容器 `git push` 被接受的瞬间, 母体目录里的文件自动更新成 push 内容, 不用手动 pull.
- **git 守护进程 (daemon)**: 随容器生灭临时起的 `git daemon` 进程, 容器碰到代码的唯一通道, 无认证.
- **决策收据**: 脚本向我提问时开出的一次性票据, 绑定当时的资源状态; 我答后重跑时先核对状态没变才采用, 变了就重新问.
- **retired 容器**: 换母体后被停下的旧容器, 只准终结不准恢复.
- **base 层 / 项目层**: 镜像分两层 — 固定且跨项目共享的底层; 按项目推导依赖件加装的上层.

固定偏好: 硬约束交给环境 (git 配置/防火墙/拓扑); 容器内 agent 自由驰骋; 容器之外我说了算.
**命名消歧**: `swt` = host 编排脚本 `scripts/swt.py`; `swt-vnc` = 容器内 VNC helper (见登录墙节), 两者无关.

## 角色边界

- 你 (host 侧 agent) 只管理生命周期, 不进容器干活.
- 一切需我拍板的点由脚本以 DECIDE 行表达 (见决策协议节): 逐字转述给我, 我答后带 flag 重跑同一命令, 替我作答即违规.
- 真远端 (github 等) 对容器完全不暴露; 主仓 config 常驻 (残余影响见风险明示节).

## 环境前置

- rootless podman (pasta 网络), nftables, git (须支持配置里 "隐藏所有分支、只放行一个" 的 `hideRefs` 写法; birth 每次会建一次性小仓库实测确认, 不支持则 exit 4).
- `uv run python` 运行全部脚本; 脚本路径相对本 skill 目录引用.
- 记录根缺省 `~/.agents/sandbox-worktree/` (运行状态/决策收据/审计/镜像构建记录同屋), 全部脚本支持 `--records-root` 覆盖.

## 入口: status 先行

```text
uv run python scripts/swt.py status [--repo <主仓>]
```

`--repo` 缺省从 cwd 推导主仓. status 只读, 读末行 `STATE {...}` 分流: 有停着的容器/残留的 daemon/缺防火墙规则 → resume; 无任何记录 → birth; 有 retired 容器 → 唯一出路 terminate (resume 拒绝).
完成标准: 已据 STATE 判定走 birth / resume / terminate 之一.

## 诞生 (birth)

**第一步: 网络模式与白名单盘点 (固定环节, 不可跳过)**
创建容器前必须与我确认网络模式, 运行期不切换:
- **whitelist** (默认拒, 推荐): 只放行 网关 DNS + `--allow` 条目 + 已建立连接的返程流量 (保住 host 发起的 ssh), 其余容器流出全断. birth 自动把容器可达的 daemon 地址并入 allow (否则容器内 clone 物理不通), 该自动条目的残余暴露见风险明示节.
- **blacklist** (默认放行): 只断 `--deny` 条目, 护 host 侧特定服务 (数据库/redis 等) 场景.
盘点方法论: 与我一起列出容器工作所需站点, **域名须解析为具体 IP/CIDR 后传入** (防火墙规则只认 IP, 脚本拒收域名); 条目是 IP 级, 放行即全端口. 站点换 IP 失效时重新盘点. 运行期新站点需求的处理形态未定, 发生时带回本会话问我.

**第二步: 镜像判定与制备**
birth 内部自动跑 image-prep `match`, 需求清单取 `<records-root>/<项目slug>/requirements.md` (或 `--requirements` 指定):
- **清单文件不存在 → birth exit 2, 这是首次为项目建镜像的入口**: 你读项目信号 (AGENTS.md/README/package.json/pyproject.toml 等) 推导依赖件写成需求清单 (格式见镜像管理节), **展示清单与我确认后才落盘** — 装依赖会运行其安装脚本, 风险与日常装包同级, 确认时向我明示; 落盘后重跑 birth.
- REUSE → 直接用.
- BUILD-NEW → birth 停出 DECIDE 并附清单; 我确认后由你跑 `image-prep build` (见镜像管理节), birth 不吞构建环节, 构建完成带 `--image <ref>` 重跑 birth.
在跑容器镜像有新版只在 STATE 标 `newer-available`, 不动存活容器.

**第三步: 执行 birth**
```text
uv run python scripts/swt.py birth [--repo <主仓>] --branch <母体分支名原文>
    [--base <源 ref>] [--name <容器名>]
    [--mode whitelist --allow <CIDR>]... | [--mode blacklist [--deny <CIDR>]...]
    [--image <ref>] [--requirements <file>] [--new-mother | --reuse-mother]
```
母体分支名与母体目录名是同一个规范化名字 (use-worktree 的 slug 规则生成); 容器缺省名 `swt-<该名>`, 同母体第二个容器须显式 `--name`. 首次执行通常出 DECIDE (母体新建/复用, 网络模式, 镜像), 按决策协议节应答.

**第四步: 交付汇报**
向我报告:
- ssh 入口: `ssh -i <私钥> -p <宿主端口> agent@127.0.0.1`; 私钥落 `<records-root>/runtime/<identity>/ssh/` (0600), 随 terminate 清除.
- 宿主端口动态分配, 跨 stop/start 稳定; 用 `podman port <容器名>` 或 STATE 的 `ssh-port` 发现, 不记录端口 (rm 重建才变).
- 容器内路径契约: 用户 `agent`, 代码固定克隆在 `/home/agent/workspace` (当前分支 = 母体分支); skill 库在 `~/.agents/skills/`, pi 配置在 `~/.pi/agent/`.
完成标准: STATE `stage=born`, 容器内检出分支 = 母体分支, ssh 入口与端口发现方式已汇报给我.

## 存续

**ssh 入容器**: 经上方入口进容器驱动 pi 干活. 产物回流 = 容器内 `git push` (只允许历史只增不改的快进推送), **推送落地**使母体目录文件即时更新, host 直接审阅/试跑. 推送落地有秒级短延迟 (push 返回后文件稍后可读).

**herdr 接入与委派配方**: 容器不装 herdr; host 侧开窗格 `HERDR_AGENT=pi ssh -p <端口> -i <私钥> agent@127.0.0.1`, host herdr 经 env 提示把容器内 pi 识别为一等 agent. 委派配方:
1. `herdr agent get` 确认 idle — blocked/working 态不发 (无 guard 会把键打进错误界面).
2. `herdr pane send-text` 发任务文本.
3. 提交键 = 读容器内 `~/.pi/agent/keybindings.json` 的 `tui.input.submit` 首键 (跟随我的键位配置; 本机为 `alt+\`), 兜底 alt+enter.
4. `herdr agent wait` / `agent read` 收结果.
这套做法只是一层交互式编排的适配: 没有任务 id/退出码/重试保证, 别当 subagent 用. 保底形态: `pi -p "<任务>"` 批处理 (绕开 TUI 键位注入, 一轮一进程).

**展示链**: 容器内展示由 `present` skill 的容器分支全权负责 (判定/bind/端口/url 语义见其 "容器内分支" 节), 你侧只剩一项: host 侧用 `podman port` 发现映射端口, 组装交付 URL 给我.

**登录墙 (可选环节)**: 容器内需 headed 浏览器过登录墙时:
```text
uv run python scripts/login-wall.py build  --repo <主仓> --prefix localhost/sandbox-worktree --records-root <记录根>   # 浏览器项目层镜像
uv run python scripts/login-wall.py up     --image <项目层镜像> [--name <名>] [--geom 1920x1080x24]
uv run python scripts/login-wall.py verify --name <名> [--evidence-dir <目录>]
uv run python scripts/login-wall.py down   --name <名>          # 幂等
```
up 起容器并启动 VNC 栈 (Xvfb + x11vnc + websockify/noVNC), 交付 noVNC URL 给我浏览器操作; verify 做通道检查 (HTTP/ws/RFB/空白基线), 渲染阈值 0.2. 浏览器项目层清单 = `image/requirements-browser.md`; chromium 为 playwright 管理 (与 access-web 同源). 登录态 profile 落容器内 /tmp, 容器存续期内跨 ssh 会话复用, rm 即失. `build` 必传 `--repo` (image-prep build 缺省裸崩, 已知限制).

**多容器共推同一母体**: 允许. 容器只准快进推送, 后推的那个会被 git 以历史分叉为由拒绝: 容器内 `git fetch` → 解冲突 → 重推 (git 原生串行化, 无新机制).

**母体使用纪律 (转述给我)**: 母体目录是审阅现场: 只读/diff/试跑随意, **禁止编辑跟踪文件** — 母体工作区脏会拒容器 push (推送落地机制自带行为); 未跟踪文件 (编译产物等) 不阻塞. 审阅时不开会自动写文件的工具.

## 恢复 (resume)

```text
uv run python scripts/swt.py resume [--repo <主仓>] [--name <容器名>] [--confirm]
```

有 CLI 级 DECIDE gate: 检测到可恢复对象先 exit 1, 我确认后带 `--confirm` 重跑. 序列: 收残留 daemon → start 容器 → **start 后立即重注入防火墙规则** (合并式 `--merge`, 不做整表清空重建) → 校验通过前不开放工作负载. retired 容器 resume 直接 exit 2; 运行记录里的母体分支 ≠ 当前放行分支也 exit 2.
完成标准: 容器 running, 防火墙规则已重注入, daemon 可达, STATE 反映当前放行的母体分支.

## 换母体 (switch, 危险独立入口)

```text
uv run python scripts/swt.py switch [--repo <主仓>] --to <目标分支名原文> [--force]
```

同一主仓同一时刻只有一个分支对容器开放写. 换母体 = 停旧母体全部容器+daemon → 删防火墙规则 → 校验目标 → 改主仓 config 里放行的分支名. 旧容器**不删**, 标 **retired**: status 可见, resume 拒绝, 唯一出路 terminate (走正常脏检查). 想捡回旧分支 → switch 回去或重新 birth. 旧母体全部容器先脏检查, 脏 → DECIDE + `--force`. 目标母体分支不存在: 允许 (写面对象暂缺, 随后 birth 再建); 分支存在但母体工作区脏 / 无对应 worktree → exit 2.
完成标准: 旧容器全停并标 retired, config 里放行的分支已指向新目标, status 显示新母体.

## 终结 (terminate)

```text
uv run python scripts/swt.py terminate [--repo <主仓>] [--name <容器名>] [--force]
```

按容器粒度; `--name` 缺省 = 该母体唯一容器, 多容器必填. **脏检查口径**: 未提交改动 (含未跟踪文件) 算脏; 容器里有而母体没有的提交 (领先或分叉) 算脏, 只是落后于母体不算脏; 查不了 (ssh 不通/容器已停) 一律按脏处理. 脏 → DECIDE 出示脏概要, 文案含 "确认容器内 agent 已停手"; 我确认带 `--force` 重跑, 先写 `audit.jsonl` 审计登记再删. 成功后: 删防火墙规则 → rm 容器 → 最后一个容器终结才收 daemon. **母体目录与主仓 config 不动**; 母体存删我自决 (删母体走 use-worktree 流程).
完成标准: 目标容器与 (最后一个容器时) daemon 已灭, 母体目录与主仓 config 原样留存, 运行记录与 ssh 私钥已清除.

## 镜像管理 (image-prep)

```text
uv run python scripts/image-prep.py build-base [--requirements <file>]   # base 层
uv run python scripts/image-prep.py match      --repo <主仓> [--requirements <file>]
uv run python scripts/image-prep.py build      --repo <主仓> [--requirements <file>]
```

- 两层结构: **base 层** (OS+git+sshd+node+pi CLI+uv+fd+rg+python3 + skill 库全量 COPY + `~/.pi/agent` 复制, 排除 auth.json/sessions) 固定且跨项目共享; **项目层**由你读项目信号推导依赖件叠加, 清单与我确认后才构建.
- 需求清单条目 = 名称 + 版本要求 (`>= <= > < ==` 或裸名称), 指令 `install=`/`probe=` (探测缺省 `<name> --version`); apt 条目必须写 `install=` (只写 probe 不装包).
- 匹配规则: 按镜像 label 找候选取最新构建 → 需求逐项版本满足 + 硬性条件 "基于当前 base 构建" (base 更新后旧项目镜像自然淘汰) → REUSE, 否则 BUILD-NEW. 旧镜像保留不删.
- 版本语义: tag = 日期-序号 (人读索引), digest = 镜像内容哈希即精确版本; contents.md = 构建后**实测**清单.
- **base 只在我明说 "更新 base" 时重建**, 无自动检测.
- 记录落 `<records-root>/<slug>/builds/<build-id>/` (Containerfile/requirements.md/contents.md/build.json), 不落项目 git.
- 门禁类扩展 (filesystem-operation-gate 等) 留 host 不进容器; host 环境文档 (`~/AGENTS.md`/`~/docs/`) 不进容器.

## 网络控制 (net-firewall, 一般由 swt 编排)

正常路径不需要直接调用 — birth/resume/terminate/switch 自动注入与回收. 手救场用:
```text
uv run python scripts/net-firewall.py show                    # 列当前规则表
uv run python scripts/net-firewall.py remove --container-ip <IP>
uv run python scripts/net-firewall.py clear                   # 删整表 (幂等)
```
机制: 规则注入容器所在网络命名空间的自有表 `inet swt`, 按容器源地址限定, 容器内任意 uid (含 root) 不可达不可删. 容器停 → 命名空间拆 → 规则全失是固有形态, 故每次 start 后必须重注入. 多容器共享一张表: apply 不带 `--merge` 见别的容器规则即拒 (APPLY-CONFLICT).

## 决策协议 (DECIDE + 收据)

swt 五子命令非交互, 一切拍板点:
1. **exit 1 + stdout DECIDE 行**: `DECIDE <id> <kind> <问题人话> 选项: <flag 形态>`; 首次改任何资源前一次列全.
2. 逐字转述给我; 我答后带对应 flag **重跑同一命令**.
3. **决策收据** (定义见文首术语): 重跑先比对资源状态, 变了就废票重新问 — 旧答案绝不套到新状态上.
4. 执行中途新冒出的问题不是 DECIDE, 走 exit 3 PARTIAL.

exit code 全子命令统一:

| code | 含义 |
| --- | --- |
| 0 | 成功 (含幂等 no-op) |
| 1 | DECIDE 待我 |
| 2 | 前置不满足 (未动任何资源, 别重试同一命令) |
| 3 | 中途失败可重入 (PARTIAL 文案列唯一人工恢复路径) |
| 4 | 环境错误 (podman/git/nft 缺失或版本不支持) |

stdout 末行 `STATE {...}` 单行 json (只加字段不改名); stderr 首行 `FAIL|PARTIAL|ENV <人话>`, 原生报错原文透传.

## 原生报错译解表

| 原生报错 | 含义与处置 |
| --- | --- |
| `deny updating a hidden ref` | push 目标不在允许写入的范围内 (新分支/tag/删除); 容器只准推母体分支 |
| `denying non-fast-forward` | 母体分支有别人/别容器的新提交; 容器内 fetch → 解冲突 → 重推 |
| `Working directory has unstaged changes` | 母体目录跟踪文件被 host 侧改脏; 还原本体改动后重推 |
| `Address already in use` (pasta, exit 125) | 容器宿主端口被占, start 失败; 不自动换端口, 释放端口或重建容器 (exit 3 可重入) |
| `APPLY-CONFLICT` | 防火墙表内有其他容器规则, apply 拒覆盖; 走 swt 编排 (--merge) 不手调 |

## 风险明示 (向我声明)

- **auth.json 只读挂载**进容器: 防写回 host, 不防读 — 容器内恶意依赖可读 token 并经白名单内 LLM 域名外传, 已接受.
- **git 守护进程无认证/审计**: 只靠 "同一时刻只有一个分支可写" 的拓扑防容器 agent 越权; 监听落 0.0.0.0 时, 局域网内其他机器也够得着这个受限写入口 (只能快进推母体分支).
- **whitelist 自动放行 daemon 地址** = 容器可经网关地址访问 host 全部对外监听 (非仅本机回环) 的端口, 按 IP 放行无法收窄到单端口; 出访互联网方向仍收敛.
- 容器物理可读主分支最新提交 (git 协议广告藏不掉), 已接受.
- 主仓 config 常驻: 不影响主仓 push 真远端, 但**手动 push 进主仓会被拒**.

## 容器命令收拢 (provider 扩展点)

全部容器操作命令集中此节, 换/加 provider 时只改这里:
- 生命周期: `podman create --name <名> --label ... -p 22 [-p 8800] [-p 6080] <镜像>` / `podman start|stop|rm -f`
- 端口发现: `podman port <容器名>`; 状态: `podman ps -a --filter label=sandbox-worktree.repo=<主仓>`
- 镜像: `podman build` / `podman images --filter label=run.sandbox-worktree.project-id=<主仓路径>` / `podman inspect`
- 容器内操作: `podman exec` (key 注入/swt-vnc); 防火墙注入: `podman unshare nsenter --net=<容器网络命名空间> nft -f -`
- daemon 发现: `pgrep -f 'git daemon.*<主仓路径>'`

## 救场 (无修复原语)

swt 无 config/daemon 修复子命令. exit 3 的 PARTIAL 文案给出该半状态的唯一人工恢复路径; 更深的救场由你敲原生命令: `git config --get-all` / `pgrep -f 'git daemon'` / `net-firewall.py show` / `podman ps -a`, 诊断后手工收敛. 真实救场需求暴露时回报我.
