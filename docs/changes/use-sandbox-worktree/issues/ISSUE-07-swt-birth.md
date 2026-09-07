# ISSUE-07 swt birth: 诞生全链

## 父级

- `../roadmap/MILESTONE-12.md`; `../EXECUTION-M12.md` (CLI 契约/birth 顺序/测试策略 — 必读, 不重复)
- `../DECISIONS.md`: D007 (母体一名贯穿), D008 (config 模板+写入语义), D010 (单活动母体), D011 (端口策略), D013 (newer-available 只标不拆), D026 (收据), D029 (无关), D031 (两层身份), D032 (nft merge), D034 (锁), D035 (镜像只判不建)
- `../UNAUTHORIZED_DECISIONS.md`: U-002/U-003/U-004 (自动 allow)/U-006 (ssh key/测试镜像)/U-007 (! 重验)
- 下沉来源 (只读): `e2e-smoke.py` 的 `configure_repo`/`expected_config`/`start_daemon`/`create_container`/`assert_container_clone`/端口预选/pasta 探测/拒绝矩阵断言 — 复制改造进 swt.py, 不改原文件
- 前置 ISSUE-05 (骨架/收据/runtime), ISSUE-06 (apply --merge)

## 执行(Execution)

- [x] 已实现

## 要构建什么

`swt birth` 全链 (顺序见 EXECUTION-M12 CLI 契约节, 硬约束 BR-002: config 校验先于 daemon):

1. 前置: 环境检查 (podman/git/nft 缺失 exit 4; git `!` 否定语法 /tmp 迷你仓行为级重验, 失败 exit 4, U-007); 单活动母体不变量 — 本仓已有活动母体 (runtime 或 label 发现存活容器/daemon 且母体分支 ≠ 本次) → exit 2 指引 switch.
2. DECIDE 一次列全 (D026, 改任何资源前):
   - 网络模式未给 → kind=`network-mode` DECIDE (选项 `--mode whitelist --allow ...` / `--mode blacklist [--deny ...]`); whitelist 时 DECIDE 文案含 U-004 自动条目说明.
   - 母体不存在 → kind=`mother-create` DECIDE (`--new-mother`); 母体存在且干净 → kind=`mother-reuse` DECIDE (`--reuse-mother`); 母体存在但脏 → 不是 DECIDE, exit 2 (人工处理).
   - 镜像: 无 `--image` → 经 image-prep `match` (requirements 缺省 `<records-root>/<slug>/requirements.md`, 不存在则 exit 2 提示); verdict=BUILD-NEW → kind=`image-build` DECIDE (附 reason 行, 指引 D014 流程后 `--image` 重跑); REUSE → 用 match 输出 image/digest. 有 `--image` → `podman inspect` 取 digest 直入.
   - 各 DECIDE 收据指纹字段按 D026 子集 (EXECUTION-M12 CLI 契约节).
   - 全部已答 (flag 齐 + 收据指纹全过) 才进入执行; 执行中途新冒问题走 exit 3 不补 DECIDE.
3. 执行: 建母体 (`git worktree add -b <dir值> <dir路径> <base>`, base 缺省主仓默认分支头) 或复用 → `touch .git/git-daemon-export-ok` → config 写前快照+按写入语义写入 (错值 ASSERT-FAIL 级中止=exit 3? 否: 尚未动资源顺序上 config 是第一动 — 写入语义冲突属 exit 2 前置不满足, 不覆盖) → `--get-all` 逐键校验 → daemon 拉起 (socket 预选端口 ≤3 次, 监听地址兜底顺序沿用 e2e-smoke, base-path=主仓所在父目录且断言仅主仓一仓, 不开 --export-all) → 镜像 digest 落 runtime → `podman create --name swt-<dir值>|--name 值 --label 三件套+podman 实例名 -p 22 <image>` → start (exit 125 端口被占 → exit 3 PARTIAL 透传, F006) → `podman inspect` 取容器 IP → **立即 net-firewall apply (--merge 语义; whitelist 自动并 daemon 地址 /32, U-004)** → ssh key 对生成 (U-006) + authorized_keys 注入 + BatchMode 连通断言 → 容器内 `git clone -b <dir值> git://<容器侧daemon地址>:<port>/<reponame>` → 断言 `git branch --show-current` = 母体分支 + `ls-remote` 读面仅母体分支 (HEAD 广告除外, F007) → runtime `stage=born`, STATE 全就绪.
4. 失败清理: 每阶段增量写 runtime (沿用 e2e-smoke 精神); 中途失败 exit 3 `PARTIAL <阶段> <唯一人工恢复路径>` (D037 文案质量); config 写入失败用快照回滚不留半套.
5. 幂等重入: 无 runtime + 同名干净母体 → 复用路径 (仍走 DECIDE); 有 runtime 或同名存活容器 → exit 2 提示先 terminate; 无 runtime 但有存活 daemon → exit 2.
6. newer-available: 在跑容器镜像 digest ≠ 最新候选 → STATE 标 true, 不拆 (D013).
7. 下沉 smoke 验证段: birth 完成后主链验证 (容器内 commit 新文件 → push → 母体目录文件断言; 拒绝矩阵四项 `[remote rejected]`; 母体脏树拒收+还原; 负向收尾 `git reset --hard origin/<母体分支>` 复原) 实现为 swt 内部函数, 供测试经容器内 ssh 驱动 — 不做独立子命令 (D037 修复原语不进 v1), 测试直接经 ssh 断言.

