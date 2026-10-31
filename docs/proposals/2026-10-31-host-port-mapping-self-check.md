# 提案: 宿主端口映射的自查顺序 (2026-10-31)

- 性质: 改进提案, 不改代码. 触发自一次真实的交付事故
- 涉及文件: `workflow/use-sandbox-worktree/agent-prompts/ENV.md`, `workflow/use-sandbox-worktree/scripts/env_docs.py` (`_web_ports`), 以及可能受影响的 `tests/test_env_docs.py`
- 结论一句话: 端口变量缺失时, 现在的文档只写了"问人", 没写"先自查"; 而这次变量根本没缺, 只是没进新 shell

## 1 事故经过

容器 `swt-refactor-skill-around-verification` 里交付 present 页面, 需要拼给用户在宿主侧能打开的 URL. 实际发生的顺序:

1. 按 present skill 的远程容器分支, 容器内 8800 起服务并锁定端口, 成功.
2. 查当前 shell: `env | grep SWT_` 只看到 `SWT_AGENT_CLIENT_KEY` / `SWT_MAILBOX_URL` / `SWT_SESSION_*`, 没有 `SWT_HOST_*`.
3. 据此判定"宿主端口变量缺席", 按 `~/docs/web-ports.md` 的降级条款去发信箱, 宿主会话离线, 回头问用户.
4. 用户连问两轮后指出我该自己查. 执行:

   ```bash
   for p in /proc/[0-9]*/environ; do
     tr '\0' '\n' < "$p" 2>/dev/null | grep -E '^SWT_HOST'
   done | sort -u
   ```

   立刻拿到全套: `SWT_HOST_LAN_IP=192.168.65.165`, `SWT_HOST_WEB_PORT=41141`, `_2=34403`, `_3=33671`, `_4=36951`, `_5=33529`, `_6=36703`.
5. 正确 URL 也就出来了: `http://<LAN_IP>:41141/<页面>`. 从"没配"到"配了, 就在手边", 代价是三轮对话.

## 2 根因

**根因 A: 我查错了地方.** 这些变量在容器 create 时注入到当时那个进程的环境里, 之后新起的 shell, herdr 新建的 tab 都不继承. 所以"我的 shell 里没有"不等于"容器没配". 我该扫全进程环境, 而不是只看自己这一层.

**根因 B: 文档只写了升级路径, 没写查找顺序.** `web-ports.md` 里那句 "从 env 读取; 变量缺席时信箱可用就向宿主索取, 否则请我提供" 连起来读, 就是"没看到 → 问人". 它既没定义"哪个 env", 也没给出"变量缺席"之前的自查动作, 因此无法把"没配"和"没继承"这两种完全不同的情况区分开.

**根因 C: 两处文档信息不对称.** `present` skill 的 `REMOTE.md` 写明"服务自报的 url/hostname/lan_ip 是容器视角, 不要直接交付或猜测 host 地址", 而 `web-ports.md` 没有这句. 只读后者的人 (比如我) 会缺这一块判断依据.

## 3 提案

### P1 改写 `agent-prompts/ENV.md` 的容器纪律那句

改前:

```text
对外 web 发布到局域网且无认证, noVNC 屏幕无密码且对我可见; 只展示愿意公开的内容, 屏幕上避开密钥. 自测用容器 `127.0.0.1`, 给我的 URL 只用已确认宿主地址/映射端口; 缺值经可用信箱向宿主索取, 否则问我, 不猜.
```

改后:

```text
对外 web 发布到局域网且无认证, noVNC 屏幕无密码且对我可见; 只展示愿意公开的内容, 屏幕上避开密钥. 自测用容器 `127.0.0.1`, 给我的 URL 只用已确认宿主地址/映射端口. 缺值先按 ~/docs/web-ports.md 的自查顺序查 (当前 env → 容器内全进程 environ → 技能文档配方), 仍未找到再经可用信箱向宿主索取, 信箱不可用才问我; 不猜.
```

要点: 把"查"从"问"里拆出来, 并指出自查入口在 `web-ports.md`.

### P2 在 `env_docs.py::_web_ports` 里补自查顺序与视角说明

改前 (`web-ports.md` 第二行):

```text
- 宿主端口映射: 容器内 8800-8805 对应宿主环境变量 SWT_HOST_WEB_PORT, SWT_HOST_WEB_PORT_2.._6; create 后才知, 从 env 读取; 变量缺席时信箱可用就向宿主索取, 否则请我提供缺失的宿主地址/映射端口.
```

改后 (建议文本, 生成器里按行拼):

```text
- 宿主端口映射: 容器内 8800-8805 对应宿主环境变量 SWT_HOST_WEB_PORT, SWT_HOST_WEB_PORT_2.._6; 端口每次 create 都变, 不要写死.
- 自查顺序 (先查后问): 1) 当前 shell 的 `env`; 2) 缺了就扫容器内全进程, 这些变量在 create 时注入到当时进程, 常不继承给新 shell 或新 tab, 看不到不代表没配:
  `for p in /proc/[0-9]*/environ; do tr '\0' '\n' < "$p" 2>/dev/null | grep -E '^SWT_HOST'; done | sort -u`
  3) 两步都没有才算缺失, 再走下方降级, 不要凭第 1 步失败就下"没配"的结论.
- 交付形状 (端口以自查结果为准): `http://<SWT_HOST_LAN_IP>:<SWT_HOST_WEB_PORT>/<页面文件>`.
- 服务自报的 `url`/`hostname`/`lan_ip` 是容器视角, 不要直接交付; 宿主地址一律取 `SWT_HOST_LAN_IP`.
```

最后一条与 `REMOTE.md` 对齐, 消掉根因 C. 样例只给形状不给具体端口, 避免过期数字被当成事实.

### P3 补一条验收测试 (可选但值得)

`tests/test_env_docs.py` 现有断言都是关键词与段落的存在性检查 (`SWT_HOST_WEB_PORT`, 架桥配方各步, 未确认时的占位). 建议再加一条断言: 生成的 `web-ports.md` 文本里出现 `/proc/[0-9]*/environ` 与 `SWT_HOST_LAN_IP` 两个关键词, 保证这段自查指引不会被后续重构删掉而不报错.

## 4 怎么验证提案有效

在任意一个新建容器里, 不依赖人, 只按 `web-ports.md` 走到能拼出局域网 URL, 计时. 通过标准: 只在容器内操作, 不发信不提问, 5 分钟内拿到形如 `http://<LAN_IP>:<PORT>/` 的可访问地址. 这次事故的对照值是三轮对话加近十分钟.

## 5 落地归属

- 两个源文件都在本仓库 (`workflow/use-sandbox-worktree/`), 改完要按仓库常规跑 `uv run python -m pytest`, 涉及 `check_skill.py` 的文件另跑该检查.
- `~/docs/*.md` 是 `env_docs.render_docs` 的输出, 不存在独立母本, 所以不要手改容器里的 `~/docs/web-ports.md`, 改生成器.
- 本提案只记录问题与改法, 不代做改动: 具体实施建议单独开一个变更走正常流程, 免得与 `swt-container-env-docs` 的既有验收证据冲突.
