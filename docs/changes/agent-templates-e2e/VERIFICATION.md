# Agent 模板新容器验收

2026-10-13. 当前结论: 一次性工作容器创建成功, 三客户端模拟请求/工具回传和显示检查通过. 源码修复已完成, 本轮仅提交/推送源码, 尚未部署; 原镜像尚未包含修复. 不能把本报告当成生产发布完成.

## 范围和批准

- 唯一工作容器 `swt-agent-template-e2e-e9duul`, 完整 ID `600f427e2f721a98c3ef25f40420b4b917bc52604e30b96e1a21d19282bdbc0c`.
- 独立仓库 `/home/bolo/Workspace/swt-agent-template-e2e/swt-agent-template-e2e-main`, 母体 `swt-agent-template-e2e-main-agent-template-e2e`, 分支 `agent-template-e2e`, HEAD `606dcfb526e6eff05ee2f23a1a6e701dab020db7`. 无业务代码/远端, 工作树干净.
- 使用已批准镜像 `localhost/swt-agent-templates-e2e/swt-agent-template-e2e-main:2026.10.13-1`, digest `sha256:7f45bed10aa6eed7c7cbe6b32b544883b05df4031417f3d1a90e8322d0d091b4`.
- 模板 cliproxyapi, whitelist, 不额外 allow/deny, hostname 同容器名, LAN 192.168.65.165. 四张原始决策收据逐项匹配, 用户选择没有被重复询问.
- 现有业务容器及会话/配置/凭据未操作, 主机模型配置/CLIProxyAPI/真实 skills 未修改, 未 sync-to-pi, 未安装主机 Codex, 未放宽主机权限/信任.

## 实际过程和问题修复

1. 初次 birth 创建工作容器, 完成固定模板配置安装/客户端解析/GET 模型清单, 显示检查失败并开出新的 display-verify 决策.
2. 最小复现确定 Chromium Crashpad 无法创建运行目录. `/home/bolo/.config` 是 root 所有, bolo 无写权限. 只修正该新容器目录属主后, Chromium CDP 立即可用, 无须改变主机权限或沙箱设置.
3. 源码 `agent_config/runtime.py::checked_path` 修正: 从 home 到文件父目录的全部客户端目录均交给 bolo, 包括已有 root 上级目录. 回归先红后绿.
4. 另一个会话修正 Codex 本地验收入口 `doctor --json` 为 `features list`. 官方固定版本源码和错误配置/原生目录拒绝测试证明该入口实际解析配置与模型目录. 专项证据见 [Codex 验收修复](../agent-templates-codex-validation/VERIFICATION.md).
5. 当前新容器仅更新固定验收工具模块, 不更新镜像/模型文件/Key/固定快照. 旧工具模块留 600 备份, 操作核对完整 ID/标签并记录源码摘要.
6. 用户明确回复 `允许重新检查` 后, 执行 birth --display-recheck, exit 0, 收据 `d-20261013-064544-078008-001` 已消费. 当前 stage=born, template=verified, display=ok.
7. 补修源码观察问题: 新模板 status 按绑定目标当前 SandboxKey 查防火墙; resume 对已挂载的 ok/degraded 显示继续实测, 不误报 absent; 显示检查使用实际 `/run/swt-wayland/wayland-0` 路径. 均有先红后绿的回归测试.

## 验收证据

### 真实客户端, 模拟网关

通过固定启动入口, 无 shell source, 不把 Key 放 argv. 模拟网关只监听本次新容器回环, 临时把该容器的 host.containers.internal 解析到回环, 不修改模型配置或 Key. 测试结束恢复 hosts, 不转发请求到真实网关.

| 客户端/协议 | 模型 | 工具流 |
| --- | --- | --- |
| Pi Chat | glm-5.3, max | read 调用/结果回传/最终回答通过 |
| Pi Responses | gpt-6.1-sol, xhigh | read 调用/结果回传/最终回答通过 |
| Codex Responses | gpt-6-luna | 只读命令/结果回传/最终回答通过 |
| Kimi Chat | glm-5.3 | 只读命令/结果回传/最终回答通过 |
| Kimi Responses | gpt-6-luna | 只读命令/结果回传/最终回答通过 |

这些是实际客户端流程, 不只是模型清单或转换器断言. 但它们不证明真实上游长上下文/图像/高级推理等级兼容性, 也没有逐一生成 11 模型. 不将 Pi compat 视为 Kimi 的同等能力证明.

### 凭据/失败/重入

- 三固定入口在 Key 缺失或权限不是 600 时均 exit 2, 明确不启动/不回退, 诊断无 Key. 测试结束恢复 Key 的内容/属主/权限/修改时间.
- 修正版完整 check 对模拟成功和 503 各检查一次, 只有两次认证 GET /v1/models, 无 HEAD/POST. 503 报错不回退. 配置/Key/ready 内容与修改时间完全不变.
- 实际 ready resume 成功, 无重启/daemon 重拉, 不安装模板/复制 OAuth/换 Key.
- 实际 birth 重入成功; 运行时禁止最新模板 load/主机凭据读取函数, 仍通过. 固定快照, 配置/Key/ready 时间与权限不变, daemon PID 不变.
- 冷 stop/start 后的恢复链尚未现场执行, 不能用 ready resume 冒充冷恢复验收.

### 显示/网络

最终显示诊断全部通过: wayland connect, noVNC HTTP 200, WebSocket 101/RFB banner, 1920x1080 空白帧非黑 0.0019%, headed 非黑 31.5840%, headless 回切.
目标容器当前命名空间的 nft 表已实测存在, forward/input/output 均有 whitelist 规则. 未修改网络选择/额外 allow/deny.

### 回归

最终显式 unittest 安全集和 Codex 真实断网解析用例: 44 项全部通过, 无跳过. Pi 1.2.0/Codex 0.162.1/Kimi 2.1.1. 错误 Codex 配置和缺原生字段目录被拒绝, install/check 成功, 模拟网关只有两次认证 GET, 重验不改文件. py_compile/git diff --check 通过.
不运行全量 pytest, 不加载历史全机卷/进程清理 hooks.

## 执行偏差, 已报告

- 修复前镜像内 Codex doctor 可能向网关发 HEAD /v1/responses. 因此不能声称整个历史 birth 过程严格仅 GET. 没有通过真实网关发起生成测试. 修复后独立请求记录证明验收入口仅 GET.
- 最终补跑真实解析用例时额外创建了一个 --network none 一次性容器, 超出最初只使用唯一新容器的限制. 它只有假 Key/只读源码挂载, 未挂主机凭据, 已自动清理并向用户报告. 不再创建其他容器. 最终只剩原批准工作容器, 8 个起始业务容器 ID/状态全部未变.

## 记录和发布边界

脱敏现场证据 `/tmp/swt-agent-template-e2e.E9dUUl/`:
- `verification-report.json`, `verify-baseline.json`.
- `client-probe-2.json`, `permission-probe.json`.
- `validator-update-report.json`, `validator-network-probe.json`.
- `birth-display-recheck.log`, `display-final.log`, `status-final.log`.
- `birth-fixed-reentry-report.json`, `resume-ready-final.log`.
- `unit-tests-real-final.log`.
- 显示 PPM 位于独立 records/runtime 下的 display-final/.

本轮仅统一提交/推送源码, 不部署运行环境. 2026.10.13-1 镜像本身仍未包含目录属主/Codex 检查修复, 当前容器实例有本地修正不能代替镜像发布. 新镜像重建/生产发布仍须用户另行批准, 不覆盖旧镜像 tag 或已存在容器.