## 允许范围

- 修改 `swt.py`, `tests/test_swt_m12.py`; 本 ISSUE 文件
- /tmp 夹具; `--records-root /tmp/...`; 测试镜像 `localhost/swt-m03:latest` (无则 build); match 路径 scratch 伪镜像
- 只读复制 e2e-smoke.py 函数; 只读调用 slug.py/net-firewall.py/image-prep.py

## 禁止范围

- birth 禁止自动 image-prep build (D035); 禁止自动换端口; 禁止删任何已存在容器/母体
- 禁止实现 resume/terminate/switch (后续 ISSUE)
- EXECUTION-M12 全局禁止范围全部适用

## TDD 切片

- TS-201 主链: 夹具仓 → birth (先 exit 1 DECIDE 列全模式+母体新建+镜像; 带齐 flag 重跑) → exit 0; 断言: 母体 worktree/分支存在, `git config --get-all` 逐项 = D008 模板, daemon 存活且命令行无 --export-all 且 base-path 仅主仓, 容器 running 且 `podman port` 得端口, 容器内分支=母体分支, ls-remote refs 仅母体分支, runtime stage=born, STATE 字段齐.
- TS-202 push 回流: 容器内 commit+push → 母体目录文件内容 = 提交内容 (≤3s 轮询消解落地延迟, M03 实测).
- TS-203 拒绝矩阵: 容器内 push 新分支/tag/non-ff/删除 → 全 `[remote rejected]`; 外部断言主仓 refs 无新增.
- TS-204 母体脏树拒收: 制造母体跟踪文件未暂存改动 → push 被拒 → 还原.
- TS-205 config 故障注入: 预写错值 → birth exit 2, 错值未被覆盖, 无 daemon; 多值键重复值注入同理 (D008 多重集语义).
- TS-206 config 幂等: birth 成功后再 birth (复用路径带 --reuse-mother) → 键不重复.
- TS-207 不变量: 活动母体存在时 birth 另一分支 → exit 2 指引 switch.
- TS-208 DECIDE 协议: 首次 birth 一次列全 (模式+母体+镜像三 kind 同行列出); 收据文件生成; 篡改外部状态 (如改 config) 后带 flag 重跑 → 指纹不符重新 DECIDE; 收据消费后不可复用.
- TS-209 镜像判定: 无 --image 且 requirements 缺失 → exit 2; scratch 伪镜像 REUSE 路径 (M07 形态); BUILD-NEW → DECIDE + --image 重跑收敛; 无 --image 无 match 直接 --image 直入.
- TS-210 nft 联动 (whitelist): birth 后 `nft list table inet swt` 含容器 saddr 规则 + 自动 daemon 地址条目; 容器内 clone 成功本身就是放行证据; 第二个容器 (同母体, --name) birth → --merge 后两 saddr 共存.
- TS-211 中途失败: 端口被占 (占位 socket) → start 失败 exit 3 PARTIAL, exited 容器已登记 runtime; 释放后重跑 birth 收敛 (重入幂等).
- TS-212 exit 4: PATH 缺 podman → ENV.
- TS-213 ssh key: 私钥 0600 落 records-root runtime 目录, 授权后 BatchMode 通.

## 验证入口

`uv run --with pytest pytest tests/test_swt_m12.py` 全绿; `tests/test_swt_m03.py` 回归绿 (e2e-smoke 未动).

## 停止条件

需要改 D 账本语义/扩大范围/引入依赖时停止上报.
