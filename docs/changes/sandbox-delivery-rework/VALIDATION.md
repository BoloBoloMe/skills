# 沙盒交付与会话回信调整验证

## 结果

- 沙盒生命周期/交付/提示词/模板/同步: 341 passed, 31 subtests passed, 103 个容器类 e2e 用例未跑.
- mailbox 全部 20 个测试文件: 137 passed. 包含真实回环服务上的多会话定向投信/取信隔离, 幂等注册不丢待取信, 凭据权限, 服务换址, 监听恢复/取消/并发/会话切换, 容器原有凭据保留.
- `tests/pi/*.test.mjs`: 79 项通过. 全屏详情页含分区, 长命令, 小终端/动态缩放, 中文/emoji/组合字符/ANSI 的官方显示宽度验证.
- `mailbox_listen` 工具 schema 经 pi 自带 `typebox/compile` 校验, 不调用模型或真实信箱.
- `tests/run` 的 mailbox 脚本/扩展/场景夹具与 Herdr helper 4 个改动面映射验证通过.
- `git diff --check` 通过.

Herdr 测试使用隔离 HOME/XDG_STATE_HOME, 验证真实 OpenSSH 对专用 Include/私钥路径的解析, 真实 Herdr 的 list/remove 命令兼容性, 添加/清理的幂等重试与资源归属. add/远端 SSH 使用边界替身, 未执行真实容器 birth/resume/terminate 全链或升级远端 server.

校正了 3 处原版也失败的旧测试预期: 交付调用点已有固定模板重入分支, 实际是 6 处而非 5 处; 名称保护已改为固定模板创建绑定, 不再有 `name_explicit`. 没有为迎合旧测试改回旧生产逻辑.

## 重现命令

在仓库根运行:

```bash
export PYTEST_XDIST_WORKER=isolated
export MAILBOX_FLEET_KEY=/tmp/mailbox-delivery-absent-fleet.key

uv run python -m pytest -m 'not e2e' -q \
  tests/test_swt*.py tests/test_env_docs.py \
  tests/test_agent_templates.py tests/test_agent_templates_fixture.py \
  tests/test_agent_templates_safety.py tests/test_sync_to_pi*.py

uv run python -m pytest -m 'not e2e' -q tests/test_mailbox*.py

for f in tests/pi/*.test.mjs; do node "$f" || exit; done
unset PYTEST_XDIST_WORKER MAILBOX_FLEET_KEY
```

`MAILBOX_FLEET_KEY` 指向不存在的测试路径, 避免测试引导真实舰队密钥/发现邻居. 单进程设置 `PYTEST_XDIST_WORKER=isolated` 只为跳过旧 conftest 的全机新增卷/孤儿进程清理钩子, 未启用并行测试; 仍保留 e2e 分类和服务夹具.

## 生效边界

本次只修改仓库, 未同步真实 skills, 未重启真实 pi/mailbox, 未改现有容器或真实 Herdr machine 配置.

部署时需同版同步两个 skill 与扩展, 重载 pi, 重启 mailbox serve 才有新增的 admin ensure 接口. 信件队列在内存中, 重启前先处理待取信. 新建容器才生成 host 回信 sessionId; 旧提示词快照不自动改写. Herdr 登记失败保留容器和记录并报 PARTIAL, 不冒充完整交付.
