#!/usr/bin/env python3
"""Fast protocol consistency and schema parity checks for v2.24.0."""
import argparse, sys, os, re
from pathlib import Path
EXCLUDE = {'__pycache__'}

def read_md(root):
    texts=[]
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE and d != '__pycache__']
        for fn in filenames:
            if fn.endswith('.md'):
                p=Path(dirpath)/fn
                try: texts.append(p.read_text(encoding='utf-8', errors='ignore'))
                except Exception: pass
    return '\n'.join(texts)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('skill_root'); args=ap.parse_args()
    root=Path(args.skill_root).resolve(); text=read_md(root); errors=[]
    name=root.name

    for forbidden in ['lega' + 'cy-v1-compat', 'lega' + 'cy-v1-full', 'lega' + 'cy_fallback', '90-' + 'removed-crosswalk', '07-' + 'removed-crosswalk']:
        if forbidden in text:
            errors.append(f'removed pilot-asset token remains: {forbidden}')

    compat = root / 'references/shared/compatibility-contract.yaml'
    if not compat.exists():
        errors.append('missing shared compatibility-contract.yaml')
    else:
        ct = compat.read_text(encoding='utf-8', errors='ignore')
        for token in ['schema_version: "2.24.0"', 'hilp_version: "2.24.0"', 'hile_version: "2.24.1"', 'producer_skill: human-in-loop-planning', 'consumer_skill: human-in-loop-execution']:
            if token not in ct:
                errors.append(f'compatibility contract missing {token}')

    if name == 'human-in-loop-planning':
        for token in ['blocked','reapproval-record','preflight-scaffold']:
            if token not in text: errors.append(f'missing HILP enum token: {token}')
        forbidden=[
            'lifecycle_state: draft|ready-for-review|approved|superseded|retired|closed-record',
            'record_role: working-asset|approval-record|handoff-record|archive-index|historical-evidence'
        ]
        for f in forbidden:
            if f in text: errors.append('old HILP enum remains: '+f)
    elif name == 'human-in-loop-execution':
        # HILE canonical text should include partial intake but must not describe retired as a valid HILE lifecycle value.
        if 'partial' not in text: errors.append('HILE canonical docs must include partial intake_status')
        retired_bad = re.search(r'\bretired\b', text)
        if retired_bad:
            errors.append('HILE canonical docs must not mention retired')
    else:
        errors.append(f'unknown skill root name: {name}')
    if errors:
        print('PROTOCOL_CONSISTENCY_ERRORS'); print('\n'.join(errors)); sys.exit(1)
    print('protocol consistency ok')
if __name__ == '__main__': main()
