# ISSUE-04 登录墙: 容器内 VNC 通道 + headed 浏览器切换闭环

## 父级

- `../roadmap/MILESTONE-09.md` (M09 本体; 状态变更归 roadmap, 本文件不改其状态)
- `../2026-09-01-research.md` §5 (VNC 通道实测: Xvfb :99 1920x1080x24 `-ac -noreset` / x11vnc `-nopw` / noVNC 1.3.0 `?resize=scale` / vnc.html→index.html 软链兜底), §8 (`--shm-size=1g`, fonts-noto-cjk, 容器内服务 bind 0.0.0.0)
- `../../../docs/adr/0003-artifacts-in-temp-no-cross-reboot-login.md` (profile 会话级语义, access-web 零改动依据)
- `../DECISIONS.md` D014 (base 固定跨项目, 项目层按项目推导 — VNC 栈/chromium 属项目层), D015 (清单=名称+版本谓词+install=/probe=, 作者 host llm), D017/D024 (镜像记录/匹配, 经 image-prep 复用)
- M07 产物契约: `workflow/use-sandbox-worktree/scripts/image-prep.py` (build-base/match/build) + `tests/test_swt_m07.py`
- access-web 契约: `general/access-web/browse/browse.md` 环境变量表 (`BROWSER_HEADED=true` → headed chromium, 登录弹窗由人类操作); browser_agent 脱离式启动
- M08 同型先例: 8800 展示链动态宿主端口 + `podman port` 发现交付

## 执行(Execution)

- [x] 已实现

## 要构建什么

**定位**: 登录墙验证编排器, 不是 birth/五场景入口 (M11/M12 领地). 它证明: 容器内 VNC 通道 + `DISPLAY=:99 BROWSER_HEADED=true` 约定下, headed chromium 在 Xvfb 上渲染, host 经 noVNC 可见可操作, 之后回 headless.

1. `workflow/use-sandbox-worktree/image/requirements-browser.md` — 项目层清单 (D015 格式): `xvfb` / `x11vnc` / `websockify` / `novnc` / `fonts-noto-cjk` (apt 装) + `chromium` (`uv run playwright install --with-deps chromium`, 缓存落 /home/agent/.cache, 属主 agent) + swt-vnc 安装条目 (install= 写 /usr/local/bin/swt-vnc). probe 逐条实测 (apt 条目用 `dpkg-query -W -f=${Version} <pkg>` 取版本; chromium 用 playwright 装出的 chrome `--version`).

2. 容器内 helper `swt-vnc` (start/stop/status, 由清单 install= 写入 /usr/local/bin):
   - start 幂等: Xvfb :99 (`-ac -noreset`, 分辨率由 GEOM env 控制, 缺省 1920x1080x24) + x11vnc (`-display :99 -nopw -forever -shared`) + websockify (`--web /usr/share/novnc`, 监听 0.0.0.0:6080 → localhost:5900)
   - status: 三进程 + 端口 5900/6080 状态; stop: 全停
   - 容器内端口固定 5900/6080; 不改 base CMD (sshd 前台契约不动)

3. `workflow/use-sandbox-worktree/scripts/login-wall.py` — host 侧薄编排, 子命令:
   - `build`: subprocess 调 image-prep.py build (--requirements 缺省指向 requirements-browser.md; --prefix/--records-root 透传, 测试隔离用)
   - `up`: `podman run -d --shm-size=1g -p 22 -p 6080` 项目层镜像 → `podman exec swt-vnc start` → `podman port` 发现宿主端口 → 输出 noVNC URL `http://127.0.0.1:<port>/vnc.html?resize=scale`; 状态落 json (容器名/镜像/端口)
   - `verify`: (a) host 侧 noVNC HTTP 200 + websocket 握手 101 (raw Upgrade, stdlib) + 经 websockify 读到 RFB banner; (b) 容器内 python3 stdlib RFB 客户端连 127.0.0.1:5900 读 framebuffer: 分辨率=GEOM, 解码 raw 像素, 写 PPM, `podman cp` 回 host 作截图证据; (c) exec 容器以 `BROWSER_HEADED=true DISPLAY=:99 uv run python` 起 browser_agent chromium 并 navigate 到高对比测试页 → framebuffer 非黑占比超阈值; (d) 回 headless: 无 DISPLAY env 起 chromium 成功 (headless 不依赖 X)
   - `down`: 停容器 (`podman rm -f`)

