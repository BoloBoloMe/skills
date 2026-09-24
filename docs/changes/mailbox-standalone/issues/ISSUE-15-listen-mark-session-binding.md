## 父级
- `../EXECUTION.md`, `../DECISIONS.md` D021 (细化 D008)

## 执行
- [ ] 已实现

## 要构建什么
取信守护标记绑定会话身份: listen.json 增记启动者 pi 会话身份; session_start 仅在当前会话身份与标记一致 (同一会话续接/重启) 且守护进程已死时自动恢复守护; 新会话启动永不自动监听、不覆盖不清除他人标记; /mail-listen start 遇他活会话标记仍软提示后接管 (D008 软提示保留); stop 仅清自己拥有的标记; 陈旧标记 (进程已死) 可被 start 接管. 实地验收发现的缺陷: 现 "见标记即恢复" 导致任何新 pi 会话都自动监听.

## 覆盖依据
- DECISIONS.md D021 (用户 2026-09-24 验收裁决); AC-003/AC-004 语义在此细化下重新成立

## 允许范围
- `workflow/mailbox/pi-extension/index.ts`
- `tests/test_mailbox_audit.py` (BR-007 扫描若需同步注记)

## 禁止范围
- mailbox.py (脚本零改动)
- D008 软提示哲学 (不设强制唯一性)
- 手动前台取信形态

## 代码定位提示
- pi-extension/index.ts: session_start 恢复段, listen.json 读写, /mail-listen start/stop, 守护子进程管理
- pi 会话身份 API: 以 pi 官方文档与类型定义为准 (pi-coding-agent 包 docs/extensions.md 与 dist 类型), 找跨进程重启稳定的会话标识 (如会话文件 id); 找不到就停止上报, 禁止用 cwd 等近似物

## TDD 切片
- TS-001:
  接缝: index.ts 可执行化验收 (沿 ISSUE-07 的 jiti 临时脚本 + 假取信脚本模式).
  先写的失败测试或断言: 模拟 mark.session_id != 当前会话 的 session_start → 不启动守护且标记不被改写; mark.session_id == 当前会话 且进程死 → 恢复. 现状对第一分支失败.
  最小绿色实现范围: 标记结构 + session_start 判定 + start/stop 所有权语义.

## 验证入口
沿用 ISSUE-07 的 node/jiti 冒烟方式人工验证守卫生命周期; 仓库侧 /home/bolo/Workspace/skills/.venv/bin/python -m pytest tests/ -k "audit" -q -m "not e2e" 全绿 (BR-007 扫描不回退).

## 风险提示
 listen.json 结构变更需向后兼容旧文件 (无 session_id 字段时视为陈旧标记, 不自动恢复, start 可接管); 守护子进程生命周期逻辑不要重构, 只动所有权判定.

## 停止条件
pi API 找不到稳定会话身份, 或需要改 mailbox.py/D008 哲学: 停止上报.

## 验收标准
- [ ] 新开 pi 会话不自动监听
- [ ] 同会话续接自动恢复
- [ ] start/stop 所有权语义按 D021
- [ ] BR-007 扫描与既有测试全绿
