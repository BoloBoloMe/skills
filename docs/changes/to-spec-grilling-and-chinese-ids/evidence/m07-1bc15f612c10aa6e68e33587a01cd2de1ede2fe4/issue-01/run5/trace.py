"""一次性 Linux x86_64 取证. 只跟踪自己创建的隔离 CLI 子进程, 不改脚本/协作者."""
from probe import *
from target import BASE, DRAFT
import ctypes as C
import json
import signal
import time

LIBC = C.CDLL(None, use_errno=True)
LIBC.ptrace.argtypes = [C.c_uint, C.c_int, C.c_void_p, C.c_void_p]
LIBC.ptrace.restype = C.c_long
SIGNAL = signal.SIGTRAP | 0x80
FIELDS = 'r15 r14 r13 r12 rbp rbx r11 r10 r9 r8 rax rcx rdx rsi rdi orig_rax rip cs eflags rsp ss fs_base gs_base ds es fs gs'

class Regs(C.Structure):
    _fields_ = [(name, C.c_ulonglong) for name in FIELDS.split()]


def ptrace(request, pid, addr=0, data=0):
    C.set_errno(0)
    result = LIBC.ptrace(request, pid, addr, data)
    if result == -1 and C.get_errno():
        raise OSError(C.get_errno(), f'ptrace {request}: {os.strerror(C.get_errno())}')
    return result


def fdpath(pid, fd):
    try:
        return os.readlink(f'/proc/{pid}/fd/{fd}')
    except FileNotFoundError:
        return ''


def cstring(pid, ptr):
    with open(f'/proc/{pid}/mem', 'rb', buffering=0) as f:
        return os.pread(f.fileno(), 4096, ptr).split(b'\0', 1)[0].decode('utf-8')


