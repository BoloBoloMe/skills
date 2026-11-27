import os, shlex, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
E = Path(__file__).resolve().parent
ROOT = Path.cwd()
BASELINE = Path('/home/bolo/Workspace/improve')
UV = ['uv', 'run']
GH = UV + ['--with', 'gherkin-official', 'python']
PY = UV + ['python']
MARKER = '<!-- confirmed-flow: v1 -->'

def record(name, cmd):
    prefix = E / 'logs' / name
    def save(ext, data):
        prefix.with_suffix(ext).write_bytes(data)
    save('.cmd', (datetime.now(timezone.utc).isoformat() + '\ncd ' + str(ROOT) + '\n' + shlex.join(map(str, cmd)) + '\n').encode())
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    save('.stdout', r.stdout)
    save('.stderr', r.stderr)
    save('.exit', f'{r.returncode}\n'.encode())
    return r

def cli(repo, script, *args):
    return (GH if script != 'check-tech' else PY) + [repo / 'workflow/to-spec' / (script + '.py'), *args]

def fixture(rel, data):
    path = E / 'files' / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(data.encode() if isinstance(data, str) else data)
    return path

SECTIONS = ('模块划分', '模块接口', '接缝与依赖', '安全策略', '非功能要求', '关键流程', '决策引用')
REQUIRED = SECTIONS[:3] + SECTIONS[-1:]
def tech(sections):
    return '# 合成样例 Technical Spec\n\n' + ''.join(f'## {s}\n\n合成内容.\n\n' for s in sections)

def tech_inputs():
    cases = {'required': (REQUIRED, 0, '4 节'), 'conditional': (SECTIONS, 0, '7 节')}
    for i, name in enumerate(REQUIRED, 1):
        cases[f'missing-{i}'] = (tuple(s for s in REQUIRED if s != name), 1, '缺少必备节 `## ' + name + '`')
    for i, name in enumerate(SECTIONS, 1):
        cases[f'typo-{i}'] = (tuple(s + '误' if s == name else s for s in SECTIONS), 1, '非法节名 ' + repr(name + '误'))
    cases['order'] = ((REQUIRED[1], REQUIRED[0], *REQUIRED[2:]), 1, '节顺序与模板不一致')
    return cases

def tech_check(name, repo, make=False):
    results = []
    for case, (sections, code, msg) in tech_inputs().items():
        rel = 'tech/' + case + '.md'
        path = fixture(rel, tech(sections)) if make else E / 'files' / rel
        r = record(name + '-tech-' + case, cli(repo, 'check-tech', path))
        ok = r.returncode == code and msg.encode() in r.stdout + r.stderr
        results.append(f'{case}: {r.returncode}, {msg}, {ok}')
        assert ok, (case, r)
        if not make:
            for ext in ('stdout', 'stderr', 'exit'):
                logs = E / 'logs'
                assert (logs / f'base-tech-{case}.{ext}').read_bytes() == (logs / f'{name}-tech-{case}.{ext}').read_bytes()
    return results

if __name__ == '__main__':
    for line in tech_check('base', BASELINE, make=True):
        print(line)
