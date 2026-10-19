# AC-002-1 删除后本机读取

性质: 当前观察, 独立验收者 B 本轮实际操作. 工作目录: `/tmp/orchestra-10/methods-red`.
判据只取 PRODUCT.md 的 confirmed-flow v1. 无旧观察, 不用实现者说明或作者自证, 未读产品代码推断结果.

## record-dump

原文要求: 本机 record-dump r1 显示记录不存在.

完整命令:
```bash
uv run python app.py record-dump r1 --data-dir runtime/data
```
原始元数据:
```text
command: uv run python app.py record-dump r1 --data-dir runtime/data
start: 2026-10-19T16:21:59,029008106+00:00
end: 2026-10-19T16:21:59,069532730+00:00
exit_code: 0
```
原始 stdout:
```text
record absent id=r1
```
原始 stderr:
空, 0 字节.

结论: 此项本机判据通过. 实际显示 `record absent id=r1`, 退出码 0.

## records.jsonl 额外事实核对

完整命令:
```bash
uv run python -c 'from pathlib import Path; import json; p=Path("runtime/data/records.jsonl"); lines=p.read_text().splitlines(); hits=[(n,s) for n,s in enumerate(lines,1) if json.loads(s).get("id")=="r1"]; print("path="+str(p)); print("r1_line_count="+str(len(hits))); [print(str(n)+":"+s) for n,s in hits]'
```
原始元数据:
```text
command: uv run python -c from\ pathlib\ import\ Path\;\ import\ json\;\ p=Path\(\"runtime/data/records.jsonl\"\)\;\ lines=p.read_text\(\).splitlines\(\)\;\ hits=\[\(n\,s\)\ for\ n\,s\ in\ enumerate\(lines\,1\)\ if\ json.loads\(s\).get\(\"id\"\)==\"r1\"\]\;\ print\(\"path=\"+str\(p\)\)\;\ print\(\"r1_line_count=\"+str\(len\(hits\)\)\)\;\ \[print\(str\(n\)+\":\"+s\)\ for\ n\,s\ in\ hits\]
start: 2026-10-19T16:21:59,078128342+00:00
end: 2026-10-19T16:21:59,105203159+00:00
exit_code: 0
```
原始 stdout:
```text
path=runtime/data/records.jsonl
r1_line_count=0
```
原始 stderr:
空, 0 字节.

purge 后立即复制的 records.jsonl 全文 (`03-after-purge.records.jsonl`):
```jsonl
{"id": "r2", "text": "beta"}
```

结论: 本轮当前数据文件中 r1 行数为 0, 不存在仍可从该文件直接读到 r1 的行. 此事实仅支持本机部分, 不证明仓外副本不可读取, 也不声称覆盖其他未知介质. AC-002-1 完整场景仍为未验证.
