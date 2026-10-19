# AC-003-1 记录列表

判据来源: `docs/changes/vault/PRODUCT.md`, confirmed-flow v1.
原文: 假定测试数据目录 runtime/data 已初始化; 运行 record-list; 输出含 `id=r1` 与 `text=alpha`, 退出码为 0.
性质: 当前观察, 本轮实际运行. 工作目录: `/tmp/orchestra-10/methods-red`.

## 假定核对

本轮唯一一次初始化成功, 引用同组当前观察 `00-init.md` 及其文件快照, 非作者自证或旧观察.
`2026-10-19T16:20:56,716598951+00:00` 核对命令:
```bash
test -d runtime/data && test -f runtime/data/records.jsonl
```
结果: 条件成立, `data_dir_and_records_present: yes` (见 `01-record-list.meta.txt`).
尚未执行 purge, 本次命令先于 purge.

## 实际运行

完整命令: `uv run python app.py record-list --data-dir runtime/data`
开始: `2026-10-19T16:20:56,719088191+00:00`.
结束: `2026-10-19T16:20:56,765377390+00:00`.
退出码: `0`.

原始 stdout (`01-record-list.stdout.txt`):
```text
id=r1 text=alpha
id=r2 text=beta
```
原始 stderr (`01-record-list.stderr.txt`): 空, 0 字节.
元数据原件: `01-record-list.meta.txt`.

## 结论

**AC-003-1: 通过.** 初始化假定成立, stdout 实际同时含 `id=r1` 和 `text=alpha`, 退出码 0.