def run(case, interpreter):
    directory = E / 'files' / 'trace' / case
    base = fixture(f'trace/{case}/PRODUCT.base.md', BASE)
    draft = fixture(f'trace/{case}/acceptance.md', DRAFT)
    previous = fixture(f'trace/{case}/original-output.md', b'old synthetic file\r\n')
    output = fixture(f'trace/{case}/PRODUCT.md', previous.read_bytes())
    paths = {str(p): name for p, name in ((base, 'base'), (draft, 'draft'), (output, 'output'))}
    receipts = E / 'logs'
    prefix = receipts / f'trace-{case}'
    cmd = [interpreter, ROOT / 'workflow/to-spec/ac-draft.py', 'promote', base, draft, output]
    prefix.with_suffix('.cmd').write_text(f'{datetime.now(timezone.utc).isoformat()}\ncd {ROOT}\n{shlex.join(map(str, cmd))}\n')
    observed = prefix.with_suffix('.events.jsonl')
    with observed.open('x', encoding='utf-8') as events:
        def log(event, **data):
            events.write(json.dumps(dict(ns=time.monotonic_ns(), event=event, **data), ensure_ascii=False) + '\n')
            events.flush()
        pid = os.fork()
        if not pid:
            try:
                for fd, ext in ((1, '.stdout'), (2, '.stderr')):
                    raw = os.open(prefix.with_suffix(ext), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    os.dup2(raw, fd)
                    os.close(raw)
                ptrace(0, 0)  # PTRACE_TRACEME
                os.kill(os.getpid(), signal.SIGSTOP)
                os.execv(interpreter, list(map(str, cmd)))
            except BaseException as e:
                os.write(2, (str(e) + '\n').encode())
                os._exit(125)
        reaped = False
        try:
            _, status = os.waitpid(pid, 0)
            if not os.WIFSTOPPED(status):
                reaped = True
                raise RuntimeError(f'不能启动跟踪: {status}')
            ptrace(0x4200, pid, data=1 | 0x10 | 0x100000)  # TRACESYSGOOD, TRACEEXEC, EXITKILL
            log('start', pid=pid, controller=os.getpid())
            entering = True
            changed = None
            seen_reads = set()
            replaced = []
            while True:
                ptrace(24, pid)  # PTRACE_SYSCALL
                _, status = os.waitpid(pid, 0)
                if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                    reaped = True
                    exit_code = os.waitstatus_to_exitcode(status)
                    log('exit', code=exit_code)
                    break
                if os.WSTOPSIG(status) != SIGNAL:
                    continue
                regs = Regs()
                ptrace(12, pid, data=C.cast(C.byref(regs), C.c_void_p))
                n = regs.orig_rax
                if entering:
                    path = fdpath(pid, regs.rdi) if n in (0, 3, 74) else ''
                result = C.c_longlong(regs.rax).value
                pause = False
                if n == 0 and not entering and path in paths and result > 0:
                    log('read-return', file=paths[path], path=path, bytes=result)
                    seen_reads.add(paths[path])
                if n == 3 and not entering and path in paths and result == 0:
                    log('close-return', file=paths[path], path=path)
                    pause = case == paths[path] and case in seen_reads
                if n == 74 and entering and path.startswith(str(directory / '.PRODUCT.md-')):
                    log('fsync-temp-entry', path=path, reads_before_stop=sorted(seen_reads))
                    pause = case == 'output' and all(key in seen_reads for key in ('base', 'draft', 'output'))
                if n in (82, 264, 316):
                    if entering:
                        src, dst = (regs.rdi, regs.rsi) if n == 82 else (regs.rsi, regs.r10)
                        rename = [cstring(pid, src), cstring(pid, dst)]
                        if rename[1] == str(output):
                            log('rename-entry', src=rename[0], dst=rename[1], syscall=n)
                    elif rename[1] == str(output):
                        log('rename-return', result=result)
                        if result == 0:
                            replaced.append(rename)
                if pause and changed is None:
                    dest = {'base': base, 'draft': draft, 'output': output}[case]
                    old = dest.read_bytes()
                    new = {'base': BASE.replace('查阅清单', '浏览清单').encode(),
                           'draft': DRAFT.replace('合成记录', '示例记录').encode(),
                           'output': b'concurrent writer content\n'}[case]
                    assert new != old
                    fixture(f'trace/{case}/input-before.bin', old)
                    fixture(f'trace/{case}/external-intended.bin', new)
                    log('cli-paused', at='close-return' if case != 'output' else 'fsync-temp-entry',
                        file=str(dest), pid=pid)
                    data = subprocess.check_output(['cp', '--', directory / 'external-intended.bin', dest])
                    assert data == b'' and dest.read_bytes() == new
                    changed = new
                    log('external-cp-exited', argv=['cp', '--', str(directory / 'external-intended.bin'), str(dest)],
                        code=0, bytes=len(new))
                    fixture(f'trace/{case}/external-after.bin', dest.read_bytes())
                    log('cli-about-to-resume', pid=pid)
                entering = not entering
        finally:
            if not reaped:
                try:
                    os.kill(pid, signal.SIGKILL)
                    os.waitpid(pid, 0)
                except ProcessLookupError:
                    pass
    prefix.with_suffix('.exit').write_text(f'{exit_code}\n')
    if case == 'atomic':
        expected = BASE.replace('## 验收标准\n\n', '## 验收标准\n\n' + MARKER + '\n' + DRAFT + '\n').encode()
        assert exit_code == 0 and output.read_bytes() == expected, (exit_code, output)
        assert len(replaced) == 1 and json.loads(prefix.with_suffix('.stdout').read_bytes()) == {
            'success': True, 'command': 'promote', 'output': str(output)}
        r = record('trace-atomic-formal-check', cli(ROOT, 'check-ac', output))
        assert r.returncode == 0
        assert base.read_bytes() == BASE.encode() and draft.read_bytes() == DRAFT.encode()
    else:
        assert changed is not None and exit_code == 2 and not replaced, (changed, exit_code, replaced)
        error = json.loads(prefix.with_suffix('.stdout').read_bytes())
        assert not error['success'] and ('正式文件在' if case == 'output' else '输入在') in error['error']
        assert output.read_bytes() == (changed if case == 'output' else previous.read_bytes())
    assert not list(directory.glob('.PRODUCT.md-*.tmp'))
    print(f'{case}: exit={exit_code}, rename={len(replaced)}, final CONTENT matches')

if __name__ == '__main__':
    interpreter = sys.executable
    for case in ('atomic', 'base', 'draft', 'output'):
        run(case, interpreter)
