# 状态: 已关闭
# 类型: task
# 阻塞于: MILESTONE-07

## 问题

登录墙闭环 (底层通道已实测, 2026-09-01 vnc-demo, 调研 §5):

- Xvfb (`-ac -noreset`, GEOM 控制分辨率) + x11vnc (`-nopw`) + websockify/noVNC 接入编排
- `DISPLAY=:99 BROWSER_HEADED=true` 切换约定: 登录时用户经 noVNC 人工操作, 登录态落 profile volume, 之后回 headless
- access-web 代码零改动; noVNC `?resize=scale`
- chromium 需 `--shm-size=1g`, fonts-noto-cjk; 端口动态分配
