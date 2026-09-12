# 状态: 开放
# 类型: task
# 阻塞于: 无 (与 MILESTONE-10 并行)

## 问题

实现 D051 双模显示栈: 本机 wayland 直通 + VNC 保留兜底, 消掉 noVNC 在本机场景的三个短板 (窗口套窗口/软渲染/无法输中文).

依据: `../容器GUI无感访问技术报告.md`, `../DECISIONS.md` D051.

## 范围

1. swt.py birth/resume: 检测宿主机 `$XDG_RUNTIME_DIR/wayland-0` 存在 → `podman create` 恒挂 wayland socket + WAYLAND_DISPLAY/XDG_RUNTIME_DIR env + `--device /dev/dri`; 缺席时跳过并在 STATE 标注 (如 `host-display: absent`).
2. swt-display.py / display-check: 新增 wayland 直通探测一路 (容器内连 socket 实测), 与 noVNC 检查并列报告, 失败降级不阻断.
3. 容器内选路约定落地: headed 浏览器优先 `--ozone-platform=wayland`, 不可达回退 `DISPLAY=:99`; 写进 SKILL.md 显示栈节, 必要时同步 access-web/present 的容器分支描述.
4. SKILL.md 更新: 显示栈节 (双模语义), 容器命令收拢节 (新挂载参数), 风险明示节 (信任面扩大一条), birth/resume 交付汇报 (本机场景补 "登录墙窗口直接弹在宿主机桌面").
5. 测试: tests/ 新增直通参数注入与探测断言; m09/m12 回归.

## 完成判据

- 本机场景: birth 后容器内 `WAYLAND_DISPLAY` 可达, headed chromium 以 wayland 原生窗口出现在宿主机桌面 (实测证据), fcitx 中文输入可用.
- 直通缺席/失败时行为 = 现状 (noVNC), 全量 display-check 与 m09/m12 回归绿.
- SKILL.md 四节与 DECISIONS.md D051 字面一致.

## 范围外

- waypipe 远程直通 (局域网远程机桌面弹窗) — noVNC 够用前不引入.
- pulse/dbus 接线 — 声音/桌面集成需求出现时单独立项.
