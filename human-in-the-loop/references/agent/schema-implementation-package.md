# Implementation Package Schema

通用头字段和禁止字段见 `schema-common.md`。

## planning/implementation-package

这是独立资产，但只包含引用与摘要，不复制完整正文。必须记录：

- facts / design / blueprint 的 asset_ref；
- 引用资产 path，必须等于 registry.path；
- 引用资产 sha256；
- 人类可读摘要；
- 批准范围说明；
- 风险摘要；
- 验证摘要；
- 授权进入 asset-check 的资产列表。

`authorized_assets` 必须与 `references[].asset_ref` 完全一致，由 `scripts/compose_implementation_package.py` 自动写入；不得授权未被 hash-bound 的额外资产。
