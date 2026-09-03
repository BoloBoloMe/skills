# worktree 拓扑实测 findings

日期: 2026-09-03
Git: `git version 2.53.0`

## 1. 实验边界与基线

实验仓库全部位于临时目录 `/tmp/worktree-topology.4ENGpv`, 已在本报告完成后删除. 拓扑如下:

```text
main 仓库工作区: /tmp/worktree-topology.4ENGpv/main, 检出 main
linked worktree: /tmp/worktree-topology.4ENGpv/wt-work, 检出 wt-work
服务: git daemon --enable=receive-pack --base-path=/tmp/worktree-topology.4ENGpv
URL: git://127.0.0.1:24753/main
```

初始化命令的关键部分:

```bash
git init -b main main
git commit -m initial
git branch wt-work
git -C main worktree add ../wt-work wt-work
git -C main config receive.denyCurrentBranch updateInstead
touch main/.git/git-daemon-export-ok
git daemon --enable=receive-pack --base-path="$LAB" \
  --listen=127.0.0.1 --port="$PORT" "$LAB"
```

实验前置背景与原方案位置: 工作树 gate 的 `updateInstead` 假设见 `docs/changes/use-sandbox-worktree/2026-09-01-research.md:104-110`, 共享 hooks 的副作用见同文件 `:114`, 当前决策中的独立 daemon/专用目录纪律见 `docs/changes/use-sandbox-worktree/DECISIONS.md:26-36`.

## 2. 实验结果

### 2.1 updateInstead 与两个工作树

命令:

```bash
git clone "$URL" client-a
# 在 client-a 创建 commit a5e0019
printf 'wt-v2\n' > client-a/state.txt
git -C client-a commit -am 'wt update'
git -C client-a push origin HEAD:refs/heads/wt-work

# 在同一 client 创建下一 commit 3adb8b1
printf 'main-v2\n' > client-a/state.txt
git -C client-a commit -am 'main update'
git -C client-a push origin HEAD:refs/heads/main
```

结果:

| push 目标 | daemon/receive-pack | push 后工作区 | 结论 |
| --- | --- | --- | --- |
| `refs/heads/wt-work` | 接受, `3bfdb48..a5e0019` | `wt-work/state.txt` 立即为 `wt-v2` | `updateInstead` 会识别 linked worktree 的当前分支 |
| `refs/heads/main` | 接受, `3bfdb48..3adb8b1` | `main/state.txt` 立即为 `main-v2` | 也会更新主工作区检出的分支 |

两次都是 push 返回成功后立即检查文件, 无需 checkout/fetch/额外同步. 这直接验证了 `push 即落地`, 与既有 `DECISIONS.md:64-67` 的事实一致, 但本轮同时覆盖了 linked worktree 分支.

### 2.2 无 hooks 的默认写面

此轮未安装任何 hook, 仓库仍只有 `receive.denyCurrentBranch=updateInstead`. 测试命令形态:

```bash
git push --force origin HEAD:refs/heads/wt-work
# create and push refs/heads/exposed-new
git push origin HEAD:refs/heads/exposed-new
# create and push refs/tags/exposed-tag
git push origin refs/tags/exposed-tag
git push origin :refs/heads/exposed-new
git push origin :refs/heads/wt-work
git push origin :refs/heads/main
```

| 操作 | 结果 | 关键返回/现象 |
| --- | --- | --- |
| `wt-work` non-ff force push | 接受 | `a5e0019...94fcfc3 HEAD -> wt-work (forced update)`, linked 文件变为 `wt-rewrite` |
| 创建新分支 | 接受 | `* [new branch] HEAD -> exposed-new` |
| 创建 tag | 接受 | annotated tag `exposed-tag` 推送成功 |
| 删除普通分支 `exposed-new` | 接受 | `- [deleted] exposed-new` |
| 删除 linked worktree 当前分支 `wt-work` | 拒绝 | `deletion of the current branch prohibited` |
| 删除主工作区当前分支 `main` | 拒绝 | 同上 |

这里的两个删除拒绝来自 Git 默认 `receive.denyDeleteCurrent`, 不是 hooks, 且`当前分支`包括 linked worktree 检出的分支. 删除普通分支则没有这层保护. `updateInstead` 并不提供分支 allowlist 或 non-ff 门禁.

