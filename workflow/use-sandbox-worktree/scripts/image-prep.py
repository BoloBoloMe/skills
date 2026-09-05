#!/usr/bin/env -S uv run python
"""M07 image preparation (ISSUE-03).

Two-layer image flow per D014/D015/D017/D024:
  build-base : generate base Containerfile -> build -> measure -> label -> record
  match      : candidate match per D017 (contents predicates + base-digest hard rule)
  build      : project layer build -> verify -> label -> record

Records: <records-root>/<slug>/builds/<build-id>/
  Containerfile, requirements.md, contents.md, build.json, context/
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLUG_SCRIPT = ROOT / "use-worktree/scripts/slug.py"

LABEL_PREFIX = "run.sandbox-worktree"
SCHEMA_VERSION = "1"
BASE_SLUG = "base"
GATE_EXTENSIONS = (
    "filesystem-operation-gate",
    "git-operation-gate",
    "python-operation-hook",
    "repetition-guard",
)
HEADER_KEYS = {"build-id", "project-id", "image-ref", "measured-at"}
IGNORE_SKILLS = shutil.ignore_patterns("__pycache__", ".venv", ".pytest_cache", "*.pyc")
IGNORE_PI_AGENT = shutil.ignore_patterns("auth.json", "sessions", "*.bak")

DEFAULT_PREFIX = "localhost/sandbox-worktree"
DEFAULT_SKILLS_DIR = Path.home() / ".agents" / "skills"
DEFAULT_PI_AGENT_DIR = Path.home() / ".pi" / "agent"

# base 层实测清单 (D014: OS + pi CLI + skill 库全量 + fd/rg; uv 供容器内 uv sync)
DEFAULT_BASE_REQUIREMENTS = """\
# base 层需求清单 (D014)
git>=2.30
node>=20
pi>=0.80
uv>=0.5
fd>=1.0 probe="fd --version"
rg>=13.0
sshd>=8.0 probe="/usr/sbin/sshd -V"
"""


class EnvError(Exception):
    """环境/参数错误 (退出码 2)."""


@dataclass
class RequirementEntry:
    name: str
    op: str | None
    version: str | None
    install: str | None = None
    probe: str | None = None


# ---------------------------------------------------------------- 清单解析

_PRED_TOKEN = re.compile(
    r"^(?P<name>[A-Za-z0-9._+-]+?)(?P<op>>=|<=|==|>|<)(?P<version>\d+(?:\.\d+)*)$"
)
_PLAIN_TOKEN = re.compile(r"^[A-Za-z0-9._+-]+$")


def parse_requirement_line(line: str) -> RequirementEntry:
    """条目 = 名称[谓词] [install="cmd"] [probe="cmd"] (D015 + 最小接缝补钉)."""
    parts = shlex.split(line.strip())
    if not parts:
        raise ValueError(f"empty requirement line: {line!r}")
    token = parts[0]
    name = op = version = None
    pred = _PRED_TOKEN.match(token)
    if pred:
        name, op, version = pred.group("name"), pred.group("op"), pred.group("version")
    elif _PLAIN_TOKEN.match(token):
        name = token
    else:
        raise ValueError(f"bad requirement token: {token!r}")
    entry = RequirementEntry(name=name, op=op, version=version)
    for part in parts[1:]:
        key, sep, value = part.partition("=")
        if not sep or key not in ("install", "probe") or not value:
            raise ValueError(f"bad directive in requirement line: {part!r}")
        setattr(entry, key, value)
    return entry


def parse_requirements(text: str) -> list[RequirementEntry]:
    entries = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(parse_requirement_line(stripped))
    return entries


# ---------------------------------------------------------------- 版本语义

_VERSION_TOKEN = re.compile(r"(?<![A-Za-z0-9])[vV]?(\d+(?:\.\d+)*)")


def extract_version(output: str) -> str | None:
    match = _VERSION_TOKEN.search(output)
    return match.group(1) if match else None


def _version_tuple(value: str) -> tuple[int, ...] | None:
    stripped = value.strip()
    if stripped[:1] in ("v", "V"):
        stripped = stripped[1:]
    components = stripped.split(".")
    if not all(component.isdigit() for component in components):
        return None
    return tuple(int(component) for component in components)


def predicate_satisfied(measured: str | None, op: str | None, required: str | None) -> bool:
    if op is None:
        return measured is not None
    if measured is None:
        return False
    measured_tuple = _version_tuple(measured)
    required_tuple = _version_tuple(required or "")
    if measured_tuple is None or required_tuple is None:
        return False
    width = max(len(measured_tuple), len(required_tuple))
    measured_tuple = measured_tuple + (0,) * (width - len(measured_tuple))
    required_tuple = required_tuple + (0,) * (width - len(required_tuple))
    if op == ">=":
        return measured_tuple >= required_tuple
    if op == "<=":
        return measured_tuple <= required_tuple
    if op == ">":
        return measured_tuple > required_tuple
    if op == "<":
        return measured_tuple < required_tuple
    if op == "==":
        return measured_tuple == required_tuple
    raise ValueError(f"unknown operator: {op!r}")


# ---------------------------------------------------------------- build-id / slug

_BUILD_ID = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})-(\d+)$")


def allocate_build_id(builds_root: Path) -> str:
    """date-seq 分配, 锁内查重即建目录占位 (D015/D024)."""
    builds_root.mkdir(parents=True, exist_ok=True)
    today = time.strftime("%Y.%m.%d")
    with open(builds_root / ".build-id.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        seq = 0
        for child in builds_root.glob(f"{today}-*"):
            match = _BUILD_ID.match(child.name)
            if match:
                seq = max(seq, int(match.group(4)))
        while True:
            seq += 1
            build_id = f"{today}-{seq}"
            target = builds_root / build_id
            if not target.exists():
                target.mkdir(parents=True)
                return build_id


def _short_hash(project_id: str) -> str:
    return hashlib.sha1(project_id.encode()).hexdigest()[:8]


def resolve_slug(records_root: Path, repo_path: Path) -> tuple[str, str]:
    """slug 复用 use-worktree slug.py; 冲突加短 hash; base 保留 (D024)."""
    repo = repo_path.resolve()
    if not repo.is_dir():
        raise EnvError(f"NO-REPO {repo}")
    project_id = str(repo)
    result = subprocess.run(
        [sys.executable, str(SLUG_SCRIPT), repo.name],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise EnvError(f"SLUG-FAIL {result.stderr.strip()}")
    match = re.search(r"^slug=(.+)$", result.stdout, re.MULTILINE)
    if not match:
        raise EnvError(f"SLUG-FAIL no slug= line in output: {result.stdout!r}")
    slug = match.group(1).strip()
    if slug == BASE_SLUG:
        return f"{slug}-{_short_hash(project_id)}", project_id
    slug_root = records_root / slug
    if slug_root.is_dir():
        known = set()
        for manifest in sorted(slug_root.glob("builds/*/build.json")):
            try:
                known.add(json.loads(manifest.read_text()).get("project-id"))
            except (json.JSONDecodeError, OSError):
                continue
        if known and known != {project_id}:
            slug = f"{slug}-{_short_hash(project_id)}"
    return slug, project_id


# ---------------------------------------------------------------- Containerfile 生成

BASE_CONTAINERFILE = """\
# base 层: OS + pi CLI + skill 库全量 + fd/rg 等 bin (D014)
# 门禁类扩展留 host 不进容器 (D014); ~/AGENTS.md 与 ~/docs 为 host 环境文档不注入 (D023)
FROM docker.io/library/node:24-bookworm-slim

