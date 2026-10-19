#!/usr/bin/env bash
# run-batch-count.sh -- AC-002-3 批量统计 250 次的执行记录原件 (verifier-b, 2026-10-19)
#
# 如实说明: 当时没有把循环写成脚本文件执行, 而是把下面 BEGIN/END 之间这段命令
# 原样粘贴进 bash 一次性内联执行的 (工作目录 verifier-b/). 本文件是该次实际执行
# 的命令行文本的逐字抄录, 不是事后改写的脚本; 除本注释头外未增删任何字符.
# 运行轮次: 2026-10-19T20:45:59+08:00 起, 20:46:10+08:00 止, 仅此一轮.
#
# 可以看出: while 循环每读一行 expected.tsv 就执行一次 $(python3 ...tool.py count
# --file ...), 即每次循环都启动一个独立的 python3 tool.py count 进程; $() 内命令
# 的 stdout 存入 out, 其退出码由紧随其后的 rc=$? 捕获; 实际输出/期望/退出码与是否
# 一致 (OK/MISMATCH) 一并写入明细行, 经 tee 落盘到 ac002-3-detail.tsv.

### BEGIN (verbatim)
cd /tmp/orchestra-03/heavy/three-groups-2avail/docs/changes/tool-cli/evidence-c0505de-r1/verifier-b && date -Is > ac002-3.log && pass=0; fail=0; n=0; while IFS=$'\t' read -r fname exp; do n=$((n+1)); out=$(python3 /tmp/orchestra-03/heavy/three-groups-2avail/tool.py count --file "/tmp/orchestra-03/heavy/three-groups-2avail/data/count/docs/$fname"); rc=$?; if [ "$out" = "$exp" ] && [ $rc -eq 0 ]; then st=OK; pass=$((pass+1)); else st=MISMATCH; fail=$((fail+1)); fi; printf '%03d\t%s\t%s\t%s\t%d\t%s\n' "$n" "$fname" "$out" "$exp" "$rc" "$st"; done < /tmp/orchestra-03/heavy/three-groups-2avail/data/count/expected.tsv | tee ac002-3-detail.tsv | awk -F'\t' '{print $6}' | sort | uniq -c; date -Is >> ac002-3.log; echo "PASS=$pass FAIL=$fail TOTAL=$n" | tee -a ac002-3.log
### END (verbatim)

# 补充: 当时实际执行的 250 条子进程命令中, 首条与末条的完整命令行文本如下
# (由上述循环对 expected.tsv 第 1 行 doc001.txt 与第 250 行 doc250.txt 展开所得):
#
# 首条:
#   python3 /tmp/orchestra-03/heavy/three-groups-2avail/tool.py count --file /tmp/orchestra-03/heavy/three-groups-2avail/data/count/docs/doc001.txt
# 末条:
#   python3 /tmp/orchestra-03/heavy/three-groups-2avail/tool.py count --file /tmp/orchestra-03/heavy/three-groups-2avail/data/count/docs/doc250.txt
#
# 与 ac002-3-detail.tsv 首行 "001	doc001.txt	2	2	0	OK" 和末行
# "250	doc250.txt	8	8	0	OK" 对应, 可逐条复核.
