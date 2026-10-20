# 窗口直飞协议 (三态选路)

容器内 AI 开 headed 浏览器遇到 `swt-headed-browser.sh` 退出码 86 (本机直通缺席), 或设备侧取信会话收到 `swt.pull-window` 信时读本文件. 三态 = 宿主直通 wayland / 设备侧 waypipe 直飞 / noVNC 兜底 (机械判定在代码, 编排在本文件).

执行入口 = 容器固定路径 `/home/bolo/.local/bin/swt-headed-browser.sh` (母本 `headed-browser/swt-headed-browser.sh` 经 birth 换入 chromium 精确路径后只读挂载): 内部先 preflight — `WAYLAND_DISPLAY` 与 `XDG_RUNTIME_DIR` 在场且 `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY` 可连才启动 chromium; 不满足 **exit 86**, 容器 AI 见 86 即投信, 不重试脚本. 脚本内部条件导出 `PULSE_SERVER=unix:/tmp/swt/pulse-b.sock` (socket 在场才导, 宿主直通模式硬导会断本地音频) 后 `exec chromium --no-sandbox --ozone-platform=wayland`; env 由脚本内部设置, 命令行禁止 `VAR=...` 赋值前缀 (waypipe 把前缀当程序名, Spawn failure).

## 容器侧编排

preflight 退出 86 后:
1. **投信前记基线**: `ls /tmp/waypipe-server-*.sock 2>/dev/null` 记现有 token 集 — 异常死亡的会话会留 socket 尸体, 判活只看新 token 差集.
2. **投信**: 调用 `mailbox` skill, 按其 `reference/web.md` 确定当前设备并遵守主文件投信流程. exec 类型信, `--to` 显式填该设备, body 为 JSON: `{"tool": "swt.pull-window", "container": "<本容器名>"}`. 服务端形状校验 + container 动态绑定投信 session 自身, 命中直批不问人 (指令能力极窄且无参数注入面).
3. **等 ack 后轮询**: ack 只证明信被设备取走, 不证明窗口拉起 — 轮询容器内 `/tmp/waypipe-server-*.sock` 出现基线之外的新 token, 超时 **120s**. 新 token 出现 = 会话已建立并拉起 chromium; 页面 URL 已随设备侧拉窗命令附带, 不做事后导航 (实测事后导航不可靠, 且容器内禁用局域网映射地址 — hairpin 拒连, 只用容器内 `127.0.0.1:<web端口>`); token 证明会话建立, 不证明用户可见, 可见性靠拉窗命令的软件渲染参数保障.
4. **超时落兜底**: 120s 未出新 token → 落 noVNC (`DISPLAY=:99`), 并在回复中明确告知用户落了兜底.

## 设备侧拉起

取信会话收到 swt.pull-window 信; 取信脚本内置机械门禁 (代码管机械判定, 本配方管编排): waypipe 缺席 → 本机提示安装 + 立即 ack `skipped:waypipe-missing`; 同容器 300s 窗内重复 → ack `skipped:rate-limited`; 两种都不转化为 LLM 轮:
1. **前提**: 设备 Linux Wayland 桌面会话 + waypipe 客户端; Atomic 系发行版 (Bazzite 等) 经 distrobox 安装.
2. **密钥**: 设备→容器 ssh 免密经 host 上 `uv run python scripts/swt.py enroll-device-key <容器名>` 一次性发放 (密码登录无法自动化代执行).
3. **幂等探测**: `ssh <容器> pgrep -x waypipe` — 已有活跃会话直接回报不再拉起 (幂等; 不用 socket 存在判活, 尸体会残留).
4. **后台拉起** (即交付包远程直飞命令模板, 变量照 STATE 与交付包实际值代换, 页面 URL 由前置编排一并写入): 调用 `mailbox` skill 并读其 `reference/pull-window.md`, 以其中的命令模板, 参数纪律及已验证的 waypipe 版本组合为准. 部署后的副本均位于 `~/.agents/skills/` 下各自的 skill 目录.
5. **回报**: 拉起后经 herdr notification 通知设备用户窗口已送达.

## 残尸纪律

容器侧不做 waypipe 残尸清理, 旧 token 不挡差集判定; `pulse-b.sock` 残渣由 base 层 sshd `StreamLocalBindUnlink yes` 治理. ssh 会话的 `XDG_RUNTIME_DIR=/tmp/xdg-1001` 由 base 镜像 sshd_config SetEnv 烘配 (固定常量 uid), waypipe server 才有落 display socket 的位置.
