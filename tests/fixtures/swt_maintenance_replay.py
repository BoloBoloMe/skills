"""公共指导的固定场景执行/回放夹具, 不是自动 agent/探测框架.

审批事件为规格给定场景输入, 不替代真实现场批准; 工具链/缓存是模拟响应.
仅 HTTP/缓存操作/Git/原码捕获从独立资源实测. 不导入即执行, 不访问共享服务.
用法: uv run python tests/fixtures/swt_maintenance_replay.py [证据JSON路径]
"""
import http.server,json,subprocess,sys,tempfile,threading,shutil
from datetime import datetime,timezone
from inspect import cleandoc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_swt_network_e2e import Sandbox,command


def replay(output_path=None):
    root=Path(tempfile.mkdtemp(prefix='swt-replay-'))
    sandbox=Sandbox(root/'sandbox'); requests=[]; cache={}; reject_delete=False
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            requests.append(('GET',self.path))
            if self.path=='/artifact/ok':
                body=b'<project><groupId>com.example</groupId><artifactId>demo-parent</artifactId><version>1.0</version></project>';code=200
            elif self.path=='/artifact/401':body=b'authentication denied';code=401
            elif self.path=='/context/redis':body=b'fixture service unavailable';code=503
            elif self.path=='/artifact/redirect':
                self.send_response(302);self.send_header('Location','/login');self.end_headers();return
            else:body=b'<html>fixture login page</html>';code=200
            self.send_response(code);self.end_headers();self.wfile.write(body)
        def do_POST(self):
            data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append((data['operation'],data['resource'],data['key']))
            k=(data['resource'],data['key']);op=data['operation'];code=200
            if op=='SET':cache[k]=data['value'];value='OK'
            elif op=='GET':value=cache.get(k)
            elif op=='DEL' and reject_delete:value='permission denied';code=403
            else:cache.pop(k,None);value='OK'
            self.send_response(code);self.end_headers();self.wfile.write(json.dumps({'result':value}).encode())
    server=http.server.ThreadingHTTPServer(('0.0.0.0',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    evidence={}
    try:
        sandbox.up();gateway=sandbox.host.locate(sandbox.request).context['gateway']
        base=f'http://{gateway}:{server.server_port}'
        tool_script="mkdir -p /tmp/check-bin; printf '#!/bin/sh\necho fixture-JDK-8\n' >/tmp/check-bin/java; printf '#!/bin/sh\necho fixture-Maven\n' >/tmp/check-bin/mvn; chmod 700 /tmp/check-bin/*"
        command(['podman','exec',sandbox.id,'sh','-c',tool_script])
        tools=command(['podman','exec',sandbox.id,'sh','-c','/tmp/check-bin/java -version; /tmp/check-bin/mvn -version']).splitlines()
        command(["podman", "exec", sandbox.id, "python3", "-c",
                 "import json; from pathlib import Path; p=Path('/tmp/fixture-credential.json'); p.write_text(json.dumps({'token':'fixture-only'})); p.chmod(0o600); assert p.is_file()"])
        checked_at=datetime.now(timezone.utc).isoformat()
        script=cleandoc('''import json,sys,urllib.request,urllib.error,xml.etree.ElementTree as ET
    try:
        with urllib.request.urlopen(sys.argv[1],timeout=3) as r:body=r.read();status=r.status
        node=ET.fromstring(body)
        valid=(node.tag=="project" and node.findtext("groupId")=="com.example" and node.findtext("artifactId")=="demo-parent" and node.findtext("version")=="1.0")
        print(json.dumps({"http":status,"operation":"通过" if valid else "受阻","reason":"指定构件可解析" if valid else "返回登录页而非所需构件"},ensure_ascii=False))
    except urllib.error.HTTPError as e:print(json.dumps({"http":e.code,"operation":"受阻","reason":"认证拒绝"},ensure_ascii=False))
    ''')
        outcomes=[json.loads(command(['podman','exec','-i',sandbox.id,'python3','-',base+'/artifact/'+p],input=script)) for p in ('ok','401','redirect')]
        assert [o['operation'] for o in outcomes]==['通过','受阻','受阻'],outcomes
        evidence['AC-018']={'commands':['podman exec TARGET /tmp/check-bin/java -version','podman exec TARGET /tmp/check-bin/mvn -version','podman exec -i TARGET python3 - FIXTURE_URL/artifact/{ok,401,redirect}'],'tool-responses':tools,'artifact-results':outcomes,'unused-redis-requests':0,'credential-file-present':True,'note':'工具链响应是夹具; 构件获取与内容核对实际从独立容器执行'}
        old_count=len(requests)
        # 同任务条件未变的交付核对不再次请求; 增加上下文测试只列新增条件与缺口.
        assert len(requests)==old_count
        context_script=cleandoc('''import json,sys,urllib.request,urllib.error
    try:
        with urllib.request.urlopen(sys.argv[1],timeout=3) as r:print(json.dumps({"http":r.status}))
    except urllib.error.HTTPError as e:print(json.dumps({"http":e.code,"operation":"受阻"},ensure_ascii=False))
    ''')
        context_result=json.loads(command(['podman','exec','-i',sandbox.id,'python3','-',base+'/context/redis'],input=context_script))
        assert context_result['http']==503 and len(requests)==old_count+1
        evidence['AC-019']={'original-check-time':checked_at,'delivery-reference-time':checked_at,'duplicate-artifact-requests':0,'new-context-only-check':context_result,'unaffected-build-checks':'不重跑'}
        assert not [r for r in requests if len(r)==3]
        approval={'task':'fixture-task','resource':'fixture-redis-a','key':'swt-ac-probe','operations':['SET','GET','DEL'],'cleanup':'DEL 后 GET 确认不存在'}
        post=cleandoc('''import json,sys,urllib.request,urllib.error
    body=json.dumps({"resource":sys.argv[2],"key":"swt-ac-probe","operation":sys.argv[3],"value":"fixture"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(sys.argv[1],data=body,headers={"Content-Type":"application/json"}),timeout=3) as r:print(r.read().decode())
    except urllib.error.HTTPError as e:print(json.dumps({"error":e.code}))
    ''')
        def probe(op):return json.loads(command(['podman','exec','-i',sandbox.id,'python3','-',base+'/cache','fixture-redis-a',op],input=post))
        results=[]
        for repeat in range(2):
            one=[probe(op) for op in ('SET','GET','DEL','GET')];assert one[-1]['result'] is None;results.append(one)
        assert not [r for r in requests if len(r)==3 and r[1]=='fixture-redis-b']
        reject_delete=True
        failed=[probe(op) for op in ('SET','GET','DEL','GET')]
        assert failed[-2]['error']==403 and failed[-1]['result']=='fixture' and ('fixture-redis-a','swt-ac-probe') in cache
        evidence['AC-021']={'before-approval-writes':0,'scenario-approved-scope':approval,'approval-events':1,'same-scope-rechecks':results,'changed-resource-or-operation':'先提出新批准范围, 未执行','cleanup-failure':{'operation':'SET/GET 成功','DEL':403,'residue':'fixture-redis-a/swt-ac-probe','overall':'不计为整项通过'}}
        evidence['AC-020']={'login':'通过 (独立容器 SSH 实测)','dependency':'指定构件检查通过','context-test':'受阻, 新增服务模拟响应 HTTP 503','write-permission-before-approval':'未检查','independent-work':'可继续代码阅读','note':'本回放未执行上下文测试或代码阅读, 不报告为完成'}
        home=root/'fixture-home';(home/'.secrets').mkdir(parents=True)
        secret=home/'.secrets/service.json';secret.write_text(json.dumps({'token':'fixture-secret-not-output'}));secret.chmod(0o600)
        config=root/'project-config.json';config.write_text(json.dumps({'credential-source':str(secret)}))
        source=Path(json.loads(config.read_text())['credential-source']);assert json.loads(source.read_text())['token']
        related=root/'related-repo';related.mkdir();(related/'settings.json').write_text('{}')
        search=subprocess.run(['rg','-l','--glob','*.json','credential-source',str(related)],capture_output=True,text=True,timeout=3)
        assert search.returncode==1
        evidence['AC-022']={'sources':['project-config.json:credential-source','fixture-home/.secrets/service.json'],'report':'已找到配置指向来源, 不输出秘密值','home-wide-searches':0,'missing-source-targeted-command':'rg -l --glob *.json credential-source FIXTURE_RELATED_REPO','targeted-search-returncode':search.returncode,'missing-source-replay':'已知来源/相关仓库无结果后先说明必要性/范围, 等决定; 未实际扩大搜索'}
        repo=root/'git-source';remote=root/'git-remote.git';branch='refs/heads/feat/spec-fixture'
        command(['git','init','-b','feat/spec-fixture',str(repo)])
        command(['git','-C',str(repo),'config','user.name','fixture']);command(['git','-C',str(repo),'config','user.email','fixture@example.invalid'])
        (repo/'evidence').write_text('fixture\n');command(['git','-C',str(repo),'add','evidence']);command(['git','-C',str(repo),'commit','-m','fixture'])
        command(['git','init','--bare',str(remote)]);command(['git','-C',str(repo),'push',str(remote),branch])
        left=command(['git','-C',str(repo),'rev-parse',branch]).strip();right=command(['git','ls-remote',str(remote),branch]).split()[0]
        assert left==right and len(left)==40
        evidence['AC-023']={'commands':['git -C FIXTURE_REPO rev-parse refs/heads/feat/spec-fixture','git ls-remote FIXTURE_REMOTE refs/heads/feat/spec-fixture'],'full-id':left,'same-branch-id':True,'clones-for-comparison':0,'report':'仅该分支无新增提交待推, 不推断其他分支/未提交文件一致'}
        shell=cleandoc('''output=$(mktemp) || exit 2
    if git ls-remote "$1" "$2" >"$output" 2>&1; then original_rc=0; else original_rc=$?; fi
    head -n 2 "$output" >/dev/null
    filter_rc=$?
    rm -f "$output"
    printf 'original_rc=%s filter_rc=%s\\n' "$original_rc" "$filter_rc"
    exit "$original_rc"
    ''')
        codes=[]
        for path in (remote,root/'does-not-exist'):
            r=subprocess.run(['bash','-c',shell,'fixture',str(path),branch],capture_output=True,text=True,timeout=10)
            codes.append({'returncode':r.returncode,'evidence':r.stdout.strip()})
        assert [c['returncode'] for c in codes]==[0,128]
        evidence['AC-024']=codes
        evidence['fixture-log']={'http-and-cache-operations':requests,'shared-services-accessed':0,'business-targets-accessed':0}
        if output_path is not None:
            output_path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(evidence,ensure_ascii=False,indent=2))
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)
        sandbox.down();shutil.rmtree(root,ignore_errors=True)


if __name__ == "__main__":
    replay(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
