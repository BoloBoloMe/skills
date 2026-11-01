## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已完成

## 要核验什么
汇总本轮的完成证据, 并如实划出未验证范围:

- present 相关测试与修改过的 SKILL.md 格式检查: 每条检查留命令, 工具版本, 退出码与末行结果, 全过才记该项通过; 有一条失败就如实写失败命令与结果, 该项结论不是通过.
- 宿主环境真实局域网访问: 宿主侧按 SKILL.md 交付 URL 后, 由用户在同一网段另一台设备真实打开, 留下用户确认加能与本次请求对上的 `server.log` 请求行 (时间, 路径, 来源地址), 证据标明来自宿主环境.
- 容器环境真实局域网访问: 容器内 `start` 8800 后按 `SWT_HOST_LAN_IP` 加 8800 的宿主映射端口交付, 由用户设备真实打开, 留下同类证据, 标明来自容器环境; 缺映射端口或没有可用的容器环境时记未验证并列出未验证范围.
- 仓库边界 (BR-014 审计): 只改仓库内文件, 未运行会改安装目录的同步, 未改真实已安装 skills, 不声称安装效果或模型行为已验证.
- 隔离 (BR-015 审计复核): 测试与验证用独立运行时目录与端口, 未停止或接管真实展示实例.

对应 AC-007; BR-014 (审计), BR-015 (审计), BR-016 (审计); 非功能要求 两个环境的真实访问证据.

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-15/PRODUCT.md`, AC-007; BR-014, BR-015, BR-016.
- Technical: `docs/changes/workflow-stack-review/milestone-15/TECHNICAL.md`, 非功能要求 (两个环境的真实访问证据, 页面自检), 接缝与依赖 (用户设备访问 属真正外部, 无法替身).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D012, D007, D010, F015.

## 代码定位提示
- 检查入口: `general/present/tests` (测试), `general/writing-for-llm/check_skill.py` (格式检查), `general/present/SKILL.md` (被检查文档).
- 地址与端口来源: 容器已确认宿主局域网地址 `192.168.65.165` 与环境变量 `SWT_HOST_LAN_IP`; 容器 8800 的宿主映射端口只来自 `SWT_HOST_WEB_PORT`; 宿主已确认地址来自 `~/.agents/sandbox-worktree/lan-address`. 本会话 `SWT_HOST_LAN_IP` 与 `SWT_HOST_WEB_PORT` 都不在环境里, 出生信息见 `~/docs/web-ports.md`.
- 访问证据来源: 运行时目录下的 `server.log` (`<系统临时目录>/pi-present-web-<uid>/server.log`); 不要在证据里贴出真实内网敏感路径或密钥.

## 验证入口
- `uv run python -m pytest general/present/tests`; 记退出码与末行, 以及 `uv run python -m pytest --version` 与 `uv run python --version`.
- `uv run python general/writing-for-llm/check_skill.py general/present/SKILL.md`; 记输出与退出码.
- 宿主证据: 在宿主侧按 SKILL.md 起服务, 交付 `http://192.168.65.165:<实际端口>/<页面>`, 请用户在同一网段另一台设备打开; 通过标准 用户确认看到页面内容, 且 `server.log` 里有与该次打开对得上的请求行 (时间, 路径, 来源地址); 证据注明 `宿主`.
- 容器证据: 先自查 (`env | grep SWT_HOST`, 容器识别, 8800 监听与记录), 仍缺映射端口时按 BR-003 经信箱向宿主会话 `01a18814-6e80-744f-a09f-346ba7b25522` 索取; 拿到后交付 `http://192.168.65.165:<映射端口>/<页面>` 并请用户设备打开; 通过标准 同上, 证据注明 `容器`; 映射或转发改写来源地址时, 用能对上本次展示请求的等价证据并写明口径.
- 两条证据不能互相代替: 只用容器本机 curl 或源码推断不得记通过; 缺哪个环境就在结论里写未验证并列出未验证范围.
- 仓库边界: `git status --short` 与 `git diff --stat` 只落 `../EXECUTION.md` 全局允许范围; 检查全程无 `sync-to-pi.py` 调用; `ls ~/.agents/skills/present` 与改前一致 (或如实记录其状态); 证据里不写安装效果或模型行为结论.
- 隔离复核: 验证前后 `pgrep -af "scripts/web_server.py"` 的 pid 集合与真实实例记录 mtime 对比不变; `workflow/navigate/` 无改动.

## 完成证据
执行后填写: 每条检查的命令, 版本, 退出码, 末行或摘要; 宿主与容器两条真实访问证据 (URL, 访问时间, 用户确认, 对得上的日志行, 环境标注) 或未验证声明; `git status --short` 与 `git diff --stat` 输出; 隔离复核结果; 材料位置 `/tmp/m15-05/`.

## 风险提示
- 本会话缺 `SWT_HOST_WEB_PORT`, 容器证据可能拿不到; 只能记未验证, 不得用容器 8800 或猜测端口拼 URL 充当容器证据.
- 宿主场景需要先判断当前会话是否就是宿主; 若本会话只在容器内运行, 宿主场景由宿主会话执行, 本 issue 记"由宿主会话提供/待提供", 不自行改写成通过.
- 只有本机 curl 成功不构成 BR-016 要求的证据; 用户设备打开是对齐本次请求的关键, 没有它就写未验证.
- 映射或转发若改写来源地址, 日志里的来源可能不是用户设备真实 IP; 用路径与时间对上, 并写明口径, 不夸大成"已确认来源".

## 停止条件
需要改变任一 Spec, 决策或核验范围时停止; 需要挪动证据口径 (例如用非用户设备证据替代) 时先上报, 不自行放宽.

## 适合 AFK 的原因
不适合 AFK: 需要用户在同一网段另一台设备真实打开页面并确认, 还需要宿主会话提供容器 8800 的映射端口. 测试与格式检查部分可自行完成.

## 验收标准
- [ ] present 相关测试与 `check_skill.py` 的命令, 版本, 退出码与结果逐条列出, 且全部通过.
- [ ] 宿主环境有一条用户设备真实访问证据, 能与 `server.log` 里的请求行对上, 并标明来自宿主.
- [ ] 容器环境有一条同类真实访问证据并标明来自容器, 或明确记为未验证并列出范围.
- [ ] 结论里不用一种环境的证据代替另一种, 不用本机 curl 或源码推断顶替.
- [ ] `git status --short` 只落允许范围, 无同步调用, 未改真实已安装 skills, 无安装效果或模型行为声明.
- [ ] 验证前后真实展示实例未被停止或接管, `workflow/navigate/` 无改动.

## 被阻塞于
- ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04.
