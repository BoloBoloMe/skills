# milestone-07 当前容器验证环境

## 用户补充边界

用户明确要求: "不能再容器外的主机上跑. 只能在当前环境中跑. 缺少的依赖要补充. 信箱时好时坏不归你管". 已同步进 `../ACCEPTANCE.md` 的 AC-07 补充确认与 AC-07-06. 后续只在当前容器测试, 不再在宿主运行 pytest, 不把历史宿主结果当作新的完成证据. 信箱间歇失败只单列事实, 不继续调查或修复.

## 实际依赖探测

- 当前帐号 `bolo`, uid=1001, 无 sudo. `command -v podman` 无结果, `command -v apt-get` 为 `/usr/bin/apt-get`, 但本帐号无系统包安装权限. 不伪造 podman 或改测试绕过依赖.
- `uv run python -c` 通过 `importlib.util.find_spec` 检查: 解释器 `/usr/bin/python3`, pytest 位于 `/usr/local/lib/python3.11/dist-packages/pytest`, playwright 为 None.
- `uv run --project general/access-web/browse --no-sync python -c` 同样检查: 仓库播种 `.venv/bin/python` 有 playwright, 无 pytest. 该检查没有同步或安装依赖, 不能把两个解释器各自拥有的包合称为同一可用测试环境.
- 缺项: 真实 podman CLI 及使 bolo 执行 `podman volume ls -q` 可用的容器运行条件; 一个同时拥有 pytest 与仓库声明的 playwright>=1.40 的容器内测试环境.

## 补齐请求

按容器纪律, 缺依赖交出生宿主具体会话 `01a18814-6e80-744f-a09f-346ba7b25522` 处理镜像/播种层, 请求信 `61996e3b8ec246b38d6b67f2511f1a57` 已投递. 请求明确禁止宿主执行产品测试, 禁止改测试/pytest.ini/真实已安装 skills 或全局 agent 配置; 依赖只补当前容器, 若必须删除或重建容器, 先回方案等待批准, 不自行重建. 请对方回容器内 Python 入口/版本与真实 podman 依赖验证结果; 本会话随后在当前容器自行实跑.

截至本记录, 只完成依赖探测与请求, 尚未收到补齐完成证据, 未声称安装或测试成功. 仓库内另有他人未跟踪的 `RESEARCH-design-visualization.md`, 本轮不修改或代提交.
