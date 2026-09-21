# 窗口直飞协议 (三态选路)

容器内 AI 开 headed 浏览器遇到 `swt-headed-browser.sh` 退出码 86 (本机直通缺席), 或设备侧取信会话收到 `swt.pull-window` 信时读本文件. 三态 = 宿主直通 wayland / 设备侧 waypipe 直飞 / noVNC 兜底 (D007 判定拆分: 机械判定在代码, 编排在本文件).

执行入口 = 容器固定路径 `/home/bolo/.local/bin/swt-headed-browser.sh` (母本 `headed-browser/swt-headed-browser.sh` 经 birth 换入 chromium 精确路径后只读挂载, UD-06): 内部先 preflight — `WAYLAND_DISPLAY` 与 `XDG_RUNTIME_DIR` 在场且 `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY` 可连才启动 chromium; 不满足 **exit 86**, 容器 AI 见 86 即投信, 不重试脚本 (UD-11). 脚本内部条件导出 `PULSE_SERVER=unix:/tmp/swt/pulse-b.sock` (socket 在场才导, 宿主直通模式硬导会断本地音频, UD-08) 后 `exec chromium --no-sandbox --ozone-platform=wayland`; env 由脚本内部设置, 命令行禁止 `VAR=...` 赋值前缀 (N1: waypipe 把前缀当程序名, Spawn failure).

## 容器侧编排

preflight 退出 86 后:
1. **投信前记基线**: `ls /tmp/waypipe-server-*.sock 2>/dev/null` 记现有 token 集 — 异常死亡的会话会留 socket 尸体 (N2), 判活只看新 token 差集.
2. **投信**: exec 类型信, `--to` 显式填当前设备 (定设备纪律见 reference/mailbox.md 展示页网址沟通节), body 为 JSON: `{"tool": "swt.pull-window", "container": "<本容器名>"}`; 发送命令见 reference/mailbox.md 容器侧怎么投信. 服务端形状校验 + container 动态绑定投信 session 自身 (UD-05), 命中直批不问人 (指令能力极窄且无参数注入面, D008).
3. **等 ack 后轮询**: ack 只证明信被设备取走, 不证明窗口拉起 — 轮询容器内 `/tmp/waypipe-server-*.sock` 出现基线之外的新 token (F005), 超时 **120s** (UD-02). 新 token 出现 = 会话已建立并拉起 chromium; 页面 URL 已随设备侧拉窗命令附带, 不做事后导航 (M09 实测: 事后导航不可靠, 且容器内禁用局域网映射地址 — hairpin 拒连, 只用容器内 `127.0.0.1:<web端口>`); token 证明会话建立, 不证明用户可见, 可见性靠拉窗命令的软件渲染参数保障.
4. **超时落兜底**: 120s 未出新 token → 落 noVNC (`DISPLAY=:99`), 并在回复中明确告知用户落了兜底.

## 设备侧拉起

取信会话收到 swt.pull-window 信; 取信脚本内置机械门禁 (UD-07 分层: 代码管机械判定, 本配方管编排): waypipe 缺席 → 本机提示安装 + 立即 ack `skipped:waypipe-missing`; 同容器 300s 窗内重复 → ack `skipped:rate-limited`; 两种都不转化为 LLM 轮 (UD-10):
1. **前提**: 设备 Linux Wayland 桌面会话 + waypipe 客户端; Atomic 系发行版 (Bazzite 等) 经 distrobox 安装 (D006).
2. **密钥**: 设备→容器 ssh 免密经 host 上 `uv run python scripts/swt.py enroll-device-key <容器名>` 一次性发放 (N4: 密码登录无法自动化代执行).
3. **幂等探测**: `ssh <容器> pgrep -x waypipe` — 已有活跃会话直接回报不再拉起 (D008 幂等; N2 修正: 不用 socket 存在判活, 尸体会残留).
4. **后台拉起** (即交付包远程直飞命令模板, 变量照交付包实际值代换, 页面 URL 由前置编排一并写入): `nohup waypipe ssh -p <宿主端口> -R /tmp/swt/pulse-b.sock:/run/user/$(id -u)/pulse/native bolo@<host-LAN-IP> /home/bolo/.local/bin/swt-headed-browser.sh --disable-gpu --disable-gpu-compositing --no-first-run --no-default-browser-check --start-maximized http://127.0.0.1:<容器内web端口>/<页面路径> >/dev/null 2>&1 &` — `-R` 同一条会话建音频 socket (D002; 远端路径由设备 shell 展开实际 uid, 不写死 1000, UD-09); 软件渲染参数必带 (M09 实测: GPU 路径经 minimal C 版 waypipe 只出隐形窗口 — 任务栏有图标无画面); waypipe 会话须长存, 不能占 LLM 前台, 故 nohup 后台.
5. **回报**: 拉起后经 herdr notification 通知设备用户窗口已送达.

## 残尸纪律

容器侧不做 waypipe 残尸清理 (UD-12), 旧 token 不挡差集判定; `pulse-b.sock` 残渣由 base 层 sshd `StreamLocalBindUnlink yes` 治理. ssh 会话的 `XDG_RUNTIME_DIR=/tmp/xdg-1001` 由 base 镜像 sshd_config SetEnv 烘配 (UD-03, 固定常量 uid), waypipe server 才有落 display socket 的位置.
