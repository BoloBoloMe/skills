验收运行材料 (供复核复跑):
- verify.py.txt: 逐场景运行脚本, 用 python3 在项目根目录执行; 每条命令的 argv 以 JSON 数组写进各用例目录 argv.json, 避免 shell 引号丢失.
- health_stub.py.txt: AC-004-1 前提 "已取得健康服务地址与访问凭据" 所指的本机健康服务桩, 绑定 127.0.0.1:18080, 返回 {"status": "ok", "ready": true}.
- runner-stdout.txt: 运行脚本的完整标准输出.
复跑方法 (在项目根目录, 需 18080 端口空闲):
  mkdir -p /tmp/acceptance-bb25738
  cp docs/changes/tool-cli/evidence-v1-bb25738/provenance/verify.py.txt /tmp/acceptance-bb25738/verify.py
  cp docs/changes/tool-cli/evidence-v1-bb25738/provenance/health_stub.py.txt /tmp/acceptance-bb25738/health_stub.py
  python3 /tmp/acceptance-bb25738/verify.py
注意: 复跑会覆盖本证据目录内用例文件; 需保留原始结果时改用别处输出目录.
