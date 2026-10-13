# Codex 模板验收入口修复与验证

日期: 2026-10-13. 范围: `agent_config/runtime.py` 的 Codex 本地验收, 专项测试和实现说明. 本轮仅提交/推送源码, 不更新运行环境; 未重建/发布镜像, 未修改现存业务容器或真实 agent 配置.

## 原因与修复

原实现调用 `codex doctor --json`. 固定版本 0.162.1 的 doctor 不只是解析配置, 还检查更新/网络/沙盒, 包括 `HEAD /v1/responses`, 与模板的网关仅 `GET /v1/models` 约定不一致.

改用 `codex features list`. 核对官方对应版本源码确认, 此入口加载配置; 核心配置加载器同时解析 `model_catalog_json` 中的原生目录. 不启动模型会话, 不调用 doctor 的额外探针. 客户端 Key 的文件权限/环境注入和网关认证仍分别检查, 不把本地解析称为真实生成或工具流验收.

官方源码:
- https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/cli/src/main.rs
- https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/cli/src/doctor.rs
- https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/core/src/config/mod.rs

## 失败回归

新增 `tests/test_agent_templates_codex_validation.py`. 修复前运行本地专项测试, 确实失败:

```text
expected: /opt/swt-agent-bin/codex features list
actual:   /opt/swt-agent-bin/codex doctor --json
Ran 2 tests, FAILED (failures=1)
```

修复后该回归通过, 并覆盖解析失败不能被忽略, 子进程诊断中的假 Key 不得外泄.

## 真实断网容器

使用已存在且已批准的本地镜像 `localhost/swt-agent-templates-e2e/base:2026.10.13-1`, contract 2. 不拉取/构建镜像. 每次测试只新建唯一命名的一次性容器, `--network none`, 无主机配置/凭据挂载, 只读挂载本仓库初始化源码. 假 Key 和快照仅经 stdin 输入, 模拟网关仅监听容器内回环.

实测客户端: Pi 1.2.0, Codex 0.162.1, Kimi Code 2.1.1.

通过项:
- 真实容器内 `install` 和随后 `check` 返回固定成功报告.
- 三个客户端的本地解析入口执行成功.
- Codex 拒绝类型错误的配置, 也拒绝缺必填字段的原生目录.
- 重复检查前后配置/凭据/ready 文件的内容和修改时间完全一致.
- 模拟网关只收到两次带正确认证的 `GET /v1/models`, 无 HEAD/POST.
- 本次验收容器无残留. 不操作另一会话正在验收的容器.

完整模板安全回归加真实容器用例:

```bash
SWT_AGENT_PARSER_IMAGE=localhost/swt-agent-templates-e2e/base:2026.10.13-1 uv run --no-project python -m unittest discover -s tests -p 'test_agent_templates*.py' -v
```

结果: `Ran 41 tests`, `OK`, 无跳过. `git diff --check` 通过.

## 证据边界

此用例验证容器内初始化和客户端解析, 创建绑定输入是测试夹具. 不替代 host 完整 ID/标签绑定测试, 完整 birth/resume/显示栈验收, 或真实客户端生成/工具调用测试.
只读覆盖新源码的通过结果不等于旧镜像已包含修复. 镜像内工具更新仍须另行审批重建. 并行验收会话的目录属主修复被完整保留; 本记录不把其他会话的验收结果算成本次亲测结果.
