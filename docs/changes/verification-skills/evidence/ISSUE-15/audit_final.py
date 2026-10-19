#!/usr/bin/env python3
"""ISSUE-15 最终整合审计清单 (TS-001 到 TS-005).

只读核对, 不修改技能, 标准, 证据或部署副本. 五项检查:
- audit-no-git-actions (TS-001, AC-032): 五个技能与 tdd-as-orchestra 的交付边界, 演练记录里的无自动 Git 动作说明.
- audit-frontmatter (TS-002, BR-009): 六个 SKILL.md 与证据中的项目级配方的 frontmatter 机检.
- audit-scope (TS-003, BR-011): 相对开工基线的最终差异范围, 权威输入字节, 部署副本.
- audit-security-evidence (TS-004, 安全策略): ISSUE-10 与 ISSUE-08 的授权, 清理, 脱敏与冻结目标记录.
- audit-drill-records (TS-005, 测试接缝末段): 每个演练记录区分源文件, 宿主, 临时项目, 且不外推全局部署.

检查分两级: required 缺失算失败, extra 缺失只记警告 (写进 AUDIT.md 的缺口节).

用法: uv run python docs/changes/verification-skills/evidence/ISSUE-15/audit_final.py [--repo-root <路径>]
退出码 0 表示 required 全通过, 1 表示有 required 失败.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_COMMIT = "ec9d55f"
SIX_SKILLS = (
    "verify-change",
    "create-verification-skill",
    "maintain-verification-skill",
    "blast-radius",
    "benchmark-checklist",
    "tdd-as-orchestra",
)
FIVE_SKILLS = SIX_SKILLS[:5]
EVIDENCE_REL = "docs/changes/verification-skills/evidence"
ISSUES = tuple(f"ISSUE-{n:02d}" for n in range(1, 15))

# 每个技能的交付边界语句 (D024 / AC-032), 原文取自各 SKILL.md.
DELIVERY_BOUNDARY = {
    "verify-change": r"不提交, 不推送, 不开 PR, 不合并",
    "create-verification-skill": r"不提交, 不推送, 不开 PR",
    "maintain-verification-skill": r"不自动提交, 推送, 开 PR 或合并",
    "blast-radius": r"不自动合并, 不创建 PR",
    "benchmark-checklist": r"提交, 推送, 开 PR 与合并都由使用者",
}
# 五个技能里不应出现的 Git 写动作命令 (读操作如 git log / git blame / gh pr view 不算).
GIT_WRITE_CMD = re.compile(r"git (?:push|commit)\b|gh pr create\b|gh pr merge\b|git merge\b|git request-pull\b")
# tdd-as-orchestra 保留既有本地提交与合并职责 (AC-032-3).
TDD_KEEP = (r"git merge --no-ff", r"提交只落在自己的", r"不推远端")
TDD_FORBID = re.compile(r"git push\b|gh pr create\b|git request-pull\b")

# 演练记录字段 (TECHNICAL 测试接缝末段 + 完成定义).
DRILL_REQUIRED = {
    "源路径": r"workflow/(?:verify-change|create-verification-skill|maintain-verification-skill|blast-radius|benchmark-checklist|tdd-as-orchestra)|\.agents/skills/(?:verify-change|create-verification-skill|maintain-verification-skill|blast-radius|benchmark-checklist|tdd-as-orchestra)",
    "源版本": r"\b[0-9a-f]{7,40}\b",
    "宿主与 pi 版本": r"pi 1\.3\.0",
    "加载方式": r"/skill:|\.agents/skills",
    "临时项目": r"/tmp/",
    # 结论边界: 明说不覆盖全局部署副本, 或明说结论只限于本机单一宿主与其他运行时未验证.
    "结论边界": r"(?:不|未|没有).{0,20}全局部署|其他运行时.{0,24}(?:未验证|未覆盖|没有验证)|只在.{0,12}单一宿主",
}
DRILL_EXTRA = {
    "会话名": r"会话",
    "提交渠道": r"send-text|send-keys",
    "命令与结果": r"命令|运行|退出码|exit",
    "清理": r"清理|关闭|删除",
}
# 每个技能的无自动 Git 动作演练记录 (AC-032 的角色对应).
GIT_ACTION_ROLES = {
    "verify-change (验收指挥者)": ("ISSUE-01", "ISSUE-02", "ISSUE-03", "ISSUE-04", "ISSUE-05", "ISSUE-10"),
    "create-verification-skill (配方生成者)": ("ISSUE-11",),
    "maintain-verification-skill (配方维护者)": ("ISSUE-12",),
    "blast-radius (调查者)": ("ISSUE-07", "ISSUE-13"),
    "benchmark-checklist (性能检查者)": ("ISSUE-06", "ISSUE-08", "ISSUE-09", "ISSUE-13"),
    "tdd-as-orchestra (既有 Git 职责)": ("ISSUE-14",),
}
GIT_BOUNDARY_TEXT = re.compile(r"(?:未|不|没有|无).{0,14}(?:提交|推送|开 PR|合并)|由实现流程")

ALLOWED_PATH = re.compile(
    r"^(?:README\.md"
    r"|workflow/(?:verify-change|create-verification-skill|maintain-verification-skill|blast-radius|benchmark-checklist)/.+"
    r"|workflow/tdd-as-orchestra/SKILL\.md"
    r"|docs/changes/verification-skills/.+)$"
)
FROZEN_PATHS = (
    "docs/changes/verification-skills/PRODUCT.md",
    "docs/changes/verification-skills/TECHNICAL.md",
    "docs/changes/verification-skills/DECISIONS.md",
    "sync-to-pi.py",
)
SECRET_PATTERNS = {
    "sk- 密钥": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "GitHub token": re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    "AWS key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Bearer 字面量": re.compile(r"Bearer [A-Za-z0-9._\-]{24,}"),
}
SECRET_PLACEHOLDER = re.compile(r"\$|&lt;|<[^>]*>|\bVAR\b|\btoken\b", re.IGNORECASE)

failures: list[str] = []
warnings: list[str] = []


def fail(check: str, message: str) -> None:
    failures.append(f"[{check}] {message}")


def warn(check: str, message: str) -> None:
    warnings.append(f"[{check}] {message}")


def run(args: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def frontmatter_fields(path: Path) -> tuple[dict[str, str], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        return {}, lines
    end = lines.index("---", 1)
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^(name|description|disable-model-invocation):\s*(.*)$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields, lines


def check_frontmatter(root: Path) -> None:
    """TS-002 / BR-009: 六个技能的 frontmatter 与项目级配方证据."""
    check = "audit-frontmatter"
    checker = root / "general/writing-for-llm/check_skill.py"
    for name in SIX_SKILLS:
        path = root / "workflow" / name / "SKILL.md"
        if not path.exists():
            fail(check, f"缺技能源文件 {path}")
            continue
        rc, out = run(["uv", "run", "python", str(checker), str(path)], root)
        if rc != 0:
            fail(check, f"{path.relative_to(root)} check_skill.py 退出 {rc}: {out}")
            continue
        fields, _ = frontmatter_fields(path)
        if fields.get("name") != name:
            fail(check, f"{name}: name 字段 {fields.get('name')!r} 与目录名不一致")
        if fields.get("disable-model-invocation") != "true":
            fail(check, f"{name}: 缺 disable-model-invocation: true")
        description = fields.get("description", "")
        if not description or len(description.splitlines()) != 1:
            fail(check, f"{name}: description 不是单行非空摘要")
        if description.startswith(("我", "你", "本技能", "当用户")):
            fail(check, f"{name}: description 看着像触发词而非人类摘要: {description[:24]}")
        print(f"PASS {check}: {name} frontmatter exit 0, name/description/disable-model-invocation 合格")

    recipes = sorted((root / EVIDENCE_REL / "ISSUE-11/generated").glob("*.md"))
    recipes += sorted((root / EVIDENCE_REL).glob("ISSUE-12/*/final-recipe/SKILL.md"))
    if not recipes:
        fail(check, "证据里找不到项目级配方原文")
        return
    with tempfile.TemporaryDirectory() as tmp:
        for recipe in recipes:
            fields, _ = frontmatter_fields(recipe)
            name = fields.get("name", "")
            if not name:
                fail(check, f"{recipe.relative_to(root)} 缺 name 字段")
                continue
            staged = Path(tmp) / name / "SKILL.md"
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(recipe, staged)
            rc, out = run(["uv", "run", "python", str(checker), str(staged)], root)
            if rc != 0:
                fail(check, f"项目级配方 {recipe.relative_to(root)} check_skill.py 退出 {rc}: {out}")
                continue
            if fields.get("disable-model-invocation") != "true":
                fail(check, f"项目级配方 {recipe.relative_to(root)} 缺 disable-model-invocation: true")
            print(f"PASS {check}: 项目级配方 {recipe.relative_to(root)} (name={name}) exit 0")


def check_no_git_actions(root: Path) -> None:
    """TS-001 / AC-032: 交付只交文件与证据, 既有 Git 职责仍由实现流程执行."""
    check = "audit-no-git-actions"
    for name in FIVE_SKILLS:
        text = (root / "workflow" / name / "SKILL.md").read_text(encoding="utf-8")
        if not re.search(DELIVERY_BOUNDARY[name], text):
            fail(check, f"{name}: 缺交付边界语句 /{DELIVERY_BOUNDARY[name]}/")
        hits = [line for line in text.splitlines() if GIT_WRITE_CMD.search(line)]
        if hits:
            fail(check, f"{name}: 出现 Git 写动作命令: {hits[:2]}")
        print(f"PASS {check}: {name} 只交付文件与证据, 无 Git 写动作命令")

    tdd = (root / "workflow/tdd-as-orchestra/SKILL.md").read_text(encoding="utf-8")
    for pattern in TDD_KEEP:
        if not re.search(pattern, tdd):
            fail(check, f"tdd-as-orchestra: 缺既有本地提交与合并职责 {pattern!r}")
    hits = [line for line in tdd.splitlines() if TDD_FORBID.search(line)]
    if hits:
        fail(check, f"tdd-as-orchestra: 出现远端发布命令: {hits[:2]}")
    print(f"PASS {check}: tdd-as-orchestra 保留本地提交与合并, 没有推送或开 PR")

    for role, issues in GIT_ACTION_ROLES.items():
        found = 0
        missing: list[str] = []
        for issue in issues:
            text = issue_docs(root, issue)
            if GIT_BOUNDARY_TEXT.search(text):
                found += 1
            else:
                missing.append(issue)
        if not found:
            fail(check, f"{role}: 所有相关演练记录都没有无自动 Git 动作说明")
        elif missing:
            warn(check, f"{role}: 这些 ISSUE 的顶层记录未写明无自动 Git 动作: {', '.join(missing)}")
        print(f"PASS {check}: {role} 有 {found}/{len(issues)} 份记录写明只交付文件与证据")


def check_scope(root: Path) -> None:
    """TS-003 / BR-011: 最终差异只在允许范围, 权威输入字节不变, 未同步部署."""
    check = "audit-scope"
    rc, out = run(["git", "rev-parse", "--verify", f"{BASE_COMMIT}^{{commit}}"], root)
    if rc != 0:
        fail(check, f"找不到开工基线提交 {BASE_COMMIT}: {out}")
        return
    rc, changed = run(["git", "diff", "--name-only", f"{BASE_COMMIT}..HEAD"], root)
    if rc != 0:
        fail(check, f"git diff 失败: {changed}")
        return
    paths = [p for p in changed.splitlines() if p]
    outside = [p for p in paths if not ALLOWED_PATH.match(p)]
    if outside:
        fail(check, f"最终差异越出允许范围: {outside[:10]}")
    print(f"PASS {check}: 相对 {BASE_COMMIT} 的 {len(paths)} 个改动文件全部在允许范围")

    rc, frozen = run(["git", "diff", "--name-only", f"{BASE_COMMIT}..HEAD", "--", *FROZEN_PATHS,
                      "docs/adr", "general", "tests", "pi"], root)
    if rc != 0:
        fail(check, f"git diff (冻结路径) 失败: {frozen}")
    elif frozen.strip():
        fail(check, f"权威输入或禁止路径被改动: {frozen.splitlines()[:10]}")
    else:
        print(f"PASS {check}: PRODUCT.md/TECHNICAL.md/DECISIONS.md, ADR, general, tests, pi, sync-to-pi.py 字节不变")

    other_workflow = sorted(
        p for p in paths
        if p.startswith("workflow/")
        and not re.match(r"^workflow/(?:verify-change|create-verification-skill|maintain-verification-skill|blast-radius|benchmark-checklist)/", p)
        and p != "workflow/tdd-as-orchestra/SKILL.md"
    )
    if other_workflow:
        fail(check, f"改动了范围外的既有技能: {other_workflow[:10]}")
    else:
        print(f"PASS {check}: 既有 workflow 技能除 tdd-as-orchestra/SKILL.md 外没有改动")

    rc, readme_diff = run(["git", "diff", f"{BASE_COMMIT}..HEAD", "--", "README.md"], root)
    removed = [line for line in readme_diff.splitlines() if line.startswith("-") and not line.startswith("---")]
    added = [line for line in readme_diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    if removed:
        fail(check, f"README.md 有删除或改写行: {removed[:5]}")
    missing = [name for name in FIVE_SKILLS if not any(f"](workflow/{name}/SKILL.md)" in line for line in added)]
    if missing:
        fail(check, f"README.md 索引缺五个新技能中的: {missing}")
    extra = [line for line in added if not re.search(
        r"^\+\| \[`(?:verify-change|create-verification-skill|maintain-verification-skill|blast-radius|benchmark-checklist)`\]\(workflow/(?:verify-change|create-verification-skill|maintain-verification-skill|blast-radius|benchmark-checklist)/SKILL\.md\)", line)]
    if extra:
        fail(check, f"README.md 新增了索引行以外的内容: {extra[:3]}")
    if not removed and not missing and not extra:
        print(f"PASS {check}: README.md 只新增五个技能的索引行")

    platforms = [p for p in paths if re.search(r"(?:^|/)(?:platform|runner|harness|schema|protocol)s?/|result[-_]protocol|evaluation[-_]platform", p)]
    if platforms:
        fail(check, f"出现疑似新增评测平台或结果协议文件: {platforms[:5]}")
    else:
        print(f"PASS {check}: 没有新增统一评测平台或结果 JSON 协议文件")

    home = Path.home()
    deployed = [str(home / ".agents/skills" / name) for name in FIVE_SKILLS if (home / ".agents/skills" / name).exists()]
    deployed += [str(home / ".pi/skills" / name) for name in FIVE_SKILLS if (home / ".pi/skills" / name).exists()]
    if deployed:
        fail(check, f"五个新技能出现在全局部署目录: {deployed}")
    else:
        print(f"PASS {check}: ~/.agents/skills 与 ~/.pi/skills 下没有五个新技能的部署副本")


def check_security_evidence(root: Path) -> None:
    """TS-004 / 安全策略: 授权, 清理, 脱敏与冻结目标."""
    check = "audit-security-evidence"
    evidence = root / EVIDENCE_REL

    plan = evidence / "ISSUE-10/drill-green-011-012/plan.md"
    report = evidence / "ISSUE-10/drill-green-011-012/report.md"
    cleanup = evidence / "ISSUE-10/logs/cleanup.txt"
    plan_text = plan.read_text(encoding="utf-8") if plan.exists() else ""
    report_text = report.read_text(encoding="utf-8") if report.exists() else ""
    problems = []
    if "写入授权" not in plan_text:
        problems.append("计划里没有写入授权节")
    if "写入与清理记录" not in report_text:
        problems.append("报告里没有写入与清理记录节")
    if "残留" not in report_text:
        problems.append("报告没有单列清理残留")
    if not cleanup.exists():
        problems.append("缺清理记录 logs/cleanup.txt")
    if "config/shared.json" not in report_text or "sha256" not in report_text.lower():
        problems.append("报告没有记录未批准对象的哈希不变证据")
    for problem in problems:
        fail(check, f"ISSUE-10 {problem}")
    if not problems:
        print(f"PASS {check}: ISSUE-10 有写入授权, 写入与清理记录, 残留单列与未批准对象哈希证据")

    oneoff = evidence / "ISSUE-08/green-ts003/docs/green3.md"
    oneoff_text = oneoff.read_text(encoding="utf-8") if oneoff.exists() else ""
    for pattern in ("一次性实验", "冻结"):
        if pattern not in oneoff_text:
            fail(check, f"ISSUE-08 一次性实验记录缺 {pattern}")
    if oneoff_text:
        print(f"PASS {check}: ISSUE-08 一次性实验边界记录存在且标明冻结目标")

    hits: list[str] = []
    placeholders = 0
    for path in sorted(evidence.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".txt", ".log", ".jsonl", ".py", ".sh", ".diff"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(text):
                snippet = match.group(0)
                if SECRET_PLACEHOLDER.search(snippet):
                    placeholders += 1
                    continue
                hits.append(f"{path.relative_to(root)}: {label}")
    if hits:
        fail(check, f"证据里出现疑似凭据字面量: {sorted(set(hits))[:5]}")
    else:
        print(f"PASS {check}: 证据里没有凭据字面量 (占位符 {placeholders} 处已排除)")

    frozen = evidence / "ISSUE-08/TS-003.md"
    frozen_text = frozen.read_text(encoding="utf-8") if frozen.exists() else ""
    if "冻结" not in frozen_text:
        warn(check, "ISSUE-08 TS-003 没有复查冻结目标未被修改的说明")
    else:
        print(f"PASS {check}: ISSUE-08 TS-003 复查了冻结目标未被修改")


def issue_docs(root: Path, issue: str) -> str:
    """一个 ISSUE 的顶层说明文档 (不含原始会话与夹具), 用于字段核对."""
    base = root / EVIDENCE_REL / issue
    parts = []
    for path in sorted(base.glob("*.md")):
        parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def check_drill_records(root: Path) -> None:
    """TS-005 / 测试接缝末段: 每个演练记录区分源文件, 宿主, 临时项目, 不外推全局部署."""
    check = "audit-drill-records"
    for issue in ISSUES:
        if not (root / EVIDENCE_REL / issue).is_dir():
            fail(check, f"{issue} 证据目录不存在")
            continue
        text = issue_docs(root, issue)
        missing = [field for field, pattern in DRILL_REQUIRED.items() if not re.search(pattern, text)]
        if missing:
            fail(check, f"{issue} 顶层记录缺字段: {', '.join(missing)}")
            continue
        missing_extra = [field for field, pattern in DRILL_EXTRA.items() if not re.search(pattern, text)]
        if missing_extra:
            warn(check, f"{issue} 顶层记录缺补充字段: {', '.join(missing_extra)}")
        print(f"PASS {check}: {issue} 记录了源文件与版本, 宿主与 pi 版本, 加载方式, 临时项目, 结论边界")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[5])
    args = parser.parse_args()
    root = args.repo_root.resolve()

    check_frontmatter(root)
    check_no_git_actions(root)
    check_scope(root)
    check_security_evidence(root)
    check_drill_records(root)

    print()
    if warnings:
        print(f"WARN {len(warnings)} 项 (写进 AUDIT.md 缺口节):")
        for item in warnings:
            print(f"  - {item}")
    if failures:
        print(f"FAIL {len(failures)} 项:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("OK: 五项审计 required 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
