#!/usr/bin/env python3
"""Fast protocol consistency and schema parity checks for v2.24.1."""
import argparse, sys, os, re
from pathlib import Path
EXCLUDE = {'__pycache__'}

STANDARD_NO_CONFIRM_ROUTE = 'tier_standard' + '_and_confirmation_not_required'
STANDARD_NO_CONFIRM_ERROR = 'standard execution must not define a no-confirmation route; only tiny may skip separate confirmation under tiny exception rules'


def read_md_files(root):
    files=[]
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE and d != '__pycache__']
        for fn in filenames:
            if fn.endswith('.md'):
                p=Path(dirpath)/fn
                try:
                    files.append((p, p.read_text(encoding='utf-8', errors='ignore')))
                except Exception:
                    pass
    return files


def read_md(root):
    return '\n'.join(text for _, text in read_md_files(root))


def context_has_standard_no_confirmation(text):
    for m in re.finditer('no' + '_confirmation_required', text):
        start = max(0, m.start() - 600)
        end = min(len(text), m.end() + 600)
        ctx = text[start:end].lower()
        if 'standard_confirmation' in ctx or 'standard execution' in ctx or 'tier_standard' in ctx:
            return True
    return False


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('skill_root'); args=ap.parse_args()
    root=Path(args.skill_root).resolve(); md_files=read_md_files(root); text='\n'.join(t for _, t in md_files); errors=[]
    name=root.name

    for forbidden in ['lega' + 'cy-v1-compat', 'lega' + 'cy-v1-full', 'lega' + 'cy_fallback', '90-' + 'removed-crosswalk', '07-' + 'removed-crosswalk']:
        if forbidden in text:
            errors.append(f'removed pilot-asset token remains: {forbidden}')

    compat = root / 'references/shared/compatibility-contract.yaml'
    if not compat.exists():
        errors.append('missing shared compatibility-contract.yaml')
    else:
        ct = compat.read_text(encoding='utf-8', errors='ignore')
        for token in ['schema_version: "2.24.1"', 'hilp_version: "2.24.0"', 'hile_version: "2.24.1"', 'producer_skill: human-in-loop-planning', 'consumer_skill: human-in-loop-execution']:
            if token not in ct:
                errors.append(f'compatibility contract missing {token}')

    if name == 'human-in-loop-planning':
        for token in ['blocked','reapproval-record']:
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
        if STANDARD_NO_CONFIRM_ROUTE in text:
            errors.append(STANDARD_NO_CONFIRM_ERROR)
        routing = root / 'references/agent/03-routing.md'
        if not routing.exists():
            errors.append('missing HILE routing projection references/agent/03-routing.md')
        else:
            rt = routing.read_text(encoding='utf-8', errors='ignore')
            if context_has_standard_no_confirmation(rt):
                errors.append(STANDARD_NO_CONFIRM_ERROR)
            if 'execute_plan_with_tdd_and_verification' in rt and (('no' + '_confirmation_required') in rt or STANDARD_NO_CONFIRM_ROUTE in rt):
                errors.append(STANDARD_NO_CONFIRM_ERROR)
            if 'plan_saved_but_not_confirmed' not in rt or 'already_confirmed' not in rt:
                errors.append('standard confirmation routing must expose only waiting and already-confirmed states')
            if 'Routing must not introduce weaker confirmation semantics' not in rt:
                errors.append('routing must declare SKILL.md and execution tiers authoritative for confirmation semantics')
        tiers = root / 'references/agent/02-execution-tiers.md'
        if not tiers.exists():
            errors.append('missing HILE execution tiers references/agent/02-execution-tiers.md')
        else:
            tt = tiers.read_text(encoding='utf-8', errors='ignore')
            if 'confirmation_required: true' not in tt or 'always_before_file_modification' not in tt:
                errors.append('standard tier must retain confirmation_required: true and always_before_file_modification')
        layout = root / 'references/shared/execution-asset-layout.md'
        if layout.exists():
            lt = layout.read_text(encoding='utf-8', errors='ignore')
            for token in ['completion_review: asset_ref|path|null', 'latest_completion_review: asset_ref|path|null']:
                if token not in lt:
                    errors.append(f'execution layout schema missing {token}')
        for script in ['scripts/init_execution_package.py','scripts/validate_execution_manifest.py']:
            sp = root / script
            if sp.exists() and 'completion_review' not in sp.read_text(encoding='utf-8', errors='ignore'):
                errors.append(f'{script} missing completion_review parity')
    else:
        errors.append(f'unknown skill root name: {name}')
    if errors:
        print('PROTOCOL_CONSISTENCY_ERRORS'); print('\n'.join(errors)); sys.exit(1)
    print('protocol consistency ok')
if __name__ == '__main__': main()
