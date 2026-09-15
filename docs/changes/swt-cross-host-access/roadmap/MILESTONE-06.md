# 状态: 已关闭
# 类型: deliberate
# 阻塞于: 无

## 问题

窗口直飞 (waypipe 远程直通) 固化盘问. 已实测可行; 触发链路定型为 (b) 经信箱通知设备侧拉起为主, (a) 手工命令为底层零件.

待盘点 (依据 [recon/03](../recon/03-waypipe.md)):

- 触发链路: (b) 主形 + (c3) 设备侧常驻隧道 + 容器内按需起 server 是否加 (唯一 "容器内 LLM 直接发起且零白名单改动" 的形态, 代价设备侧常驻运维)
- headed 选路两态改三态的容器内判定语义 (文件/socket 事实, 不靠 env)
- 音频形态终选: ssh -R unix socket 反带 (文献可行, M07 实测) vs 已实测的 TCP 直连
- 启动脚本模板母本制: 模板位置 / birth 生成形态 (挂载 vs exec 写入) / 参数注入
- base 层改动清单与 D017 级联成本摆台: sshd SetEnv 单行 (XDG_RUNTIME_DIR) + /tmp/xdg-1000 目录保障 + StreamLocalBindUnlink yes (是否接受)
- STATE 选项 (不动 / 探测快照 / 出生声明)
- B 端前提 (Linux Wayland + waypipe, Atomic 走 distrobox) 写进文档与交付提示的口径
