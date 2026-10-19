# 无效演练: frontmatter 解析失败导致技能没被加载

这四份日志是 ISSUE-01 的第一批演练, 结论作废, 只作事故记录保留:

- `drill-G1a-green-criteria.log`, `drill-G1b-green-missing-product.log`, `drill-R2-red-dirty-accepted.log`: 用当时只有判据规则的中间稿跑, 会话在启动横幅的 `[Skill conflicts]` 段报:

  ```text
  [Skill conflicts]
    /tmp/orchestra-01/a-committed-clean/.agents/skills/verify-change/SKILL.md
      Nested mappings are not allowed in compact mappings at line 2, column 14:
  description: 独立产品验收: 只按被验项目已确认的 PRODUCT.md 逐项核对最终成品.
               ^
  ```

  实际原因是当时的 `description` 写成 `独立产品验收` 后接 "冒号+空格" 再接正文, 裸标量里的这个组合被 YAML 当成嵌套映射, 技能因此没有注册; 会话只是手工读取了同路径文件再照做, 不构成 `/skill:verify-change` 公开加载入口可用的证据.

- 同批次的 `drill-G1a-evidence-dir/`, `drill-R2-into-repo-evidence/` 是那些会话写出的产物, 一并保留.

处理: 把 `description` 改成不含 "冒号+空格" 的写法, 重跑全部演练, 正式证据在上一级目录. `check_skill.py` 在 `disable-model-invocation: true` 时允许 description 出现冒号, 与 pi 的实际 YAML 解析不一致, 这条机检缺口已写入 HANDOFF, 本 ISSUE 的禁止范围不允许改 `general/`.
