# milestone-22 准备物检查记录

本记录由协调会话写入, 不代替 milestone-08 的终点验收; 它覆盖 milestone-22 自己的完成标准: present 改造(milestone-15)的 PRODUCT/TECHNICAL/EXECUTION/issues 可读, 无未处理的标准或验证契约缺口, milestone-15 可按 drive-execution 派工.

## 产物

- 产品规格: [../milestone-15/PRODUCT.md](../milestone-15/PRODUCT.md) (41 场景 / 7 AC, 对应 AC-15-01..07; 用户 2026-11-01 采纳 review_id `eaf9d2bb96b451f7cccccf847896a76d73026be9c887f91e57a37b3794f9e548`)
- 技术规格: [../milestone-15/TECHNICAL.md](../milestone-15/TECHNICAL.md)
- 执行输入: [../milestone-15/EXECUTION.md](../milestone-15/EXECUTION.md) 与 [../milestone-15/issues/](../milestone-15/issues/) (ISSUE-01 至 ISSUE-05)

## 实际检查

1. 验收草稿机检 (草稿模式), 每次修改后重跑:
   `uv run workflow/to-spec/check-ac.py /tmp/to-spec-ac-b9g3hc52/PRODUCT.base.md --draft /tmp/to-spec-ac-b9g3hc52/review/AC-draft-v5.md`
   结果: 通过 - 41 个场景, 7 个 AC, 退出码 0.
2. 转正: `uv run workflow/to-spec/ac-draft.py promote ... --review eaf9d2bb96b4...`, `success: true`.
3. 正式产品规格机检: `uv run workflow/to-spec/check-ac.py docs/changes/workflow-stack-review/milestone-15/PRODUCT.md` → 通过 - 41 个场景, 7 个 AC.
4. 技术规格机检: `uv run workflow/to-spec/check-tech.py docs/changes/workflow-stack-review/milestone-15/TECHNICAL.md` → 通过 - 7 节.
5. 拆分基线核对: `uv run python -m pytest general/present/tests --collect-only -q` → 143 条, 其中 browser_session 相关 63 条, 与 EXECUTION.md 完成定义记录一致.
6. 独立检查: [SPEC-REVIEW.md](SPEC-REVIEW.md) (gpt-6.1-sol, 未参与编写) 报 7 阻断 + 4 建议, 协调方逐项核实全部成立并修订.
7. 独立补核: [SPEC-RECHECK.md](SPEC-RECHECK.md) (glm-5.3-flash, 未参与编写) 判定 B02-B07 与 A01-A04 共 10 项闭环, 残留 B01 (TECHNICAL 模块接口的容器 URL 端口口径) 与建议 N2 (loopback_bind 归属歧义).
8. 协调方收尾 (本轮无第三轮独立复核, 结论只覆盖这两句):
   - B01: 模块接口 start/status 的 URL 端口补环境限定 (宿主用监听端口, 容器用 8800 的宿主映射端口), `loopback_bind` 移出"不给 url"的错误码族 → 改后 check-tech 通过.
   - N2: 同上, 由 loopback 专用契约承接.
   - `--lan-host` 适用范围按 D011 写明只作用于宿主分支, 容器固定用 `SWT_HOST_LAN_IP` + `SWT_HOST_WEB_PORT`; EXECUTION.md 里原来的"待裁决点"随之改为已定口径, ISSUE-01 同步一行.
9. EXECUTION/issues 抽查: 每个 issue 有 验证契约/验证入口/交付证据, 覆盖矩阵把 AC-001..007 与 BR-001..019 逐条落到 issue 或人工核验; 审计 BR-014/015/016 走人工核验; 评审起点写"待填", 等 drive-execution 首次派工填入.

## 边界与未验证

- 本轮只准备输入, 没有实现 present 改动, 没有跑 present 相关 pytest, 没有跑 check_skill.py, 没有修改真实已安装 skills, 没有运行同步.
- 没有启动或验证 milestone-15 的新行为; AC-15 全部标准仍是待实现的验收项.
- 两份独立报告用的是两个第三方模型的只读检查, 不构成用户验收.
- 本会话环境缺 `SWT_HOST_LAN_IP`/`SWT_HOST_WEB_PORT`; 容器 8800 的宿主映射端口经信箱向宿主会话问得 `41141` (宿主实测 `http://192.168.65.165:41141/` 返回 200), 只用于本次预览交付, 不写成 milestone-15 的执行证据.