4. `tests/test_swt_m09.py` — 按 TDD 切片.

## 最小接缝补钉 (权威输入未钉死, 待用户追认)

1. VNC 栈/chromium 全部进**项目层** (base 不动): 依据 D014 分层精神 + M07 run 报告预告 "浏览器二进制归 M09/项目层".
2. swt-vnc 属容器内 helper, 接口 start/stop/status 三动作; host 侧经 `podman exec` 调用. M11 盘问五场景时可调整, 不算冻结 host 接口.
3. "登录态落 profile volume" 按 ADR 0003 现实修正: profile 落容器内 /tmp (access-web 自身行为, 零改动), 容器存续期 (含 stop/start) 内跨 ssh 会话复用; rm 容器即失, 不加 volume.
4. x11vnc 加 `-forever -shared`: x11vnc 缺省首个客户端断开即退出, 与反复登录场景冲突; `-nopw` 沿调研 §5 (容器网络已有 nft 白名单约束).
5. chromium 装法 = playwright 管理的 chromium (`playwright install --with-deps`), 非 apt chromium — access-web 经 playwright 驱动, 二进制须同源.
6. 真实链路 (真 base + ~/.agents/sandbox-worktree/ 记录) 的首次 build-base 由产物实跑执行并记录; 测试全部走隔离 prefix/records-root.

## 允许范围

- 新建 `workflow/use-sandbox-worktree/scripts/login-wall.py`, `workflow/use-sandbox-worktree/image/requirements-browser.md`, `tests/test_swt_m09.py`
- 只读调用 (subprocess/读文件) `image-prep.py`; /tmp 测试夹具; 测试经 `--prefix localhost/swt-m09-*` + records-root 隔离
- 产物 `../milestone-09-login-wall-run.md` (含截图证据指针)

## 禁止范围

- 不改 `image-prep.py`, `e2e-smoke.py`, `net-firewall.py`, `image/Containerfile`, `tests/test_swt_m0*.py` (M03/M04/M07 契约)
- 不改 access-web / present 任何代码 (零改动硬约束)
- 不做五场景 host 入口/容器创建 label/宿主动态端口分配的通用化 (M11/M12 领地; 本 ISSUE 的 -p/--shm-size 只在 login-wall 闭环内)
- 不碰真实用户仓库; 不推送远端

## TDD 切片

- TS-001 (单元): RFB 客户端纯逻辑 — 假 RFB 服务器喂 banner/ServerInit/rect, 断言握手字节流, raw 帧解码, PPM 写出, 非黑占比判定 (阈值可注入).
- TS-002 (端到端, 网络重): 隔离 base (image-prep build-base, 真 skills staging) + requirements-browser.md build — probe 全过 (apt dpkg 版本 / chromium --version), swt-vnc 入镜像可执行, 字体包在位.
- TS-003 (端到端): up → swt-vnc start → Xvfb GEOM 分辨率生效 (framebuffer 尺寸), 5900/6080 监听 0.0.0.0, 宿主端口动态发现; swt-vnc status/stop 幂等正确.
- TS-004 (端到端): host 侧 noVNC HTTP 200 + ws 握手 101 + 经 websockify RFB banner; 空白 framebuffer 基线 (全黑, 证明链路本身不注入内容).
- TS-005 (端到端): BROWSER_HEADED=true + DISPLAY=:99 起 chromium 渲染高对比页 → framebuffer 非黑超阈值 + PPM 截图回 host; headless 回切成功; down 清容器后无残留.
