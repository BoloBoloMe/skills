from probe import *
import json
from html.parser import HTMLParser

BASE = '''# 合成清单 Product Spec

## 背景

合成输入, 不代表用户确认.

## 目标

- 目标1: 读者能查阅清单.

## 非目标

- 非目标1: 不写真实数据.

## 业务规则

''' + ''.join(f'- 规则{i}: 合成规则 {i}.' + (' (审计)' if i == 9 else '') + '\n' for i in range(1, 10)) + '''
## 验收标准

## 决策引用

- 无.
'''
DRAFT = '''```gherkin
# language: zh-CN
功能: 合成清单

背景:
假定 读者已打开清单

@AC-001 @normal @G-001 @BR-002
场景大纲: 查看 <条数> 条合成记录
假定 清单有 <条数> 条合成记录
当 读者查看清单
那么 读者看到 <条数> 条合成记录

例子:
| 条数 |
| 1 |
| 2 |
```
'''

AC_CASES = {
    'missing-goal': (BASE, DRAFT.replace('@G-001', '@G-099'), 1, '不存在'),
    'audit-rule': (BASE, DRAFT.replace('@BR-002', '@BR-009'), 1, '指向 (审计) 条目'),
    'duplicate-goal': (BASE.replace('## 非目标', '- 目标1: 重复编号.\n\n## 非目标'), DRAFT, 2, '目标1 重复'),
    'keyword': (BASE, DRAFT.replace('假定 读者', '假如 读者'), 1, '关键字白名单'),
    'multiple-ac': (BASE, DRAFT.replace('@AC-001', '@AC-001 @AC-002'), 1, '@AC 标签数为 2'),
    'free-tag': (BASE, DRAFT.replace('@normal', '@normal @smoke'), 1, '非法标签 @smoke'),
    'marker': (BASE, MARKER + '\n' + DRAFT, 2, '草稿不携带确认标记'),
}

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.articles = []
        self.controls = []
        self.links = []
        self.raw = ''
        self.in_raw = False
        self.body_text = []
        self.in_body = False

    def handle_starttag(self, tag, values):
        attr = dict(values)
        if tag == 'article' and attr.get('class') == 'acceptance-card':
            self.articles.append(attr)
        if tag in ('form', 'input', 'button') or any(key.startswith('on') for key in attr):
            self.controls.append((tag, attr))
        if tag == 'a':
            self.links.append(attr['href'])
        if tag == 'pre' and attr.get('id') == 'draft-content':
            self.in_raw = True
        if tag == 'body':
            self.in_body = True

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.in_raw = False
        if tag == 'body':
            self.in_body = False

    def handle_data(self, data):
        if self.in_raw:
            self.raw += data
        if self.in_body:
            self.body_text.append(data)


def main():
    for script, sub in ([] if resume else [('ac-draft', 'workspace'), ('ac-draft', 'preview'), ('ac-draft', 'promote'), ('check-ac', '')]):
        r = record(f'target-help-{sub or script}', cli(ROOT, script, *([sub] if sub else []), '--help'))
        assert r.returncode == 0 and b'--review' not in r.stdout
    if not resume:
        r = record('target-workspace', cli(ROOT, 'ac-draft', 'workspace'))
        data = json.loads(r.stdout)
        assert r.returncode == 0 and data['success'] and Path(data['review']).is_dir()
        assert Path(data['review']).parent == Path(data['dir']) and E in Path(data['dir']).parents
    data = {}
    for case, (b, d, code, msg) in {'valid': (BASE, DRAFT, 0, '1 个场景, 1 个 AC'), **AC_CASES}.items():
        base = E / f'files/ac/{case}/PRODUCT.base.md'
        draft = E / f'files/ac/{case}/review/acceptance.md'
        if resume and draft.exists():
            assert base.read_bytes() == b.encode() and draft.read_bytes() == d.encode()
            name = 'target-ac-' + case
            r = subprocess.CompletedProcess([], int((E / f'logs/{name}.exit').read_text()),
                                            (E / f'logs/{name}.stdout').read_bytes(),
                                            (E / f'logs/{name}.stderr').read_bytes())
        else:
            fixture(f'ac/{case}/PRODUCT.base.md', b)
            fixture(f'ac/{case}/review/acceptance.md', d)
            r = record('target-ac-' + case, cli(ROOT, 'check-ac', base, '--draft', draft))
        assert r.returncode == code and msg.encode() in r.stderr + r.stdout, (case, r)
        print(f'check-ac {case}: {code} / {msg}')
        data[case] = base, draft
    base, draft = data['valid']
    r = record('target-preview', cli(ROOT, 'ac-draft', 'preview', base, draft))
    result = json.loads(r.stdout)
    page_path = Path(result['preview'])
    assert r.returncode == 0 and result['success'] and result['draft'] == str(draft)
    assert page_path.is_file() and page_path.parent == draft.parent and 'review_id' not in result
    page = Page()
    page.feed(page_path.read_text(encoding='utf-8'))
    assert len(page.articles) == 2 and page.raw == DRAFT and not page.controls
    assert draft.name in page.links and all(link.startswith('#') or link == draft.name for link in page.links)
    assert '页面仅供选看, 不用于确认.' in page.body_text
    assert '请在 chat 中确认' not in ''.join(page.body_text)
    assert base.read_bytes() == BASE.encode() and draft.read_bytes() == DRAFT.encode()
    fixture('ac/valid/page-nodes.json', json.dumps(dict(articles=page.articles, raw=page.raw,
                                                        controls=page.controls, links=page.links,
                                                        rendered_body_text=page.body_text), ensure_ascii=False, indent=2))
    print('preview: 0 / 2 张展开卡片, 节点原文和草稿一致, 原文件链接, 无确认控件, 两输入未变')
    for case in ('removed-option', 'bad-input'):
        before = fixture(f'promote/{case}/before.md', '原有正式文件, 只作保护对象.\n')
        output = fixture(f'promote/{case}/PRODUCT.md', before.read_bytes())
        b, d = data['valid' if case == 'removed-option' else 'missing-goal']
        args = ['--review', 'unused'] if case == 'removed-option' else []
        r = record('target-promote-' + case, cli(ROOT, 'ac-draft', 'promote', b, d, output, *args))
        if args:
            assert r.returncode == 2 and b'unrecognized arguments: --review' in r.stderr
        else:
            assert r.returncode == 1 and b'@G-099' in r.stdout and not json.loads(r.stdout)['success']
        assert output.read_bytes() == before.read_bytes()
        print(f'promote {case}: {r.returncode} / 原正式稿未变')
    for line in tech_check('target', ROOT):
        print('check-tech 基线和候选一致: ' + line)
    draft = E / 'files/tech/conditional.md'
    output = draft.with_name('TECHNICAL.md')
    for label, cmd in [('copy', ['cp', '--', draft, output]), ('compare', ['cmp', '--', draft, output]),
                       ('formal', cli(ROOT, 'check-tech', output))]:
        assert record('target-tech-' + label, cmd).returncode == 0
    print('技术草稿通过后 cp/cmp/正式机检: 均 0')


if __name__ == '__main__':
    resume = '--continue' in sys.argv
    main()
