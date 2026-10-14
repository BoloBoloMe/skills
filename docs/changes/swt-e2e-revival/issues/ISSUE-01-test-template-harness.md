## 父级
- `../EXECUTION.md`
## 执行
- [x] 已实现
## 要构建什么
让"agent 模板"这条链在测试里可以完全本机自足, 并把 M03 冒烟镜像升到契约 2:
1. 模板根可被测试覆盖: `scripts/agent_config/template.py` 的模板根支持一个环境变量 (建议名 `SWT_AGENT_TEMPLATES_DIR`); 未设时行为与现在逐字一致 (仍指向 `workflow/use-sandbox-worktree/agent-templates`).
2. tests/conftest.py 提供夹具 (建议名 `fake_agent_template`): 每个用例建一个临时模板根, 在其中写 `template.json` (含 name/version/kind=openai-gateway/contract=2/base_url 指向本次刚起的假网关/credential 指向本次的临时假 Key 文件) 与假 Key 文件; 起一个本机假网关 (HTTP, 对 `/v1/models` 返回本模板声明的完整模型清单, 其余路径给合理应答), 把 `SWT_AGENT_TEMPLATES_DIR` 指向临时模板根. 夹具退出时全部清理.
3. `image/Containerfile` 补契约: 加 `LABEL run.sandbox-worktree.agent-template-contract="2"` 且容器内 `/etc/swt-agent-template-contract` 内容为 `2` (值以 `scripts/agent_config/common.py` 的 `CONTRACT` 为唯一真相源).
## 覆盖依据
- `../EXECUTION.md` 权威输入节的仓库自定测试原则 ("测试均用临时目录/假 Key/模拟 Podman/本机模拟网关")
- `scripts/agent_config/template.py` (`TEMPLATES`/`load`/`choices`), `scripts/agent_config/runtime.py` (凭据与网关校验是致命错误), `scripts/agent_config/common.py` (`CONTRACT`, 路径常量)
## 相关决策
- `../../swt-container-env-docs/UNAUTHORIZED_DECISIONS.md` UD-015 (本旧账的成因与四层阻塞)
## 允许范围
- `scripts/agent_config/template.py`; `tests/conftest.py`; `image/Containerfile`
## 禁止范围
- `scripts/swt.py` 的任何行为语义; 用户真实 `~/.config/cliproxyapi/`; 真实 8317 网关; 宿主 wayland socket; 既有测试的断言意图
## 代码定位提示
- `template.py`: 顶部 `TEMPLATES = ...` 与 `load(name, root=TEMPLATES)` / `choices(root=TEMPLATES)` 的缺省值
- `runtime.py`: 凭据读取 (`private_json` / `valid_key`) 与网关校验 (`check_gateway`, 走 `template["base_url"] + "/models"`) 的失败都是 `TemplateError` (致命), 所以夹具必须让两者都成立
- `image/Containerfile`: 现为 `FROM docker.io/library/node:24-bookworm-slim`, 已装 git/openssh-server/socat/python3, npm 装 pi CLI
- `tests/conftest.py`: 已有 `free_port`/`Serve` 等重外部资源夹具可参考风格 (注意 `tests/` 下禁止 `from conftest import` 以外的跨树导入约定见 `pytest.ini` 顶部注释)
## TDD 切片
- TS-001:
  接缝: `template.choices` / `template.load` 的公开签名.
  测试用例: 当设置 `SWT_AGENT_TEMPLATES_DIR` 指向含一只合法模板的临时目录时, `choices()` 返回该目录的模板且不含仓库默认目录的模板; 未设该变量时 `choices()` 结果与改动前逐字一致.
  先写的失败测试: 现在没有这个环境变量, 设了也不生效.
  最小绿色实现范围: 模板根缺省值改为"读环境变量, 缺省回落现路径", 其余不动.
  不得测试: 模板加载的其余内部逻辑.
  覆盖: 模板根可覆盖.
- TS-002:
  接缝: 夹具 (`tests/conftest.py` 的假模板 + 假网关).
  测试用例: 当使用该夹具时, 对夹具给出的 `base_url + "/models"` 发 GET 能拿到本模板声明的完整模型清单; 夹具的假 Key 文件存在且内容只含 `client_api_key` 一个字段.
  先写的失败测试: 夹具尚不存在, 测试收集即失败.
  最小绿色实现范围: 夹具实现 + 清理逻辑.
  不得测试: 网关实现的内部结构.
  覆盖: 假 Key + 本机模拟网关.
- TS-003:
  接缝: 真容器 (接缝 2), 一次性冒烟.
  测试用例: 用重建后的 `localhost/swt-m03:latest` 与夹具模板, 走一次 `swt.py birth --agent-template <夹具模板名>` 能到 `born`, 且容器内 `/etc/swt-agent-template-contract` 为 `2`.
  先写的失败测试: 现镜像无契约标记, birth 会在模板安装步报"镜像缺少 agent-template 契约".
  最小绿色实现范围: Containerfile 补契约 + 重建镜像.
  不得测试: 模板安装的内部步骤.
  覆盖: M03 镜像契约 2.
## 验证入口
- `uv run python -m unittest tests.test_agent_templates -v` 全过
- 新夹具的单测全过
- 重建镜像: `podman build -t localhost/swt-m03:latest workflow/use-sandbox-worktree/image/` 后 `podman image inspect localhost/swt-m03:latest --format '{{index .Labels "run.sandbox-worktree.agent-template-contract"}}'` 输出 `2`, `podman run --rm localhost/swt-m03:latest cat /etc/swt-agent-template-contract` 输出 `2`
- 冒烟: 一条真容器 birth 到 `born` 的原始输出 (命令与输出写进回报)
## 风险提示
- 加契约标记会改变 M03 镜像在既有用例里的角色 (原先它是"无契约的旧镜像"). 动手前先 grep 全测试树确认没有用例依赖"m03 无契约"; 有的话停下报告, 不要改那些用例的意图.
- 夹具不要写用户真实家目录/配置目录.
- 模板根的 env 覆盖必须只影响缺省值, 不能改变显式传 `root=` 的调用行为.
## 停止条件
- 发现既有用例依赖 m03 无契约; 或需要改 `swt.py` 语义; 或需要用户真实凭据/网关时, 停下报告
## 适合 AFK 的原因
- 路线与边界由用户裁决锁定 (甲路线), 仓库自定测试原则写明"假 Key + 本机模拟网关", 无待决产品点
## 验收标准
- [ ] 模板根可被测试覆盖且不影响生产缺省; 夹具就位; M03 镜像带契约 2; 冒烟 birth 到 born; 既有模板测试与快层不回归
## 被阻塞于
- 无
