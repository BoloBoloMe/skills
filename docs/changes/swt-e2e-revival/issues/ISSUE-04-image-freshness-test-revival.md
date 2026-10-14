## 父级
- `../EXECUTION.md`
## 执行
- [x] 已实现
## 要构建什么
把 `TestReviewP3ImageFreshness::test_rebirth_reports_newer_candidate_digest` 改成驱动**存活的那条路径** (用户 2026-10-14 裁决: 甲 —— 承认老期望过期, 改测试面, 不动产品代码).

现状与为什么红:
- 该用例 (tests/test_swt_m12.py 约 1408-1431 行) 先 `birth_ready()`, 再把 runtime 记录里容器的 `image-digest` 篡改成 `"sha256:old-running-image"`, 然后带同名重跑 `birth` 期望 rc=0 且 `image.newer-available` 为真.
- 模板化后: (i) 重入固定模板的 born 容器会在 `swt.py` 约 3126-3139 提前返回 "已就绪 (固定模板未重装)", 打印的是 `runtime["image"]` (由 `prepare_image` 显式给出 `verdict=EXPLICIT, newer-available=False`), 不复算; (ii) 篡改 `image-digest` 还会先被 `agent_templates.target` 守卫拒绝, 报 `容器标签/创建令牌/镜像记录不匹配` (rc=2).
存活路径: `swt.py` 的 `image_state()` (约 4684 行) 用 `latest_build_digest(records_root, repo)` 与记录里的 digest 比对产出 `newer-available`, 由 `mothers_states()` (约 4704 行) 组成 `mothers[].image`, 经只读命令输出 (STATE 里含 `mothers[]`, 读法先例见 tests/test_swt_m12.py 约 357 行).

要改成什么 (保持 D013 原意图: 在跑容器的镜像有更新版 → 只标 newer-available, 不自动升级):
- 保留 `birth_ready()` 得到在跑容器;
- 按 `image_state()` 的判据造出"有更新版可用"的事实 (即 `latest_build_digest` 能取到与容器记录不同的 digest; 具体落法读该函数实现, 用测试夹具可写的方式造);
- 跑输出 `mothers[]` 的那条只读命令, 断言对应 mother 的 `image.newer-available` 为真;
- 加一条"只标不升级"的证据: 该容器 record 的 `image-digest` 未变;
- 加一条负向断言: 镜像一致时 `newer-available` 为假.
## 覆盖依据
- `../EXECUTION.md` 完成定义节 + 用户裁决 (甲)
- `docs/changes/swt-container-env-docs/DECISIONS.md` D013 (原语义)
## 相关决策
- `../../swt-container-env-docs/UNAUTHORIZED_DECISIONS.md` UD-015 / UD-017 (该残留的记录)
## 允许范围
- `tests/test_swt_m12.py` (仅该用例及它需要的夹具辅助函数)
## 禁止范围
- `scripts/` 下任何文件; 其他用例的断言; `docs/changes/swt-container-env-docs/` 内任何文件
## 代码定位提示
- `swt.py`: `latest_build_digest` (约 4668), `image_state` (约 4684), `mothers_states` (约 4704, 其中 4773 行调用 `image_state`), 模板重入提前返回 (约 3126-3139), 守卫 (约 3120-3125)
- 测试: `TestReviewP3ImageFreshness` (约 1408-1431), 读 `mothers[]` 的先例 (约 357 行), `self.state()` 的解析方式
## TDD 切片
- TS-001:
  接缝: 接缝 2 (真容器) + 只读命令输出.
  测试用例: 当在跑容器的镜像有更新版可用时, `mothers[].image.newer-available` 为真, 且容器 record 的 image-digest 未变; 镜像一致时为假.
  先写的失败测试: 改写后的断言在现状下会红 (事实构造或路径取错), 先红再补.
  最小绿色实现范围: 只改测试文件.
  不得测试: `image_state` 内部实现细节; 不得放宽或删除原意图的断言.
  覆盖: D013 只标不升级.
## 验证入口
- `uv run --no-project python -m unittest tests.test_swt_m12.TestReviewP3ImageFreshness -v` 全过 (真容器)
- 整套: `uv run --no-project python -m unittest tests.test_swt_m12 -v` = 79 项全过
- `uv run --with pytest python -m pytest -m "not e2e" -q` 失败集合不超过既有 8 项
## 风险提示
- 别把负向断言写成"binary 同义反复": 镜像一致的对照要用真实构造, 不是把刚才的事实清掉再断言.
- 该用例走真容器, 单跑一次开销大; 改完先单跑该用例类, 再跑整套.
## 停止条件
- 若存活路径 (image_state/mothers_states) 在模板化世界里确实无法构造出 newer-available=true, 即 D013 语义真的没有实现面 -> 停下报告, 不要硬改断言
## 适合 AFK 的原因
- 用户已选定方向, 剩忠实改写与构造证据
## 验收标准
- [ ] 该用例改为驱动存活路径且真容器通过; 整套 m12 79 项全绿; 快层不新增红
## 被阻塞于
- 无
