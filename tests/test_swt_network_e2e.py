"""独立 pasta 容器 + 本地 Git 桥 + 私有 DNS 网络空间, 不触业务表/认证/服务.

运行: uv run python -m pytest --confcutdir=/tmp tests/test_swt_network_e2e.py -q
不使用旧 conftest 的全机卷清理. 所有容器/进程/链路仅按本夹具创建的 ID 清理.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "workflow/use-sandbox-worktree/scripts"
sys.path.insert(0, str(SCRIPTS))
import network_update as net
import swt

pytestmark = pytest.mark.e2e
IMAGE = "localhost/swt-m03:latest"


def command(argv, input=None, timeout=30):
    result = subprocess.run(argv, input=input, capture_output=True, text=True, timeout=timeout)
    assert result.returncode == 0, (argv, result.returncode, result.stderr)
    return result.stdout


def wait_file(path, process):
    end = time.monotonic() + 10
    while not path.exists():
        assert process.poll() is None, "夹具进程提前退出"
        assert time.monotonic() < end, f"夹具文件超时: {path}"
        time.sleep(0.05)


class Sandbox:
    def __init__(self, root, repo=None):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.records = root / "records"
        self.repo = repo or root / "repo"
        self.branch = "feat/" + uuid.uuid4().hex[:8]
        self.name = "swt-network-test-" + uuid.uuid4().hex[:12]
        self.mother = root / "mother"
        self.processes = []
        self.daemon = None
        self.bridge = None
        self.id = None

    def up(self):
        command(["podman", "image", "exists", IMAGE])
        if not self.repo.exists():
            command(["git", "init", "-b", "main", str(self.repo)])
            command(["git", "-C", str(self.repo), "config", "user.name", "fixture"])
            command(["git", "-C", str(self.repo), "config", "user.email", "fixture@example.invalid"])
            (self.repo / "README.md").write_text("isolated fixture\n")
            command(["git", "-C", str(self.repo), "add", "README.md"])
            command(["git", "-C", str(self.repo), "commit", "-m", "fixture"])
        command(["git", "-C", str(self.repo), "worktree", "add", "-b", self.branch, str(self.mother)])
        swt.configure_repo(self.repo, self.mother, self.branch)
        swt.place_daemon_export_ok(self.mother)
        self.daemon = swt.start_daemon(self.mother)
        self.identity = swt.pair_identity(self.repo, self.mother)
        self.bridge = swt.start_git_bridge(self.records, self.identity, self.daemon.port)
        bridge_dir = swt.git_bridge_dir(self.records, self.identity)
        self.id = command(["podman", "run", "-d", "--name", self.name, "--network", "pasta",
                           "--label", f"sandbox-worktree.repo={self.repo}",
                           "--label", f"sandbox-worktree.mother={self.branch}",
                           "-p", "127.0.0.1::22", "-v", f"{bridge_dir}:/run/swt-git", IMAGE]).strip()
        key = self.root / "fixture-key"
        command(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)])
        command(["podman", "exec", "-i", self.id, "sh", "-c",
                 "install -d -m 700 -o bolo -g bolo /home/bolo/.ssh; "
                 "cat >/home/bolo/.ssh/authorized_keys; chown bolo:bolo /home/bolo/.ssh/authorized_keys; "
                 "chmod 600 /home/bolo/.ssh/authorized_keys; echo 'bolo:fixture-only' | chpasswd"],
                input=key.with_suffix(".pub").read_text())
        detail = json.loads(command(["podman", "inspect", self.id]))[0]
        self.ip = swt.container_ip(detail)
        self.netns = swt.container_netns(detail)
        self.port = int(command(["podman", "port", self.id, "22/tcp"]).strip().rsplit(":", 1)[1])
        self.record = {"name": self.name, "podman-id": self.id, "network-ip": self.ip, "state": "running",
                       "branch": self.branch, "clone_dir": "/home/bolo/fixture", "retired": False, "ssh-port": self.port, "ssh_private_key": str(key),
                       "remote": swt.fixed_git_remote(self.mother), "display": "absent", "host-display": "absent"}
        self.path = self.records / "runtime" / f"{self.identity}.json"
        runtime = {"schema": 2, "repo": str(self.repo), "mother": {"branch": self.branch, "dir": str(self.mother)},
                   "mother_branch": self.branch, "mother_dir": str(self.mother), "stage": "born",
                   "config": {"swt-form": True}, "containers": [self.record],
                   "daemon": {"pid": self.daemon.process.pid, "addr": self.daemon.address,
                              "port": self.daemon.port, "base-path": str(self.daemon.base_path), "bridge": self.bridge},
                   "network": {"mode": "whitelist", "allow": ["203.0.113.10/32"], "deny": [],
                               "allow-reasons": {"203.0.113.10/32": "独立验收旧条目"}}}
        net.FileStore().write(self.path, runtime)
        self.request = net.Request("update", self.repo, self.records, self.name,
                                   add=[("198.51.100.20", "独立验收新增条目")])
        self.host = swt.NetworkHost(self.request)
        target = self.host.locate(self.request)
        network = net.policy_for_context(runtime["network"], target.context)
        network["netns"] = self.netns
        runtime["network"] = network
        net.FileStore().write(self.path, runtime)
        swt.apply_network(swt.NetworkPlan("whitelist", tuple(network["allow"]), (), target.context["gateway"],
                                         self.ip, self.netns, target.context["route-gateway"], self.name),
                          dns_servers=target.context["dns"], allow_reasons=network["allow-reasons"])
        swt.ensure_container_git_forward(self.name)
        command([*swt.container_ssh_base(key, self.port), "git clone -b " + self.branch + " " + self.record["remote"] + " ~/fixture"])

    def network_cli(self, action="update", flags=None):
        proc = subprocess.run(["uv", "run", "python", str(SCRIPTS / "swt.py"), "network", action,
                               "--repo", str(self.repo), "--records-root", str(self.records), "--name", self.name,
                               *(flags or [])], capture_output=True, text=True, timeout=90)
        lines = proc.stdout.splitlines()
        assert lines and lines[-1].startswith("NETWORK "), (proc.stdout, proc.stderr)
        return proc.returncode, json.loads(lines[-1].removeprefix("NETWORK "))

    def nft(self, *args):
        return command(["podman", "unshare", "nsenter", f"--net={self.netns}", "nft", *args])

    def down(self):
        for process in self.processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=3)
        if self.id:
            command(["podman", "rm", "-f", "-v", self.id])
        runtime = swt.load_runtime_tolerant(getattr(self, "path", self.root / "absent"))
        # resume 可能替换了 daemon/桥, 同样只清本夹具自己的记录.
        if runtime:
            swt.stop_git_bridge(runtime, self.records, self.identity)
            daemon = runtime.get("daemon") or {}
            if isinstance(daemon.get("pid"), int):
                try:
                    os.kill(daemon["pid"], signal.SIGTERM)
                except ProcessLookupError:
                    pass
        if self.daemon:
            if self.daemon.process.poll() is None:
                self.daemon.process.terminate()
            self.daemon.process.wait(timeout=5)
        if self.bridge:
            try:
                os.kill(self.bridge["pid"], signal.SIGTERM)
            except ProcessLookupError:
                pass


@pytest.fixture
def sandbox(tmp_path):
    fixture = Sandbox(Path(tempfile.mkdtemp(prefix="swt-net-test-")))
    try:
        fixture.up()
        yield fixture
    finally:
        fixture.down()
        shutil.rmtree(fixture.root, ignore_errors=True)


def test_birth_persists_required_reason_using_only_fixture_skills(monkeypatch):
    # 不用 SwtBirthFixture.tearDown 的缺省 clear; 基类仅清自己创建的容器/进程.
    sys.path.insert(0, str(ROOT / "tests"))
    from test_swt_m12 import SwtFixture
    fixture = SwtFixture(methodName="runTest")
    fixture.setUp()
    try:
        skills = fixture.root / "fixture-skills"
        shutil.copytree(SCRIPTS.parent, skills / "use-sandbox-worktree", ignore=shutil.ignore_patterns("__pycache__"))
        monkeypatch.setattr(swt, "SKILLS_HOST_DIR", skills)
        monkeypatch.setattr(swt, "LLM_SELECT_HOST_DIR", fixture.root / "no-llm-select")
        monkeypatch.setattr(swt, "MAVEN_SETTINGS_HOST", fixture.root / "no-maven-settings")
        name = "swt-network-birth-" + uuid.uuid4().hex[:10]
        fixture.container_names.append(name)
        candidates = [IMAGE, *command(["podman", "images", "--format", "{{.Repository}}:{{.Tag}}",
                                       "--filter", "reference=localhost/sandbox-worktree/base:*", "--sort", "created"]).splitlines()]
        image = next((ref for ref in candidates if json.loads(command(["podman", "image", "inspect", ref]))[0]
                      .get("Labels", {}).get("run.sandbox-worktree.agent-template-contract") == "2"), None)
        assert image, "需要已存在且兼容契约 2 的本地测试镜像, 不自动构建/拉取"
        args = swt.parse_args(["birth", "--branch", "feat/network-birth", "--name", name,
                               "--records-root", str(fixture.records), "--image", image,
                               "--agent-template", fixture.AGENT_TEMPLATE_NAME, "--mode", "whitelist",
                               "--allow-entry", "203.0.113.10", "下载构建依赖",
                               "--hostname", "fixture-network", "--lan-ip", "192.0.2.1"])
        assert swt.birth(args, fixture.repo) == 0
        paths = list((fixture.records / "runtime").glob("*.json"))
        assert len(paths) == 1
        saved = net.FileStore().read(paths[0])
        assert saved["network"]["allow"] == ["203.0.113.10/32"]
        assert saved["network"]["allow-reasons"] == {"203.0.113.10/32": "下载构建依赖"}
        request = net.Request("show", fixture.repo, fixture.records, name)
        code, result = net.Maintenance(swt.NetworkHost(request)).execute(request)
        assert code == 0 and result["checks"]["rules"]["status"] == "通过", result
        assert result["diff"]["entries"][0]["reason"] == "下载构建依赖"
        assert all(e["reason"] for e in result["diff"]["automatic"])
    finally:
        fixture.tearDown()


def test_cli_real_rules_ssh_git_and_other_container(sandbox, tmp_path):
    other = Sandbox(sandbox.root / "b", repo=sandbox.repo)
    try:
        other.up()
        other_before = other.path.read_bytes()
        other_rules = other.nft("-j", "list", "table", "inet", "swt")
        code, shown = sandbox.network_cli("show")
        assert code == 0 and shown["checks"]["rules"]["status"] == "通过", json.dumps(shown, ensure_ascii=False)
        before = sandbox.path.read_bytes()
        flags = ["--add", "198.51.100.20", "独立验收新增条目"]
        code, preview = sandbox.network_cli(flags=flags)
        assert code == 1, preview
        assert before == sandbox.path.read_bytes()
        code, updated = sandbox.network_cli(flags=[*flags, "--confirm", preview["decision-id"]])
        assert code == 0, updated
        assert all(c["status"] == "通过" for c in updated["checks"].values()), updated
        for chain in ("input", "forward", "output"):
            assert "198.51.100.20/32" in " ".join(updated["policy"]["allow"])
        assert other.path.read_bytes() == other_before
        assert other.nft("-j", "list", "table", "inet", "swt") == other_rules
        assert json.loads(command(["podman", "inspect", other.id]))[0]["State"]["Status"] == "running"
    finally:
        other.down()


def test_shared_netns_concurrent_merge_and_stale_guard(sandbox):
    # 只在夹具自有 namespace 内模拟另外两个源地址, 不使用共享 rootless 桥表.
    procs = []
    for address in ("10.77.0.3", "10.77.0.4"):
        procs.append(subprocess.Popen(["uv", "run", "python", str(SCRIPTS / "net-firewall.py"), "apply",
                                       "--mode", "whitelist", "--container-ip", address, "--gateway", "10.77.0.1",
                                       "--allow", "203.0.113.30", "--merge", "--netns", sandbox.netns],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
    for proc in procs:
        out, err = proc.communicate(timeout=40)
        assert proc.returncode == 0, (out, err)
    table = sandbox.nft("list", "table", "inet", "swt")
    assert all(f"ip saddr {a}" in table for a in (sandbox.ip, "10.77.0.3", "10.77.0.4"))
    flags = ["--add", "198.51.100.20", "独立验收新增条目"]
    code, preview = sandbox.network_cli(flags=flags)
    assert code == 1, preview
    # 异己规则变化不使目标票据失效, 也不会被目标更新覆盖.
    command(["uv", "run", "python", str(SCRIPTS / "net-firewall.py"), "apply", "--mode", "whitelist",
             "--container-ip", "10.77.0.4", "--gateway", "10.77.0.1", "--allow", "203.0.113.40",
             "--merge", "--netns", sandbox.netns])
    code, updated = sandbox.network_cli(flags=[*flags, "--confirm", preview["decision-id"]])
    assert code == 0, updated
    table = sandbox.nft("list", "table", "inet", "swt")
    assert "ip saddr 10.77.0.4 ip daddr 203.0.113.40 accept" in table
    # 目标未知规则不能被重新审批/merge 收编或清掉.
    sandbox.nft("insert", "rule", "inet", "swt", "output", "ip", "saddr", sandbox.ip, "ip", "daddr", "198.51.100.99", "accept")
    before = sandbox.path.read_bytes()
    code, result = sandbox.network_cli(flags=["--add", "198.51.100.21", "未知现场不修改"])
    assert code == 2, result
    assert sandbox.path.read_bytes() == before
    assert "198.51.100.99" in sandbox.nft("list", "table", "inet", "swt")


def test_real_resume_replays_updated_allow_and_reasons(sandbox, monkeypatch):
    flags = ["--add", "198.51.100.20", "独立验收新增条目"]
    code, preview = sandbox.network_cli(flags=flags)
    assert code == 1, preview
    assert sandbox.network_cli(flags=[*flags, "--confirm", preview["decision-id"]])[0] == 0
    command(["podman", "stop", "-t", "1", sandbox.id])
    # 本夹具是无模型凭据的旧形态记录. 不调用真实 auth.json 注入, 不碰宿主显示.
    monkeypatch.setattr(swt, "inject_auth_json", lambda name: None)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-absent")
    args = swt.parse_args(["resume", "--repo", str(sandbox.repo), "--records-root", str(sandbox.records), "--name", sandbox.name])
    assert swt.resume(args, sandbox.repo) == 1
    args.confirm = True
    assert swt.resume(args, sandbox.repo) == 0
    saved = net.FileStore().read(sandbox.path)
    assert saved["network"]["allow-reasons"]["198.51.100.20/32"] == "独立验收新增条目"
    assert sandbox.path.stat().st_mode & 0o777 == 0o600
    sandbox.netns = saved["network"]["netns"]
    for chain in ("forward", "input", "output"):
        assert "198.51.100.20" in sandbox.nft("list", "chain", "inet", "swt", chain)


def test_real_rollback_keeps_foreign_update(sandbox):
    original = sandbox.path.read_bytes()
    class FailingCheckHost(swt.NetworkHost):
        failed = False
        def checks(self, target):
            if not self.failed:
                self.failed = True
                command(["uv", "run", "python", str(SCRIPTS / "net-firewall.py"), "apply", "--mode", "whitelist",
                         "--container-ip", "10.77.0.4", "--gateway", "10.77.0.1", "--allow", "203.0.113.40",
                         "--merge", "--netns", sandbox.netns])
                yield "ssh", {"status": "失败", "detail": "独立检查接缝故障注入"}
            else:
                yield from super().checks(target)
    service = net.Maintenance(FailingCheckHost(sandbox.request))
    code, preview = service.execute(sandbox.request)
    assert code == 1
    sandbox.request.confirm = preview["decision-id"]
    code, result = service.execute(sandbox.request)
    assert (code, result["stage"]) == (3, "rolled-back"), result
    assert sandbox.path.read_bytes() == original
    table = sandbox.nft("list", "table", "inet", "swt")
    assert "ip saddr 10.77.0.4 ip daddr 203.0.113.40 accept" in table
    assert "198.51.100.20" not in table and "203.0.113.10" in table


@pytest.mark.parametrize("stopped", [False, True])
def test_real_interruption_and_recover_original_identity(sandbox, stopped):
    class InterruptHost(swt.NetworkHost):
        def apply(self, *args):
            super().apply(*args)
            raise KeyboardInterrupt()
    service = net.Maintenance(InterruptHost(sandbox.request))
    code, preview = service.execute(sandbox.request)
    assert code == 1
    sandbox.request.confirm = preview["decision-id"]
    with pytest.raises(KeyboardInterrupt):
        service.execute(sandbox.request)
    assert net.FileStore().read(sandbox.path)["network-change"]["phase"] == "prepared"
    if stopped:
        command(["podman", "stop", "-t", "1", sandbox.id])
    code, preview = sandbox.network_cli("recover")
    assert code == 1, preview
    code, result = sandbox.network_cli("recover", ["--confirm", preview["decision-id"]])
    assert (code, result["stage"]) == (0, "recovered"), result
    assert "network-change" not in net.FileStore().read(sandbox.path)
    status = json.loads(command(["podman", "inspect", sandbox.id]))[0]["State"]["Status"]
    assert status == ("exited" if stopped else "running")


def test_explicit_terminate_archives_only_original_target_transaction(sandbox):
    class InterruptHost(swt.NetworkHost):
        def apply(self, *args):
            super().apply(*args)
            raise KeyboardInterrupt()
    service = net.Maintenance(InterruptHost(sandbox.request))
    code, preview = service.execute(sandbox.request)
    assert code == 1
    sandbox.request.confirm = preview["decision-id"]
    with pytest.raises(KeyboardInterrupt):
        service.execute(sandbox.request)
    args = swt.parse_args(["terminate", "--repo", str(sandbox.repo), "--records-root", str(sandbox.records),
                           "--name", sandbox.name, "--force"])
    # daemon 是本测试进程的直接子进程, 及时 wait, 不把夹具僵尸误判为未结束.
    reaper = threading.Thread(target=sandbox.daemon.process.wait, daemon=True)
    reaper.start()
    try:
        assert swt.terminate(args, sandbox.repo) == 0
    finally:
        reaper.join(timeout=5)
    saved = net.FileStore().read(sandbox.path)
    assert saved["stage"] == "idle" and "network-change" not in saved
    audit = list((sandbox.records / "runtime" / sandbox.identity).glob("audit*"))
    assert audit and any("network-change-terminated" in p.read_text() for p in audit if p.is_file())
    assert all(p.stat().st_mode & 0o777 == 0o600 for p in audit if p.is_file())
    sandbox.id = None  # 已经显式终结, teardown 不再 rm.


def test_real_dns_flow_after_approved_auto_sync(sandbox):
    """私有 DNS namespace 经 veth 连目标, 指定 src 确保命中真实过滤链."""
    holder_pid = sandbox.root / "dns-holder.pid"
    holder = subprocess.Popen(["podman", "unshare", "unshare", "--net", "sh", "-c",
                               f"echo $$ > {holder_pid}; exec sleep infinity"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    sandbox.processes.append(holder)
    wait_file(holder_pid, holder)
    pid = int(holder_pid.read_text())
    target_prefix = ["podman", "unshare", "nsenter", f"--net={sandbox.netns}"]
    dns_prefix = ["podman", "unshare", "nsenter", f"--net=/proc/{pid}/ns/net"]
    command([*target_prefix, "ip", "link", "add", "swt-dns-a", "type", "veth", "peer", "name", "swt-dns-b"])
    command([*target_prefix, "ip", "link", "set", "swt-dns-b", "netns", str(pid)])
    command([*target_prefix, "ip", "link", "set", "swt-dns-a", "up"])
    command([*dns_prefix, "ip", "link", "set", "lo", "up"])
    command([*dns_prefix, "ip", "addr", "add", "198.51.100.53/32", "dev", "swt-dns-b"])
    command([*dns_prefix, "ip", "link", "set", "swt-dns-b", "up"])
    command([*target_prefix, "ip", "route", "add", "198.51.100.53/32", "dev", "swt-dns-a", "src", sandbox.ip])
    command([*dns_prefix, "ip", "route", "add", sandbox.ip + "/32", "dev", "swt-dns-b"])
    script = sandbox.root / "dns.py"
    ready = sandbox.root / "dns.ready"
    script.write_text('''import socket,struct,threading
from pathlib import Path

def answer(q):
    return q[:2]+b"\\x81\\x80"+q[4:6]+b"\\x00\\x01\\x00\\x00\\x00\\x00"+q[12:]+b"\\xc0\\x0c\\x00\\x01\\x00\\x01\\x00\\x00\\x00\\x1e\\x00\\x04\\xc6\\x33\\x64\\x14"
def udp():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.bind(("198.51.100.53",53))
    while True:
        q,addr=s.recvfrom(512); s.sendto(answer(q),addr)
def tcp():
    s=socket.socket(); s.bind(("198.51.100.53",53)); s.listen()
    while True:
        c,_=s.accept()
        with c:
            n=struct.unpack("!H",c.recv(2))[0]; q=c.recv(n); a=answer(q); c.sendall(struct.pack("!H",len(a))+a)
threading.Thread(target=udp,daemon=True).start()
threading.Thread(target=tcp,daemon=True).start()
Path(''' + repr(str(ready)) + ''').touch()
threading.Event().wait()
''')
    server = subprocess.Popen([*dns_prefix, "uv", "run", "--no-project", "--offline", "python", str(script)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    sandbox.processes.append(server)
    wait_file(ready, server)
    command(["podman", "exec", sandbox.id, "sh", "-c", "printf 'nameserver 198.51.100.53\\n' > /etc/resolv.conf"])
    code, preview = sandbox.network_cli()  # 无用户变更, 只审批真实解析器自动项.
    assert code == 1, preview
    code, updated = sandbox.network_cli(flags=["--confirm", preview["decision-id"]])
    assert code == 0, updated
    probe = '''import socket,struct
q=b"\\x12\\x34\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x0adependency\\x04test\\x00\\x00\\x01\\x00\\x01"
for kind in (socket.SOCK_DGRAM,socket.SOCK_STREAM):
    with socket.socket(socket.AF_INET,kind) as s:
        s.settimeout(3); s.connect(("198.51.100.53",53))
        if kind==socket.SOCK_DGRAM: s.send(q); a=s.recv(512)
        else: s.sendall(struct.pack("!H",len(q))+q); n=struct.unpack("!H",s.recv(2))[0]; a=s.recv(n)
        assert a[-4:]==socket.inet_aton("198.51.100.20"),a
print("udp/tcp DNS fixture passed")
'''
    assert "passed" in command(["podman", "exec", "-i", sandbox.id, "python3", "-"], input=probe)
