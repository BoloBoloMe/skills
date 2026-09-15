# MILESTONE-08 未经授权决策账本

实施期 (2026-09-15) 总指挥/执行者自主决策, 未经用户逐条批准, 按 M03/M05 先例落账备审.

## UD-01 EXECUTION 为总指挥自拟
- 状态: 当前有效
- 内容: M08 无现成 EXECUTION.md, 沿 M05 UD-01 先例由总指挥依 M06 账本 + M07 N1-N6 自拟, issue 内联 (M03/M05 同款), 未走 to-spec/to-execution 全流程.

## UD-02 直飞轮询超时 = 120s
- 状态: 当前有效
- 内容: D007 留白的超时取 120s (ack 后轮询容器内新 waypipe-server token 的窗口). 依据: 信被取走后设备侧 LLM 轮 (幂等探测 + nohup 拉起) 典型 10-30s, LLM 延迟是主导项且方差大; 太短会假失败落 noVNC (体验倒退), 太长徒增等待. 仅作用于"投信已 ack"之后的等待.

## UD-03 XDG 目录固定常量 /tmp/xdg-1001
- 状态: 当前有效
- 内容: N5 指出 uid=1001, D004 原文 /tmp/xdg-1000 失真. 取固定常量 1001 (镜像 useradd 固定 bolo, uid 稳定), 不做 `id -u` 派生 — SetEnv 行是静态文本无法派生, 两处 (SetEnv 与 entrypoint install -d) 必须同源, 常量是唯一不脱钩写法.

## UD-04 XDG_RUNTIME_DIR 注入走 sshd_config SetEnv, 不用 ~/.ssh/environment
- 状态: 当前有效
- 内容: N3 证明 ~/.ssh/environment 也是可行路径, 但 inject_ssh_key 每次重写该文件 (`cat >` 全量覆盖), 显示栈变量混入会把 D004 改动耦合进 env 重写逻辑; SetEnv 对全部 ssh 会话一致生效且是 D004 既定方案. 维持 D004, N3 路径仅作文档备选记录.

## UD-05 pull-window 成员 = 服务端内置形状校验, 不落静态 whitelist 行
- 状态: 当前有效
- 内容: D008 要求 "服务端对容器注册表校验合法", 即 container 标识须动态绑定投信容器自身 — 静态 canonical 行 (M01 D005 机制) 无法表达该绑定, 且按行注册会漏 "他人容器名" 越权 (A 容器替 B 投信仍命中 B 的行). 故成员落地为: dict 恰含 {tool, container} 两键 + container == 投信 key 的容器名. 裸 tool 无 container / 多余键 / 错名 → 一律降级. admin whitelist 机制保持不动, 供未来无动态绑定的成员使用.

## UD-06 chromium 路径解析 = throwaway podman run, 失败则跳过不阻断
- 状态: 当前有效
- 内容: F006 要求 birth 时解析精确字面路径. 实现: `podman run --rm --entrypoint /bin/sh <image-ref> -c 'ls -d /home/bolo/.cache/ms-playwright/chromium-*/chrome-linux*/chrome | sort -V | tail -1'` (多 rev 并存取最高, 一次性成本约 1s). 解析失败 (空输出/超时) → stderr 告警 + 跳过实例脚本/挂载/交付模板行 (交付打 reason 行, F3), birth 不因此失败 — 该容器仍可终端工作 + noVNC, 仅无直飞.

## UD-07 设备侧执行器分层: 代码管机械判定, LLM 配方管编排
- 状态: 当前有效
- 内容: D007 判定拆分原则在设备侧同款适用. relay 扩展代码管: 限频 (同容器 300s) + waypipe 在场检查 + 缺席期抑制同类信; 取信会话 LLM 按 SKILL.md 配方管: 端点发现 (经既有 ssh/herdr 通道查 host)、幂等探测 (ssh 容器 pgrep -x waypipe, N2 修正后不用 socket 存在判活)、nohup 后台拉起 (waypipe ssh 会话须长存, 不能占 LLM 前台)、herdr notification 回报. 限频 300s 依据: 拉窗是低频动作, 5 分钟窗足以把注入驱动的循环轰炸压成噪声, 又不误伤人手重试.

## UD-08 音频 socket 条件导出
- 状态: 当前有效
- 内容: D002 的 `PULSE_SERVER=unix:/tmp/swt/pulse-b.sock` 改为脚本内条件导出 (`[ -S ] && export`): 宿主直通模式下该 socket 不存在, 硬导出会断 chromium 本地音频. 窗口直飞模式下 socket 由设备侧 -R 建立后才存在, 条件导出两种模式都对.

## UD-09 交付包 -R 远端路径用 /run/user/$(id -u)/pulse/native
- 状态: 当前有效
- 内容: D002/M07 实测写死 /run/user/1000 (设备 uid 1000). 设备 uid 非恒 1000, 模板用 `$(id -u)` 由设备 shell 展开, 严格更优. 容器侧路径 /tmp/swt/pulse-b.sock 不变 (D004 目录保障).

## UD-10 被抑制来信立即 ack, outcome 记 skipped 原因
- 状态: 当前有效
- 内容: waypipe 缺席/限频而未 triggerTurn 的来信立即 ack (outcome=skipped:waypipe-missing / skipped:rate-limited), 不留队列滞留到 7 天滚动删除; 状态经 admin 可查. 若不 ack, 服务端视为未处理, 语义失真 (信实际已被设备侧拒绝执行). D006 "不取下一封同类信" 指不转化为 LLM 轮, 不是不 ack.

## UD-11 preflight 失败退出码 = 86
- 状态: 当前有效
- 内容: D007 要求 "明确退出码退出, 不做选路". 取 86 (避开既有 2=传输失败系), 脚本头注释与 SKILL.md 编排节同值: 容器 AI 见 86 即按三态编排走投信, 不重试脚本.

## UD-13 评审采纳记录 (双轴 code-review, 基准点 d6e3484)
- 状态: 当前有效
- 内容: Spec 轴全符合无缺失; Standards 轴无硬性违规, 5 条判断性发现, 采纳处置: #2 双通道传递 — 核实后两分支均已以 runtime record 为单源 (参数只喂 record 初值), re-entry 忽略参数是正确语义, 无需改码; #4 pulse socket 用例测试隔离 — 采纳, 加在场守卫 skipTest (不扰动真实 host 状态); 其余 (Data Clumps 参数团, 源码文本守卫测试, 跨语言常量重复) 记录不采纳: 前两者是可辩护的既有形态, 后者是协议两端无共享常量的必要重复.

## UD-12 不加 waypipe 残尸清理
- 状态: 当前有效
- 内容: N2 暴露 waypipe 异常死亡留下 waypipe-server-*.sock 尸体并累积. 不加 entrypoint 清理: 残尸对功能无碍 (新会话 token 唯一, D007 轮询按 token 差集不受旧尸干扰; 唯一挡路残渣 pulse-b.sock 已由 StreamLocalBindUnlink yes 治理), D004 原文即 "明确不加, 双机制冗余". 累积速率观察留 M09, 有害再补.