# 稳定层: 系统 bin 与 sshd (M03 镜像契约)
RUN apt-get update \\
    && apt-get install --no-install-recommends -y git openssh-server fd-find ripgrep python3 ca-certificates curl \\
    && rm -rf /var/lib/apt/lists/* \\
    && ln -s /usr/bin/fdfind /usr/local/bin/fd

# 稳定层: uv (容器内 uv sync 重建依赖, host .venv 不可复用)
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh

# 稳定层: pi CLI
RUN npm i -g @earendil-works/pi-coding-agent

# agent 用户 + sshd host keys (M03 镜像契约)
RUN useradd --create-home --shell /bin/bash agent \\
    && ssh-keygen -A \\
    && mkdir -p /run/sshd \\
    && chmod 755 /run/sshd

# 常变层: skill 库全量 COPY (D014/D018); ~/.pi/agent 机械复制 (D018/D023); auth.json/sessions 不进镜像 (D018)
COPY --chown=agent:agent skills/ /home/agent/.agents/skills/
COPY --chown=agent:agent pi-agent/ /home/agent/.pi/agent/

# skill 库内 pyproject 的依赖在容器内重建 (无锁文件先试 frozen 再回落)
RUN for p in $(find /home/agent/.agents/skills -name pyproject.toml 2>/dev/null); do \\
        uv sync --project "$(dirname "$p")" --frozen || uv sync --project "$(dirname "$p")"; \\
    done \\
    && chown -R agent:agent /home/agent/.agents /home/agent/.pi

# 容器内端口固定 (22 ssh / 8800 present / 6080 noVNC); 宿主端口不钉, 诞生时 -p <容器端口> 动态分配
EXPOSE 22 8800 6080

CMD ["/usr/sbin/sshd", "-D", "-e"]
"""


def generate_base_containerfile() -> str:
    return BASE_CONTAINERFILE


def generate_project_containerfile(
    base_ref: str, base_digest: str, requirements: list[RequirementEntry]
) -> str:
    """项目层: FROM base@digest + install 指令按序 (fat 分层由清单作者保证, 生成器保序)."""
    lines = [f"FROM {base_ref}@{base_digest}"]
    for entry in requirements:
        if entry.install:
            lines.append(f"RUN {entry.install}")
    return "\n".join(lines) + "\n"


def stage_context(context_dir: Path, skills_dir: Path, pi_agent_dir: Path) -> None:
    """构建上下文 staging: skills 全量; ~/.pi/agent 除 auth.json/sessions (D018)."""
    if not skills_dir.is_dir():
        raise EnvError(f"NO-SKILLS-DIR {skills_dir}")
    if not pi_agent_dir.is_dir():
        raise EnvError(f"NO-PI-AGENT-DIR {pi_agent_dir}")
    context_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skills_dir, context_dir / "skills", ignore=IGNORE_SKILLS,
                    dirs_exist_ok=True)
    shutil.copytree(pi_agent_dir, context_dir / "pi-agent", ignore=IGNORE_PI_AGENT,
                    dirs_exist_ok=True)


# ---------------------------------------------------------------- podman 接缝

def run_podman(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(["podman", *args], capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"podman {' '.join(args)} failed: {result.stderr.strip()}")
    return result


def podman_build(context: Path, containerfile: Path, tags: list[str],
                 labels: dict[str, str]) -> str:
    cmd = ["build", "-q", "-f", str(containerfile), str(context)]
    for tag in tags:
        cmd += ["-t", tag]
    for key, value in labels.items():
        cmd += ["--label", f"{key}={value}"]
    result = run_podman(cmd)
    return result.stdout.strip().splitlines()[-1].strip()


def image_inspect(ref: str, template: str) -> str:
    return run_podman(["inspect", ref, "--format", template]).stdout.strip()


def resolve_base(base_ref: str) -> tuple[str, str]:
    """当前 base = 该 reference 下 build-id 最新的镜像 → (digest, build-id)."""
    listing = run_podman(
        ["images", "--no-trunc", "--format", "{{.ID}} {{.Repository}} {{.Tag}}"]
    ).stdout
    seen: dict[str, list[str]] = {}
    for line in listing.splitlines():
        image_id, repository, _tag = (line.split(None, 2) + ["", ""])[:3]
        if repository == base_ref:
            seen.setdefault(image_id, []).append(line)
    best: tuple[tuple[int, ...], str, str] | None = None
    for image_id in seen:
        build_id = image_inspect(
            image_id, '{{index .Labels "%s.build-id"}}' % LABEL_PREFIX
        )
        # images --no-trunc 给 sha256: 前缀, build -q 给裸 hex; 归一化后再比
        normalized = image_id.removeprefix("sha256:")
        match = _BUILD_ID.match(build_id)
        if not match:
            continue
        key = tuple(int(part) for part in match.groups())
        if best is None or key > best[0]:
            best = (key, normalized, build_id)
    if best is None:
        raise EnvError(f"NO-BASE {base_ref}")
    digest = image_inspect(best[1], "{{.Digest}}")
    return digest, best[2], best[1]


def build_id_sort_key(build_id: str) -> tuple[int, ...]:
    match = _BUILD_ID.match(build_id)
    if not match:
        return (0,)
    return tuple(int(part) for part in match.groups())


def probe_image(image: str, entry: RequirementEntry) -> str | None:
    """镜像内实测版本: probe 缺省 <name> --version, 取输出首个版本 token."""
    command = entry.probe or f"{entry.name} --version"
    result = subprocess.run(
        ["podman", "run", "--rm", image, "sh", "-c", command],
        capture_output=True, text=True, check=False, timeout=300,
    )
    return extract_version(result.stdout + result.stderr)


def measure(image: str, entries: list[RequirementEntry]) -> dict[str, str | None]:
    return {entry.name: probe_image(image, entry) for entry in entries}


def parse_contents(text: str) -> dict[str, str]:
    contents: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        name, sep, value = stripped.partition(":")
        if not sep:
            continue
        name = name.strip()
        if name in HEADER_KEYS:
            continue
        contents[name] = value.strip()
    return contents


def contents_text(build_id: str, project_id: str, image_ref: str,
                  measured: dict[str, str | None]) -> str:
    lines = [
        "# contents.md — 构建后实测版本清单 (D015)",
        f"build-id: {build_id}",
        f"project-id: {project_id}",
        f"image-ref: {image_ref}",
        f"measured-at: {time.strftime('%Y-%m-%dT%H:%M:%S')}",
    ]
    for name, version in measured.items():
        lines.append(f"{name}: {version if version is not None else 'MISSING'}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 流程

def verify_entries(entries: list[RequirementEntry],
                   measured: dict[str, str | None]) -> list[str]:
    failures = []
    for entry in entries:
        version = measured.get(entry.name)
        if not predicate_satisfied(version, entry.op, entry.version):
            failures.append(
                f"VERIFY-FAIL {entry.name}: measured={version!r} "
                f"required={entry.op or 'present'}{entry.version or ''}"
            )
    return failures


def write_build_manifest(record_dir: Path, *, kind: str, project_id: str, slug: str,
                         build_id: str, image_ref: str, digest: str,
                         contents_digest: str, base_ref: str, base_digest: str | None,
                         label_keys: list[str]) -> None:
    manifest = {
        "version": 1,
        "kind": kind,
        "project-id": project_id,
        "slug": slug,
        "build-id": build_id,
        "image-ref": image_ref,
        "digest": digest,
        "contents-digest": contents_digest,
        "base-ref": base_ref,
        "base-digest": base_digest,
        "label-keys": label_keys,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    (record_dir / "build.json").write_text(json.dumps(manifest, indent=2) + "\n")


def cmd_build_base(args: argparse.Namespace) -> int:
    prefix: str = args.prefix
    base_ref = args.base_ref or f"{prefix}/base"
    skills_dir = Path(args.skills_dir).expanduser()
    pi_agent_dir = Path(args.pi_agent_dir).expanduser()
    records_root = Path(args.records_root).expanduser()
    requirements_text = (
        Path(args.requirements).read_text()
        if args.requirements else DEFAULT_BASE_REQUIREMENTS
    )
    entries = parse_requirements(requirements_text)
    project_id, slug = BASE_SLUG, BASE_SLUG

    builds_root = records_root / slug / "builds"
    build_id = allocate_build_id(builds_root)
    record_dir = builds_root / build_id
    context_dir = record_dir / "context"
    stage_context(context_dir, skills_dir, pi_agent_dir)
    (record_dir / "requirements.md").write_text(requirements_text)
    containerfile = record_dir / "Containerfile"
    containerfile.write_text(generate_base_containerfile())

    print(f"[BUILD] phase-1 build {base_ref} (unstable id)")
    image_id = podman_build(context_dir, containerfile, [], {})

    measured = measure(image_id, entries)
    failures = verify_entries(entries, measured)
    if failures:
        (record_dir / "probe-report.txt").write_text(
            "\n".join(failures) + "\n" + json.dumps(measured, indent=2) + "\n"
        )
        run_podman(["rmi", "-f", image_id], check=False)
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    image_ref = f"{base_ref}:{build_id}"
    contents = contents_text(build_id, project_id, image_ref, measured)
    (record_dir / "contents.md").write_text(contents)
    contents_digest = hashlib.sha256(contents.encode()).hexdigest()
    label_keys = ["schema-version", "contents-digest", "build-id"]
    podman_build(context_dir, containerfile, [image_ref], {
        f"{LABEL_PREFIX}.schema-version": SCHEMA_VERSION,
        f"{LABEL_PREFIX}.contents-digest": contents_digest,
        f"{LABEL_PREFIX}.build-id": build_id,
    })
    run_podman(["rmi", "-f", image_id], check=False)
    digest = image_inspect(image_ref, "{{.Digest}}")
    write_build_manifest(
        record_dir, kind="base", project_id=project_id, slug=slug, build_id=build_id,
        image_ref=image_ref, digest=digest, contents_digest=contents_digest,
        base_ref=base_ref, base_digest=None, label_keys=label_keys,
    )
    print(f"kind=base")
    print(f"build-id={build_id}")
    print(f"image={image_ref}")
    print(f"digest={digest}")
    print(f"record={record_dir}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    prefix: str = args.prefix
    base_ref = args.base_ref or f"{prefix}/base"
    records_root = Path(args.records_root).expanduser()
    repo_path = Path(args.repo).expanduser()
    if not args.requirements:
        raise EnvError("REQUIREMENTS-REQUIRED --requirements <file>")
    requirements_path = Path(args.requirements).expanduser()
    try:
        requirements_text = requirements_path.read_text()
    except OSError as error:
        raise EnvError(f"BAD-REQUIREMENTS {error}")
    try:
        entries = parse_requirements(requirements_text)
    except ValueError as error:
        raise EnvError(f"BAD-REQUIREMENTS {error}")

    base_digest, base_build_id, base_image_id = resolve_base(base_ref)
    slug, project_id = resolve_slug(records_root, repo_path)
    builds_root = records_root / slug / "builds"
    build_id = allocate_build_id(builds_root)
    record_dir = builds_root / build_id
    context_dir = record_dir / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / "requirements.md").write_text(requirements_text)
    containerfile = record_dir / "Containerfile"
    containerfile.write_text(
        generate_project_containerfile(base_ref, base_digest, entries)
    )

    print(f"[BUILD] phase-1 build from {base_ref}@{base_digest} (base {base_build_id})")
    image_id = podman_build(context_dir, containerfile, [], {})

    measured = measure(image_id, entries)
    failures = verify_entries(entries, measured)
    if failures:
        (record_dir / "probe-report.txt").write_text(
            "\n".join(failures) + "\n" + json.dumps(measured, indent=2) + "\n"
        )
        if image_id != base_image_id:
            run_podman(["rmi", "-f", image_id], check=False)
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    image_ref = f"{prefix}/{slug}:{build_id}"
    contents = contents_text(build_id, project_id, image_ref, measured)
    (record_dir / "contents.md").write_text(contents)
    contents_digest = hashlib.sha256(contents.encode()).hexdigest()
    label_keys = ["project-id", "schema-version", "contents-digest", "build-id",
                  "base-digest"]
    podman_build(context_dir, containerfile, [image_ref], {
        f"{LABEL_PREFIX}.project-id": project_id,
        f"{LABEL_PREFIX}.schema-version": SCHEMA_VERSION,
        f"{LABEL_PREFIX}.contents-digest": contents_digest,
        f"{LABEL_PREFIX}.build-id": build_id,
        f"{LABEL_PREFIX}.base-digest": base_digest,
    })
    if image_id != base_image_id:
        run_podman(["rmi", "-f", image_id], check=False)
    digest = image_inspect(image_ref, "{{.Digest}}")
    write_build_manifest(
        record_dir, kind="project", project_id=project_id, slug=slug, build_id=build_id,
        image_ref=image_ref, digest=digest, contents_digest=contents_digest,
        base_ref=base_ref, base_digest=base_digest, label_keys=label_keys,
    )
    print(f"kind=project")
    print(f"slug={slug}")
    print(f"project-id={project_id}")
    print(f"build-id={build_id}")
    print(f"image={image_ref}")
    print(f"digest={digest}")
    print(f"record={record_dir}")
    return 0


def cmd_match(args: argparse.Namespace) -> int:
    prefix: str = args.prefix
    base_ref = args.base_ref or f"{prefix}/base"
    records_root = Path(args.records_root).expanduser()
    repo_path = Path(args.repo).expanduser()
    if not args.requirements:
        raise EnvError("REQUIREMENTS-REQUIRED --requirements <file>")
    try:
        entries = parse_requirements(Path(args.requirements).expanduser().read_text())
    except (OSError, ValueError) as error:
        raise EnvError(f"BAD-REQUIREMENTS {error}")

    base_digest, _base_build_id, _base_image_id = resolve_base(base_ref)
    slug, project_id = resolve_slug(records_root, repo_path)

    listing = run_podman(
        ["images", "--filter", f"label={LABEL_PREFIX}.project-id={project_id}",
         "--format", "{{.ID}}"]
    ).stdout
    digest_map: dict[str, dict] = {}
    for image_id in listing.split():
        info = image_inspect(
            image_id,
            "{{.Digest}}|{{index .Labels \"%s.build-id\"}}|"
            "{{index .Labels \"%s.contents-digest\"}}|{{.RepoTags}}"
            % (LABEL_PREFIX, LABEL_PREFIX),
        )
        digest, build_id, contents_digest, tags = info.split("|", 3)
        if not build_id:
            continue
        candidate = digest_map.setdefault(
            digest,
            {"build-id": build_id, "contents-digest": contents_digest,
             "tags": [], "id": image_id},
        )
        candidate["tags"] += tags.strip("[]").split()

    order = sorted(digest_map.items(),
                   key=lambda item: build_id_sort_key(item[1]["build-id"]),
                   reverse=True)
    for digest, candidate in order:
        build_id = candidate["build-id"]
        contents_path = records_root / slug / "builds" / build_id / "contents.md"
        if not contents_path.is_file():
            print(f"reason=record-missing:{build_id}")
            continue
        contents_bytes = contents_path.read_bytes()
        actual_digest = hashlib.sha256(contents_bytes).hexdigest()
        if candidate["contents-digest"] != actual_digest:
            print(f"reason=digest-mismatch:{build_id}")
            continue
        contents = parse_contents(contents_bytes.decode())
        ok = True
        for entry in entries:
            version = contents.get(entry.name)
            if version is None:
                print(f"reason=missing:{entry.name}")
                ok = False
            elif not predicate_satisfied(version, entry.op, entry.version):
                print(f"reason=version:{entry.name}")
                ok = False
        if not ok:
            continue
        base_label = candidate.get("base-digest")
        if base_label is None:
            info = image_inspect(
                candidate["id"],
                '{{index .Labels "%s.base-digest"}}' % LABEL_PREFIX,
            )
            candidate["base-digest"] = base_label = info.strip()
        if base_label != base_digest:
            print(f"reason=base-digest:{build_id}")
            continue
        wanted = f"{prefix}/{slug}:{build_id}"
        image = wanted if wanted in candidate["tags"] else (
            candidate["tags"][0] if candidate["tags"] else digest
        )
        print(f"verdict=REUSE")
        print(f"digest={digest}")
        print(f"image={image}")
        print(f"build-id={build_id}")
        print(f"slug={slug}")
        print(f"project-id={project_id}")
        return 0
    print(f"verdict=BUILD-NEW")
    print(f"slug={slug}")
    print(f"project-id={project_id}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("build-base", "match", "build"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--records-root",
                         default=str(Path.home() / ".agents" / "sandbox-worktree"))
        sub.add_argument("--prefix", default=DEFAULT_PREFIX)
        sub.add_argument("--base-ref", default=None)
        if name == "build-base":
            sub.add_argument("--skills-dir", default=str(DEFAULT_SKILLS_DIR))
            sub.add_argument("--pi-agent-dir", default=str(DEFAULT_PI_AGENT_DIR))
            sub.add_argument("--requirements", default=None)
        if name in ("match", "build"):
            sub.add_argument("--repo")
            sub.add_argument("--requirements")
        sub.set_defaults(handler={"build-base": cmd_build_base, "match": cmd_match,
                                  "build": cmd_build}[name])

    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except EnvError as error:
        print(str(error), file=sys.stderr)
        return 2
    except RuntimeError as error:
        print(f"PODMAN-FAIL {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
