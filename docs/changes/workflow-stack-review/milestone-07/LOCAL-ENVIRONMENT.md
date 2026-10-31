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

以上是最初依赖探测与请求时的记录, 不是当前安装状态. 当时仓库另有他人的 `RESEARCH-design-visualization.md`, 本轮未修改或代提交.

## 用户收窄范围后取消补装

用户随后明确 Podman 本来不该有, 相关代码没有改到就不用测. 已核对源提交 c77f6af 相对父提交 6717c5e 的 17 项全部为 Markdown/skill 目录删除迁移, Podman/容器运行程序/相关测试/浏览器程序均零改动. 当前七个 SKILL 与 README 等源内容相对 c77f6af 也未变. 因此修订 AC-07-06 为直接相关检查, 不再为无关路径补装 Podman 或运行全套测试. 信箱间歇问题不由本节点调查或修复.

已发送取消信 `74719246e71f46bb8182a7c3c8bafede`, 不再请求补 playwright 或扩大容器运行能力. 但随后实际探测 `/usr/bin/podman` 已出现, `dpkg-query` 为 `podman 4.3.1+ds1-8+deb12u1+b3 install ok installed`; FINAL-CHECKS.log 的 2026-10-31T17:10:13Z 记录也如实为 podman_present=true. 本会话未执行补装命令, 安装动作与范围尚待宿主回报, 不把取消投递成功当成已撤销.

已以 `868ee14def224d5d9db2a22084fadb9e` 请求宿主立即停止进一步配置/权限放宽/产品测试, 回报本任务实际改装与最小安全还原方案; 不做 autoremove, 不删测试数据或既有依赖, 不重建容器. 源文件工作不再被 Podman 测试阻塞, 这里只处理本轮多余依赖请求的撤回收尾.
