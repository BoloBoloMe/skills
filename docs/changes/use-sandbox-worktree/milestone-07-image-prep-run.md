# MILESTONE-07 镜像制备实现结果 (ISSUE-03)

日期: 2026-09-05. 验证命令: `uv run --with pytest pytest tests/test_swt_m07.py` (30 用例全绿, 119s).

## 交付物

- `workflow/use-sandbox-worktree/scripts/image-prep.py`: build-base / match / build 三子命令.
- `tests/test_swt_m07.py`: 30 用例 (单元 + podman 端到端).
- `issues/ISSUE-03-image-preparation.md`: 可执行 ISSUE (含最小接缝补钉清单).

## 实测事实 (TestBaseBuildE2E, 真实 base 构建)

- base 镜像实构建成功, 容器内实测: git 2.39.5, node 24.20.0, pi 0.85.0, uv 0.12.10, fd 8.6.0, rg 13.0.0, sshd 9.2 (contents.md 与 label contents-digest 一致).
- 契约核验: sshd 前台 CMD (M03 沿用), EXPOSE 22/8800/6080 (宿主端口不钉), staging 排除 auth.json/sessions (D018), 无 ~/AGENTS.md ~/docs (D023), 无门禁类扩展 (D014).
- access-web/browse 与 present 的 pyproject 存在, base 构建内 uv sync 真实运行 (present 无依赖, browse 装 playwright>=1.40 包; 浏览器二进制归 M09/项目层).
- match 端到端: REUSE 取 build-id 最新/base-digest 硬谓词/谓词不满足与缺失即 BUILD-NEW/多余项容忍/记录篡改 (digest 不符) 跳过该候选, 全部按 D017.
- build 流: 谓词失败退出码 1 (VERIFY-FAIL) 且不打 tag; 坏清单退出码 2; build-id 日期-序号锁内分配查重; 再 match REUSE 同 digest.

## 过程中实锤的实现级事实 (不在任何权威输入中, 已按最小方式处理)

1. `podman build FROM base@digest` 在项目层无 RUN 行时产出与 base 相同 image ID (podman 同 config 去重). phase-1 收尾清理若不设防会删掉共享的 base 本体 — 已加同 ID 跳过清理守卫.
2. ID 格式三态: `podman images` 默认短 12 位, `--no-trunc` 带 `sha256:` 前缀 71 位, `podman build -q` 裸 64 位 hex. 比较前必须归一化 (resolve_base 已做).
3. image label 不可原地改 (M05 结论), 采用 预build → 实测 → 二次 build (层缓存仅改 config) 落 contents-digest.
4. `podman inspect` 不接受裸 manifest digest 作 ref, 按 image ID 查 label.

## 待用户追认 (ISSUE-03 最小接缝补钉节)

- requirements.md 行格式与谓词集 (>= <= > < == + 裸名称), install=/probe= 指令; 探测缺省 `<name> --version`.
- reference 前缀缺省 `localhost/sandbox-worktree` (M05 推荐), base 为 `<prefix>/base`; build-id = tag 同格式日期-序号; build.json 为记录目录机器索引; slug 冲突后缀 sha1[:8]; `base` 保留 slug.

## 边界与遗留

- 容器创建/容器 label (identity/worktree-path/image-digest)/宿主动态端口分配: 无权威输入, 未落地 (归诞生流程, M11); 本里程碑只落 EXPOSE 端口契约.
- M03 回归 (`uv run --with pytest pytest tests/test_swt_m03.py`) 尚未跑 — ISSUE-03 验证入口要求全绿, 待执行.
- roadmap/MILESTONE-07.md 状态未动; 未提交 git (待用户确认后按 ISSUE 提交).
- 本会话曾两次误操作已改正: 误删自写测试文件 (已重写), 驱动脚本曾在仓库根落 scB/scC/scD 临时文件 (已清理, git status 无残留). pi/AGENTS.md 有用户改动, 未触碰.
