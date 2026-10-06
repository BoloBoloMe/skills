# 远程展示

仅在 `SKILL.md` 判定为远程模式时读取. 将页面生成到 `SKILL.md` 选定的 `output_dir`, 页面含 Mermaid 时先按 `SKILL.md` 运行 `<embed>` 内联渲染库, 再用 web 服务交付, 不启动 Chromium 或安装本地浏览器环境. 页面仍须提供 `__PRESENTATION_STATE__`, 但远程没有读取通道, 反馈和最终确认都在 chat 完成.

## 挂载与交付

从 `SKILL.md` 所在目录解析 `scripts/web_server.py` 的绝对路径, 记为 `<web-server>`. 通过以下命令挂载页面所在目录:

```bash
uv run python <web-server> start <port> <页面所在目录绝对路径> --bind <addr>
```

成败以 stdout 单行 JSON 的 `success` 字段为准.

- 在 `49152-65534` 内随机选端口; 返回 `port_in_use` 时换端口重试, 最多 10 次.
- SSH 场景默认 `--bind 0.0.0.0`, 以便用户直接访问. 服务没有认证和 TLS, 开放期间同网段主体可读取已挂载目录; 使用前向我说明这一风险一次. 若我要求仅本机访问, 用 `--bind 127.0.0.1`, 并原样转述成功输出中的 `ssh -L` 端口转发指引.
- 同一用户的存活实例在 bind 一致时幂等复用, 新目录自动挂载, 端口差异只告警. bind 不一致会返回 `bind_conflict`; 告诉我先 `stop` 再重新启动, 不要静默复用.
- 成功时在 chat 给出可点击 URL, 原样转述 JSON 中的 `url`/`hostname`/`lan_ip` 和 `port`, 并用一句话说明展示内容和待反馈问题.
- 重试与备选 bind 均失败后, 给出 HTML 本地绝对路径链接和内容摘要, 然后继续原工作流.

完成标准: 已交付宿主机可访问的 URL, 或已给出本地路径和摘要并继续原工作流.

## 容器分支

远程模式下若 `/run/.containerenv` 存在, 使用容器创建时映射的 8800 端口, 并锁定端口:

```bash
uv run python <web-server> start 8800 <页面所在目录绝对路径> --bind 0.0.0.0 --fixed-port
```

容器端口映射要求监听 `0.0.0.0`; 映射端口固定, 换端口会令 host 无法访问. 若 8800 被占用, 报错退出, 不换端口. JSON 中的 `url`/`hostname`/`lan_ip` 是容器视角, 不要直接交付或猜测 host 地址; 在 chat 报告容器端口和挂载根目录, 由 host 侧会话运行 `podman port <容器> 8800` 后组装 URL.

同一容器中的多页复用锁定实例, 后续用 `add-dir <dir>` 挂载, 不另起服务. 若已运行的实例未锁端口, 再次启动时带 `--fixed-port` 不会补锁; 按输出 warning 告知我, `stop` 后按上方命令重启. 容器终结时服务和状态一并消失, 无需先 `stop`.

## 服务生命周期

- `status` 探活; 服务已停止时按原挂载清单重建, 以输出中的 `port`/`rebuilt` 更新 URL. 普通实例可能换端口; 锁定实例沿用原端口, 若端口被占则报错, 释放端口后重试.
- `add-dir <dir>` 增挂目录, 同目录幂等; `stop` 终止服务并删除运行时文件.
- 服务空闲 24 小时后自退; 运行时文件在系统临时目录, 系统重启后归零.
