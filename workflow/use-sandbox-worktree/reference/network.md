# 网络维护与事务恢复

查询规则, 增删运行中白名单/补理由, 或发现 `network-change` 时先读本文件. 普通维护用 `swt.py network`, 保留未涉及条目/自动项/其他容器; 底层规则命令只用于另行授权的 [手工救场](ops.md).

```text
uv run python scripts/swt.py network show --repo <主仓> --name <容器名>
uv run python scripts/swt.py network update --repo <主仓> --name <容器名>
    [--add <CIDR> "理由"]... [--remove <CIDR>]... [--reason <CIDR> "新理由"]...
    [--confirm <收据ID>]
uv run python scripts/swt.py network recover --repo <主仓> --name <容器名> [--confirm <收据ID>]
```

均支持 `--records-root`. 末行是 `NETWORK {...}`, 不是 STATE. 返回码沿用主文件的 0/1/2/3/4 含义, 执行失败即使已回退也返回 3. 以 `stage/checks/pending` 判断结果, 不以命令已结束或 SSH 可连当成功.

## 查看与变更

1. **核对目标与现状.** show 只读, 显示地址/用途理由/自动项及 pending/checks, 规则与记录不一致只报告. 只查询时按第 3 项报告后结束. update 仅支持运行中 whitelist 的独占配置目标; 停止/retired/旧共享记录/身份替换/未知规则均拒绝. 先向我报告冲突, 人工收敛另行授权, 不通过重新审批收编未知状态.
   完成标准: 已确定目标身份与实际规则/事务状态; 需要变更时满足 update 条件, 否则转恢复或报告阻塞.
2. **预览本次差异并等我批准.** 用 update 表达增删/理由更正, 不手拼整份名单. 有变化时逐字转述 DECIDE 和差异, 我批准后带脚本给出的 `--confirm <收据ID>` 重跑同一请求, 状态变化须重新批准. 无变化直接返回 0. 旧理由缺失可保留或如实标未核实, 不编造本次用途.
   注意实际网段范围与重叠: 删 /32 不等于收回更大网段或自动 DNS 仍放行的权限, /0 是全部 IPv4/全部端口. 仅 `--reason` 更正理由不重建规则; 若自动项已变, 先用无用户变更的 update 单独审批同步, 再改理由.
   完成标准: 差异已获我的批准并按有效收据执行, 或确认请求无变化.
3. **按实际检查交回结果.** 成功检查覆盖规则/SSH/只读本地 Git 桥/DNS 规则, 不代表上游 DNS 或任务服务已实测; 任务验证另按 [task-conditions.md](task-conditions.md).
   完成标准: 报告 `NETWORK.stage/checks/pending`, 说明失败/回退/残留与下一步; 仅在输出证实完成时称维护成功.

## 复用清单 (约定, 机制未实现)

新 birth 不读任何预设名单: 白名单只来自命令行 `--allow-entry` 或同一母体未终结的记录. 项目级基线放 `<records-root>/<项目slug>/network-allow.conf`, 每行 `<CIDR> <理由...>`, `#` 注释与空行忽略, 理由取到行尾. 起容器时由执行者读出条目, 逐条展开成 `--allow-entry`; 命令行条目优先于文件, 冲突以命令行为准并报告.

只收跨需求稳定项: 依赖源 (Maven Central/镜像/私有仓库), 公司内网固定设施, 共用测试环境. 按需求才用的第三方渠道 (支付/短信/具体业务方域名) 不入, 免把一次性放行固化成默认. 增删按需求评审, 与 `requirements.md` 同属项目级配置, 不进 Git.

`swt.py` 尚未实现自动读取; 机制化须先改脚本并成套分发. 汇报时不得把本约定说成"已自动生效"或"下次会自己带上".

## 未完成事务

中断/回退失败会保留 `network-change`, 此时 update/birth/resume 都须暂停. 先 show 看 pending/checks, 再用 recover 预览本工具事务的旧状态恢复; 按同一审批协议获准后执行. 原完整 ID 仍在的停止目标只恢复记录, 不启动容器.
未知状态或写进程未确认结束时保留现场并报告, 不自动 stop/restart/clear, 不用旧版脚本处理新事务. recover 不接管未知规则或同名新 ID. 如果我明确终结事务原目标, terminate 会保留私有事务审计并清活动标记; 这是终结, 不是网络恢复成功.
完成标准: 旧状态已按 NETWORK 检查恢复且 pending 清除, 或将仍未完成的事务与阻塞明确交还给我.