### 2.3 `receive.denyNonFastForwards` + `receive.denyDeletes`

配置:

```bash
git -C main config receive.denyNonFastForwards true
git -C main config receive.denyDeletes true
```

结果:

| 操作 | 结果 | 关键返回/现象 |
| --- | --- | --- |
| force non-ff 到 `wt-work` | 拒绝 | `denying non-fast-forward refs/heads/wt-work` |
| 创建新分支 `policy-new` | 接受 | 创建本身不是 non-ff, 仍成功 |
| 创建 tag `policy-tag` | 接受 | 新 tag 仍成功 |
| 删除普通分支 | 拒绝 | `denying ref deletion` |
| 删除 `wt-work` | 拒绝 | `denying ref deletion` |
| 删除 `main` | 拒绝 | `denying ref deletion` |

副作用范围实测:

```bash
git -C main branch host-local-ref
# 成功, 本地 ref 操作未被阻止

git init --bare outbound-2.git
# 从 main 仓库向另一个 receiver 先建立分支, 再制造 receiver 的分叉
# 最后从 main 仓库执行:
git -C main push --force outbound-2.git \
  refs/heads/main:refs/heads/outbound-probe
```

最后一次向独立 receiver 的 force push 成功, 返回 `+ 55f8640...3adb8b1 ... (forced update)`. 因此这两项是 receive-pack 端配置: 它们约束`谁接收这个仓库的 push`, 不约束本地建分支, 也不改变该仓库作为发送方 push 到正常远端的行为. 对用户日常`只 push 到远端, 不 push 回自己的工作仓`流程无直接副作用; 只要某个仓库被当作 receive 端, 该仓库接收规则会受影响.

### 2.4 `uploadpack.hideRefs` 与 `receive.hideRefs`

#### 2.4.1 只隐藏 upload 侧的 `main`

```bash
git -C main config uploadpack.hideRefs refs/heads/main
git ls-remote "$URL"
git clone "$URL" client-hidden-upload
```

`ls-remote` 不再列出 `refs/heads/main`, 但仍列出:

```text
3adb8b1... HEAD
... refs/heads/host-local-ref
... refs/heads/policy-new
... refs/heads/wt-work
... refs/tags/exposed-tag
... refs/tags/policy-tag
```

clone 成功, 但由于远端 `HEAD` 仍指向被隐藏的 `main`, 默认 checkout 结果是 detached HEAD, 并提示 `正在切换到 '3adb8b1...'`. clone 不会自动把 `wt-work` 作为默认分支. `refs/remotes/origin/main` 不存在, 但 HEAD 对应的 main 对象本身仍被泄露.

只设置 `uploadpack.hideRefs` 不阻止显式写入 main. 随后向 main 做 fast-forward push 成功, 主工作区更新了 `upload-hide-push` 文件.

#### 2.4.2 `receivepack.hideRefs` 不是有效的 receive 配置键

曾设置:

```bash
git -C main config receivepack.hideRefs refs/heads/main
```

在未设置正确 `receive.hideRefs` 时, 向 main 的 push 仍成功. 该键对本次 Git 2.53.0 的 receive-pack 没有产生隐藏/拒写效果. 正确的仓库配置键是 `receive.hideRefs`.

设置:

```bash
git -C main config receive.hideRefs refs/heads/main
```

之后向 main 的 fast-forward push 返回:

```text
! [remote rejected] HEAD -> main (deny updating a hidden ref)
```

`receive.hideRefs` 不会替代 upload 侧隐藏: 只设置它时, `ls-remote` 仍会看到 main. 两个方向需分别配置.

#### 2.4.3 用前缀 + 否定例外只广告 `wt-work`

Git 2.53.0 接受多个 hideRefs 值及 `!` 否定例外:

```bash
git -C main config --add uploadpack.hideRefs refs/heads
git -C main config --add uploadpack.hideRefs '!refs/heads/wt-work'
git -C main config --add uploadpack.hideRefs refs/tags
```

此时 `ls-remote` 仅为:

```text
d28989d... HEAD
19ef794... refs/heads/wt-work
```

clone 仍 detached 在 `HEAD` 对应的 main 对象, 但 remote-tracking refs 只有 `origin/wt-work`. 因此`只看见 wt-work`可以做到 ref 列表层面, 但无法用 hideRefs 消除协议保留的 HEAD 广告; 若要默认 clone 检出 wt-work, 还需让仓库 HEAD 指向 wt-work, 这与主工作区当前检出 main 的目标冲突.

