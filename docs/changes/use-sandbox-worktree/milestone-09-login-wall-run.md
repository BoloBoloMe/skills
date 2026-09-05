# MILESTONE-09 登录墙实现结果 (ISSUE-04)

日期: 2026-09-06. 验证: `uv run --with pytest pytest tests/test_swt_m09.py` (31 用例全绿, ~7 分钟含镜像构建); 真链路 dogfood 实跑见下.

## 交付物

- `workflow/use-sandbox-worktree/scripts/login-wall.py`: build (薄封装 image-prep) / up / down / verify 四子命令
- `workflow/use-sandbox-worktree/image/requirements-browser.md`: 浏览器项目层清单 (7 条目: xvfb / x11vnc / websockify / novnc / fonts-noto-cjk / chromium / swt-vnc)
- `tests/test_swt_m09.py`: 31 用例 (TS-001 RFB 纯逻辑 5 + ws/compose 单元 12 + TS-002 镜像 2 + TS-003 up 流 4 + TS-004 通道 2 + TS-005 渲染 2 + build 封装 4)
- `issues/ISSUE-04-login-wall.md`: 可执行 ISSUE (含最小接缝补钉清单)
- 容器内 swt-vnc helper (base64 内嵌于清单): Xvfb :99 (-ac -noreset, GEOM 归一化校验) + x11vnc (-nopw -forever -shared) + websockify (0.0.0.0:6080 → 5900)

## 真链路 dogfood 实测 (2026-09-06, 真记录根 ~/.agents/sandbox-worktree/)

- 真实 base 构建: `localhost/sandbox-worktree/base:2026.09.06-1`, 1m45s (层缓存复用)
- 项目层构建: `localhost/sandbox-worktree/skills:2026.09.06-1` (slug=skills), 4m35s (chromium 下载为主)
- up → verify → down 全过: 6 检查 OK — noVNC HTTP 200 / ws 握手 101 / 经 websockify RFB banner / 空白基线 non_black=0.0019% / headed 渲染 non_black=30.19% / headless 回切成功; 截图 PPM 落宿主 evidence 目录; down 后无容器残留
- 渲染占比实测 30.19%: 窗口固定 1280x720 (access-web --window-size, 零改动) + UI 栏非黑 + 40vh 黑条, 在 1920x1080 屏上边缘过线 → 阈值定为 0.2 (留健康余量, 基线 <1%)

## 过程中实锤的实现级事实 (不在任何权威输入中, 已按最小方式处理)

1. GEOM 两段式 (WxH) 使 Xvfb 直接 Fatal 退出 — 归一化下沉 swt-vnc 脚本 (WxH→WxHx24 + 段数/上限校验), up 原样透传 (总指挥裁决).
2. x11vnc 缺省首客户端断开即退出 — 加 `-forever -shared`.
3. swt-vnc status 端口 hex 曾错 (5900=0x170C 写成 0x1704, 差 8) — 双轴 review 抓出修正.
4. `podman images --filter reference=<prefix>*` 的 glob 不跨 `/` — 测试清理 rmi 历轮静默失效, 泄漏 34 镜像; 修为 `prefix*/*`.
5. `podman cp` 目标目录不存在直接失败 (rc 125) — verify 现对 evidence-dir 一律 mkdir -p; 该 dogfood bug 由真链路实跑暴露, 测试补嵌套路径用例.
6. requirements 清单的 apt 条目必须写 install= (只写 probe 不装包, 会借 playwright --with-deps 顺带装的包欺骗性通过); probe 内 dpkg-query `${Version}` 单引号保护即可穿过 shlex 与容器 sh.
7. playwright 新布局浏览器在 `chromium-<rev>/chrome-linux64/`; 容器内以 root exec 时须注入 HOME=/home/agent, 否则 playwright 找 /root/.cache 漏掉项目层 chromium.
8. image-prep `build` 缺 `--repo` 时裸 TypeError 崩 (M07 领地未改, login-wall build 封装必传 --repo 规避).

## 3840 翻倍疑点 — 挂起档案

TS-003 验收期收到一条无法溯源的转述 (`assert 1920 == 3840`, 疑 RFB 宽度翻倍). 排查: 复现 0/21 (单用例 + 同镜像 up→RFB→down 高压 20 轮), 本机无失败 run 痕迹, 转述格式与任何现存断言的 unittest 输出不吻合, 代码无产出 3840 的路径. 用户确认原文找不回且非本人操作. 挂起: 不阻塞; 若复现 (TS-005/实跑中 RFB 尺寸再异常), 优先怀疑容器时钟/多 X 客户端/旧脚本镜像三类现场并留容器验尸. 完整档案: 会话内 /tmp/m09/3840-suspended.md (易失, 本节即沉淀).

## 待用户追认 (ISSUE-04 最小接缝补钉节)

1. VNC 栈/chromium 全进项目层 (base 不动).
2. swt-vnc 为容器内 helper (start/stop/status), host 经 podman exec 调用; M11 盘问五场景时可调整.
3. "登录态落 profile volume" 按 ADR 0003 现实修正: profile 落容器内 /tmp, 容器存续期内跨 ssh 会话复用, rm 即失, 不加 volume.
4. 渲染阈值 0.2 与实测几何 (见上).
5. chromium 装法 = playwright 管理的 chromium (非 apt), 与 access-web 驱动链同源.

## 边界与遗留

- 五场景 host 入口/容器创建 label/通用化端口分配: 未做 (M11/M12 领地).
- verify 的 noVNC URL 交付形态 (host LAN 地址可选) 留 M11 汇报形态定夺; 当前输出 127.0.0.1.
- M03 回归 (test_swt_m03.py) 未在本轮跑 (ISSUE-04 禁止范围未动 M03 契约文件, 风险低).
