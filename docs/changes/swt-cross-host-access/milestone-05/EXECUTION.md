# MILESTONE-05 网页访问实施 EXECUTION

任务书: [MILESTONE-05.md](../roadmap/MILESTONE-05.md). 权威输入: [M04 决策账本](../milestone-04/DECISIONS.md) (D001-D013/F001-F008), ADR [0012](../../../adr/0012-container-web-direct-access.md), [M03 交付](../milestone-03/EXECUTION.md) (信箱能力), [词汇表](../../../language/UBIQUITOUS_LANGUAGE.md), [UNAUTHORIZED_DECISIONS.md](UNAUTHORIZED_DECISIONS.md) (UD-01 起).

工作模式: AFK 自主推进 (probe task 类型, 设计与验收已经 M04 与用户闭环; EXECUTION 为总指挥自拟, 见 UD-01), 自主决定逐条落 UNAUTHORIZED_DECISIONS.md.

## 全局约束

- 只处理改动后新建的容器 (D009); 不改造/迁移/重建现有容器, 旧容器输出与行为不变.
- 测试设计已由 D011 回答, 不再回问用户 (UD-02); 接缝 = swt CLI 可观察行为 (DECIDE 行/交付输出/STATE) 与 present 公开命令+HTTP, 不测内部实现.
- swt 测试沿用 test_swt_birth_mailbox.py 约定: importlib 加载 swt.py, fake `run` 替换 podman 边界, tmpdir 当 records_root, 不依赖 podman.
- present 测试沿用 general/present/tests 既有约定 (真实 HTTP 回环).
- 服务端/swt 零新增第三方依赖, Python 标准库.
- 测试命令 `uv run --with pytest python -m pytest tests/...` (本环境无 pytest 可执行, `--with` 临时供给); 本环境 (sandbox) 无 podman, 需真 podman 的路径不宣称通过, 留 M09.
- 镜像重建/分发超出本环境能力: 交付仓库改动 + 分发步骤文档, 实际重建留 host/M09 (UD-08).
- 提交粒度: 每 ISSUE 一次 `feat: ISSUE-<NN>: <描述>` (文档类 ISSUE 用 `doc:`), 只 stage 本 ISSUE 文件; MILESTONE-06.md 为另一会话脏文件, 永不 stage.

## ISSUE 列表

- [x] ISSUE-01: swt birth 发布 8800 + STATE web-port 登记
  - 范围: `create_and_start_container` 加 `-p 8800` (宿主 0.0.0.0 动态, 与 `-p 22` 同款); 新增 web 端口回读 (仿 container_vnc_port, 无映射容错 None); `web-port` 登记三处: record 初始化 / refresh_container / podman_container_state (status 重建条目). 旧容器无映射时 web-port=None 不崩.
  - 依据: D001/D003/F001. 接缝: fake-run 断言 create 参数含 `-p 8800` 且无回环绑定; `podman port <名> 8800` 回读入 record/STATE.
- [x] ISSUE-02: LAN 地址确认机制 (D010)
  - 范围: `--lan-ip <ipv4>` flag; 已确认值持久化到 records_root 根级文件; birth 无已确认值且未给 flag → 决策收据新增 kind `lan-address`, DECIDE 行 exit 1 (候选 = lan_ip() 现算值仅作提示, 不交付); 确认后写入; 交付用址一律取已确认值 (UD-03).
  - 依据: D010/F006 + 旧图 M14 第 3 项移交 (顺带取代其猜测式选址). 接缝: swt CLI 行为 (DECIDE 行/flag 消费/持久化/指纹失配重问).
- [x] ISSUE-03: 双 URL 交付 (birth/resume/status)
  - 范围: print_delivery_lines 增 web 本机 URL (`http://127.0.0.1:<web-port>`) 与局域网 URL (`http://<已确认地址>:<web-port>`), 仅当容器有 web-port; birth/resume 交付接入; status 对有 web-port 容器附同样双 URL 行 (UD-04); 无 web-port 旧容器输出不变; birth 只交付入口不自动打开 (D005).
  - 依据: D003/D005/D007. 接缝: 交付输出文本断言 (含只列自身 URL, 不汇总其他母体).
- [x] ISSUE-04: 一母体一活跃容器 (D003)
  - 范围: birth 时同母体已有活跃容器 → 拒绝 (含 born 重入加新 --name 路径); 同名重入 (失败重试) 仍允许; 报错信息指引先 terminate 旧容器; 不追溯既有容器; resume/terminate/switch 的多容器兼容逻辑不动.
  - 依据: D003/F004. 接缝: birth 拒绝/放行行为.
- [ ] ISSUE-05: present 容器分支钉 8800 + 锁端口
  - 范围: web_server.py start 增 `--fixed-port` (锁定态持久化, status 重建遇锁定实例端口被占 → 报错不换端口, UD-05); general/present/SKILL.md 容器分支钉 `start 8800 <root> --bind 0.0.0.0 --fixed-port`, 多页复用 add-dir 单实例; 非锁定用法行为不变.
  - 依据: D001/D002/F002. 接缝: present 公开命令 + HTTP 行为 (锁定重建报错/复用 add-dir/bind 冲突).
- [ ] ISSUE-06: 信箱查网址/回话/代开指引 + 当前设备 (文档级)
  - 范围: use-sandbox-worktree/SKILL.md 信箱章节增补: 当前设备确定流程 (UD-06); 展示信件 `to` 显式填当前设备, body 必带容器名+宿主定位+原会话标识; 设备侧配方 (收信 → ssh/herdr 查 STATE/podman port → 回话原会话 → xdg-open 一次); open_url 用法示例; 信箱未运行时交付包链接降级路径 (D007); 不以缺省轮询路由冒充当前设备 (F007).
  - 依据: D005/D006/D007/D012/F005. 无代码接缝; 真链验证归 M09 (TC-004).
- [ ] ISSUE-07: use-sandbox-worktree SKILL.md 修正与分发说明
  - 范围: 修正与 D003 冲突的多容器说法 (L10/L66/L101/L122/L131 段); 交付包定义加 web 双 URL (L15 段); 8800 发布说明 (L97 段, 0.0.0.0 动态, 与 6080 回环对照); 展示链段更新 (L95 段); 分发说明 (D013: swt/SKILL 经 sync-to-pi 到 host 即效, present 改动需 base 重建级联, UD-08).
  - 依据: D001/D003/D013. 文档 ISSUE.
- [ ] ISSUE-08: e2e 门禁测试
  - 范围: tests/test_swt_web_access.py (UD-07): 覆盖 D011 可在本环境自动化部分 — ISSUE-01/02/03/04 全行为 + present 钉端口/复用; TC-001/TC-004 真机双机部分标注待 M09, 不记通过.
  - 依据: D011. 必过门禁.

## 顺序与依赖

ISSUE-01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 串行 (单执行者; 01-04 同文件 swt.py, 05 独立但单执行者排队; 06/07 同文件 SKILL.md).

## 已知风险

- present 规则入容器需 base 重建 (D013/F008), 本环境不可执行 → UD-08, 与 M08/M09 协调; 不宣称已生效.
- TC-001 (真机点击) / TC-004 (双设备取信+换电脑) 无法在本环境验证 → 待 M09, 收口汇总逐条明示.
- M06 (直飞盘问) 在另一会话进行中, 其产物 (脚本母本制等) 不改本执行文件; MILESTONE-06.md 脏文件不 stage.