### 2.5 receive 侧 hideRefs 收敛写面

为验证不靠 hook 的完整收敛, 配置:

```bash
git -C main config --add receive.hideRefs refs/heads
git -C main config --add receive.hideRefs '!refs/heads/wt-work'
git -C main config --add receive.hideRefs refs/tags
git -C main config receive.denyNonFastForwards true
git -C main config receive.denyDeletes true
```

同一轮也使用了上节的 uploadpack 配置. 没有任何拒绝型 hook, 仅保留一个后续用于日志的允许型 hook.

| push 操作 | 结果 | 关键返回 |
| --- | --- | --- |
| `wt-work` fast-forward | 接受, 工作树即时更新 | `19ef794..fea7801 HEAD -> wt-work` |
| 创建新分支 | 拒绝 | `deny updating a hidden ref` |
| 创建新 tag | 拒绝 | `deny updating a hidden ref` |
| `main` fast-forward | 拒绝 | `deny updating a hidden ref` |
| 删除已有普通分支 | 拒绝 | `deny deleting a hidden ref` |

所以在配置不被 host 侧改写且 Git 版本支持否定例外的前提下, receive 侧可把协议写入面收敛为 `refs/heads/wt-work` 的允许更新; `denyNonFastForwards` 再将它收敛为 fast-forward. 这是 ref 级收敛, 不是内容级策略: agent 仍可在允许分支中提交任意内容.

### 2.6 per-worktree `core.hooksPath`

准备:

```bash
git -C main config extensions.worktreeConfig true
git -C wt-work config --worktree core.hooksPath "$LAB/worktree-hooks"
```

在共享 hooks 目录安装允许型 `pre-receive`, 它记录 `hook=shared` 和完整环境; `$LAB/worktree-hooks/pre-receive` 记录 `hook=worktree`. 然后经 daemon push 到 `wt-work`, 输出:

```text
hook=shared
GIT_DIR=.
PWD=/tmp/worktree-topology.4ENGpv/main/.git
GIT_PUSH_OPTION_COUNT=0
REMOTE_ADDR=127.0.0.1
```

没有出现 `hook=worktree`. 同一 shared hook 对 push 到 main 也会运行, 说明 receive-pack 使用的是仓库共享 hooks 配置/目录, 不会按将被更新的 linked worktree 选择其 `config.worktree`. 结论是 per-worktree hooksPath 不能作为 daemon receive-pack 的门禁隔离手段. 这与既有对共享 hooks 误伤主仓的风险记录 `2026-09-01-research.md:114` 相吻合.

### 2.7 daemon 来源环境识别

同一 shared hook 分别记录 daemon transport 和本地 file transport:

| push 来源 | hook 中观察到的变量 |
| --- | --- |
| `git://127.0.0.1:PORT/main` | `REMOTE_ADDR=127.0.0.1`, `GIT_DIR=.`, `PWD=.../main/.git`, `GIT_PUSH_OPTION_COUNT=0` |
| 直接 push 到 `/tmp/.../main` | 无 `REMOTE_ADDR`, 其余基础变量相同 |
| daemon push 且客户端 `-c protocol.version=2` | 仍有 `REMOTE_ADDR=127.0.0.1`, hook 中无 `GIT_PROTOCOL` |

daemon verbose log 确实记录了 `Extended attribute "protocol": version=2` 和 `Request receive-pack`, 但 Git 2.53.0 没有把 `GIT_PROTOCOL` 传给 receive hook. `SSH_CONNECTION`/`SSH_ORIGINAL_COMMAND` 也未出现.

可识别性不是不可伪造的安全凭据. 实测执行:

```bash
REMOTE_ADDR=203.0.113.9 git -C client-a push "$LAB/main" \
  HEAD:refs/heads/wt-work
```

本地 file transport 的 hook 随即观察到 `REMOTE_ADDR=203.0.113.9`. 因此 hook 可以用`daemon 正常会设置 REMOTE_ADDR, 本地通常没有`作来源分流, 但本地调用者能向子进程注入同名环境变量; 该条件不适合作为对抗恶意本地调用者的强认证. 在本实验威胁模型中, 容器只能经 daemon 到达 gate, 这个信号足以支持`仅 daemon 来源执行规则`的折中, 但必须明确其信任边界.

