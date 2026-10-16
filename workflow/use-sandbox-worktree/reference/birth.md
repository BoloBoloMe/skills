# 创建与补完 birth

首次新建或初始化未完成时读本文件. 按顺序完成以下准备; 遇待批准或前置不足就停在当前步, 不把等待当完成. 重入复用仍适用的准备结果, 固定选择以本次创建记录为准, 不另建容器.

1. **核实母体与宿主前置.** 调用 `use-worktree` skill, 按其布局/分支/授权检查确定主仓, 来源分支, 目标分支与母体路径. 母体存在则复用, 缺席时 birth 可按 `--base`/默认来源创建, 但不能绕过该 skill 猜布局. birth 写资源前要有支持 `machine list/add/remove` 的宿主 Herdr, 其余工具与 Git 特性由脚本检查. host skill 库全树须让容器用户可读 (rootless uid 映射下靠 other 位), 带依赖的 skill 须有已部署的 `uv.lock`; 缺口先报告, 不自行放宽主机权限.
   完成标准: 主仓, 目标分支和母体路径已核实, 母体工作区干净, 宿主前置满足.
2. **与我确认网络.** birth 选择 whitelist/blacklist, 运行期不切换. whitelist 默认拒绝其他出站, 自动放行网关全端口, 实际 DNS 解析器的 udp/tcp 53 和已建立连接返程; `--allow-entry <CIDR> "理由"` 补本次所需 IPv4/IP 网段. blacklist 默认放行, `--deny <CIDR>` 阻断指定地址. 防火墙只认 IP, 放行地址即其全部端口; 从实际任务盘点站点并解析, 不按域名猜放行范围. Git 走 Unix socket 桥, 不占网络白名单. 选择前读 [risks.md](risks.md), 向我说明网关/DNS 自动项的访问面.
   完成标准: 我已确认模式与条目, 白名单新增均是具体 IPv4/IP 网段并附用途理由; 不用裸 `--allow`, 不编造历史理由.
3. **准备镜像并选择模板.** birth 自动匹配 `<records-root>/<项目slug>/requirements.md`, 或 `--requirements` 指定清单. 清单缺失时从项目 AGENTS.md/README/依赖声明推导, 展示给我并说明构建会运行安装脚本, 获确认后才落盘. 匹配为 REUSE 可继续; BUILD-NEW 时先转述 DECIDE, 我批准后单独运行 `image-prep build`, 再带 `--image <ref>` 重跑 birth. 写清单/构建前读 [image-prep.md](image-prep.md); base/display 只在我明确要求时重建, 缺失/过期也不例外. 选择模板与处理初始化失败前必读 [agent-templates.md](agent-templates.md), 按其选择/凭据/固定快照规则处理.
   完成标准: 清单已确认且有兼容镜像, 模板已由我选择; 待批准构建不算本步完成.
4. **执行创建.** 用已确认的分支和参数调用 birth, 其余选项查 `birth --help`:

   ```text
   uv run python scripts/swt.py birth --repo <主仓> --branch <母体分支名原文>
   ```

   按 DECIDE 收齐网络/模板/主机名/局域网地址/镜像等选择, 答复后重跑同一命令. `--name` 只改名称, 不改变母体配额. 显示验收失败按 DECIDE 让我的选择决定继续终端/重验/终结. Herdr 登记失败保留资源, 按 PARTIAL 修复后重跑, 不另建或自动批准替换不兼容远端 server.
   完成标准: STATE `stage=born`, 容器与母体分支一致, 模板初始化已验收, Herdr machine 已登记; 返回主流程执行交付.