## 3. 结论回答

### (a) 无 hooks 时容器写面到底多大

默认 non-bare receive 行为远大于`只写 wt-work`:

- `wt-work` 可 fast-forward, 也可 force non-ff; 接收成功会即时改写 linked worktree 文件.
- 任意新分支可创建, 任意普通分支可删除.
- 任意新 tag 可创建.
- `main` 和 `wt-work` 的删除受默认 `denyDeleteCurrent` 保护, 但这是`当前分支不许删`, 不是允许列表.
- 未隐藏的 main 或其他分支也可被 push 更新; `updateInstead` 会更新对应检出的工作区.

因此无 hooks 时写面是整个仓库的 refs 写面, 只有默认的当前分支删除保护和 `updateInstead` 的工作区干净性保护. 这不能满足分支 allowlist.

### (b) config + hideRefs 能收敛到什么程度, 残余风险是什么

组合 `receive.denyNonFastForwards=true`, `receive.denyDeletes=true`, `receive.hideRefs=refs/heads` + `!refs/heads/wt-work` + `refs/tags`, 可在本实验版本把 receive 写面收敛到:

```text
仅 refs/heads/wt-work, 且仅 fast-forward 更新
```

upload 侧用同样的 `uploadpack.hideRefs` 组合, clone/fetch 的 ref 广告可收敛到 `wt-work`, 但 `HEAD` 仍广告其对象, 默认 clone 仍 detached 在 main 对象上. `uploadpack.hideRefs` 单独不防 push; 必须同时配置正确的 `receive.hideRefs`, 不是 `receivepack.hideRefs`.

残余风险:

- 这是 host 仓库配置的策略, 不是不可变 allowlist; 能修改该仓库 config 的 host 进程可以撤销限制.
- daemon 无认证; 能到达 daemon 的对端共享同一 gate 身份和 ref 写权限.
- `wt-work` 内仍可提交任意内容, 配置只约束 ref 名称, 方向, 删除.
- `updateInstead` 依赖目标工作树 tracked 文件干净; 脏工作区会拒收, 这需要编排侧管理.
- hideRefs 解决可见性和 receive 目标过滤, 不解决对象内容泄露: HEAD 以及由可见 commit 可达的对象仍可能被获取.
- 生产必须维持单 gate 专属 base-path, 不开 `--export-all`, 避免服务端点写穿其他仓库; 该拓扑教训见 `2026-09-01-research.md:100`.
- `!` 否定规则与当前 Git 版本有关, 部署时应使用目标 Git 版本重跑兼容性检查.

### (c) per-worktree 钩子或 daemon 识别是否可行

- per-worktree `core.hooksPath` 不可行: daemon receive-pack 未执行 linked worktree 的 hooksPath, 只执行共享 hooks.
- daemon 来源识别可行但仅是环境信号: `REMOTE_ADDR` 在 daemon hook 中出现, 本地 file transport 默认没有; `GIT_PROTOCOL` 不可依赖.
- 因而`共享 pre-receive 中仅当 REMOTE_ADDR 存在时执行 daemon 门禁`可以作为折中方案, 但不是密码学隔离. 本地调用者可注入 `REMOTE_ADDR`, 该方案只适用于`容器网络只能走专属 daemon, host 本地调用者受信`的威胁模型.

## 4. 对设计的直接建议

如果目标是无 hooks 的实验性 gate, 推荐配置模板为:

```ini
[receive]
    denyCurrentBranch = updateInstead
    denyNonFastForwards = true
    denyDeletes = true
    hideRefs = refs/heads
    hideRefs = !refs/heads/wt-work
    hideRefs = refs/tags
[uploadpack]
    hideRefs = refs/heads
    hideRefs = !refs/heads/wt-work
    hideRefs = refs/tags
```

配套约束仍不可省略: 每个 gate 一个 daemon, `base-path` 目录只含该 gate, 不使用 `--export-all`, daemon 生命周期绑定容器, host 侧保护配置和工作树. 该无 hooks 方案可以达到 ref 级`只收 wt-work ff`, 但若需要人话拒绝信息, 内容级校验, 或更强审计, 仍需 shared pre-receive, 并可用 `REMOTE_ADDR` 作来源分流信号.
