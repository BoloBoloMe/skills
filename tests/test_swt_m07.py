"""M07 image preparation tests (ISSUE-03).

Unit slices: predicate/requirements parsing, build-id allocation, slug rules,
Containerfile generation audit. E2E slices: match and build flow against
real podman with per-test isolated prefix and records root.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import mkdtemp
from shutil import rmtree

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/image-prep.py"
SLUG_SCRIPT = ROOT / "workflow/use-worktree/scripts/slug.py"

TEST_PREFIX = "localhost/swt-m07-test"
TEST_BASE_REF = f"{TEST_PREFIX}/base"


def _load_module():
    spec = importlib.util.spec_from_file_location("image_prep", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["image_prep"] = module
    spec.loader.exec_module(module)
    return module


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def _kv(stdout: str) -> dict[str, str]:
    out = {}
    for line in stdout.splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            out[key] = value
    return out


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_scratch_image(tag: str, labels: dict[str, str]) -> str:
    """Tiny FROM scratch image carrying only labels; no network needed."""
    tmp = mkdtemp()
    try:
        ctx = Path(tmp)
        (ctx / "Containerfile").write_text("FROM scratch\n")
        cmd = ["podman", "build", "-q", "-f", "Containerfile", "-t", tag]
        for key, value in labels.items():
            cmd += ["--label", f"{key}={value}"]
        result = subprocess.run(cmd, cwd=ctx, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise AssertionError(f"scratch build failed: {result.stderr}")
        return result.stdout.strip().splitlines()[-1].strip()
    finally:
        rmtree(tmp, ignore_errors=True)


class _PodmanTestCase(unittest.TestCase):
    """Shared podman guard: fail loudly when podman is unavailable."""

    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            ["podman", "info"], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise AssertionError(f"podman unavailable: {result.stderr.strip()}")


class TestPredicates(unittest.TestCase):
    def setUp(self):
        self.m = _load_module()

    def test_parse_predicate_ops(self):
        for token, name, op, version in [
            ("node>=20", "node", ">=", "20"),
            ("node<=20", "node", "<=", "20"),
            ("node>20", "node", ">", "20"),
            ("node<20", "node", "<", "20"),
            ("node==20.1", "node", "==", "20.1"),
            ("fd", "fd", None, None),
        ]:
            entry = self.m.parse_requirement_line(token)
            self.assertEqual((entry.name, entry.op, entry.version), (name, op, version))

    def test_version_satisfies_matrix(self):
        cases = [
            ("24.1.0", ">=", "20", True),
            ("v24.1", ">=", "24", True),
            ("20.1.3", ">=", "20.2", False),
            ("1.2", "==", "1.2.0", True),
            ("19.9", ">=", "20", False),
            ("21", "<", "20", False),
            ("20.0.1", ">", "20", True),
            ("19", "<=", "20", True),
        ]
        for measured, op, required, expected in cases:
            self.assertEqual(
                self.m.predicate_satisfied(measured, op, required), expected,
                msg=f"{measured} {op} {required}",
            )

    def test_extract_version_token(self):
        self.assertEqual(self.m.extract_version("fake 1.2.3\n"), "1.2.3")
        self.assertEqual(self.m.extract_version("pi 0.84.4 (abc)\n"), "0.84.4")
        self.assertIsNone(self.m.extract_version("no version here"))
        self.assertEqual(self.m.extract_version("OpenSSH_9.2p1 Debian, ..."), "9.2")


class TestRequirementsParse(unittest.TestCase):
    def setUp(self):
        self.m = _load_module()

    def test_comments_and_blanks_skipped(self):
        text = "# comment\n\nnode>=20\n   \n# another\nfd\n"
        entries = self.m.parse_requirements(text)
        self.assertEqual([e.name for e in entries], ["node", "fd"])

    def test_directives_with_quoting(self):
        text = (
            'jdk>=21 install="apt-get update && apt-get install -y openjdk-21-jdk-headless"\n'
            'sshd>=9 probe="/usr/sbin/sshd -V"\n'
            'demo>=1.0 install="printf x" probe="demo --version"\n'
        )
        entries = self.m.parse_requirements(text)
        self.assertEqual(entries[0].install, "apt-get update && apt-get install -y openjdk-21-jdk-headless")
        self.assertIsNone(entries[0].probe)
        self.assertEqual(entries[1].probe, "/usr/sbin/sshd -V")
        self.assertEqual(entries[2].install, "printf x")
        self.assertEqual(entries[2].probe, "demo --version")

    def test_bad_line_raises(self):
        with self.assertRaises(ValueError):
            self.m.parse_requirements("node>=abc\n")
        with self.assertRaises(ValueError):
            self.m.parse_requirements("=9\n")

    def test_unknown_directive_raises(self):
        with self.assertRaises(ValueError):
            self.m.parse_requirements('node>=20 bogus="x"\n')


class TestBuildIdAndSlug(unittest.TestCase):
    def setUp(self):
        self.m = _load_module()
        self.root = Path(mkdtemp())
        self.addCleanup(rmtree, self.root, True)

    def test_allocate_build_id_sequence(self):
        first = self.m.allocate_build_id(self.root)
        today = time.strftime("%Y.%m.%d")
        self.assertEqual(first, f"{today}-1")
        self.assertTrue((self.root / first).is_dir())
        second = self.m.allocate_build_id(self.root)
        self.assertEqual(second, f"{today}-2")

    def test_allocate_skips_existing_dirs(self):
        today = time.strftime("%Y.%m.%d")
        (self.root / f"{today}-1").mkdir(parents=True)
        (self.root / f"{today}-5").mkdir(parents=True)
        self.assertEqual(self.m.allocate_build_id(self.root), f"{today}-6")

    def test_slug_and_project_id(self):
        repo = self.root / "demo-repo"
        repo.mkdir()
        slug, project_id = self.m.resolve_slug(self.root, repo)
        self.assertEqual(slug, "demo-repo")
        self.assertEqual(project_id, str(repo.resolve()))

    def test_slug_conflict_gets_short_hash(self):
        repo_a = self.root / "a" / "demo-repo"
        repo_b = self.root / "b" / "demo-repo"
        repo_a.mkdir(parents=True)
        repo_b.mkdir(parents=True)
        slug_a, pid_a = self.m.resolve_slug(self.root, repo_a)
        builds = self.root / slug_a / "builds" / "2026.09.05-1"
        builds.mkdir(parents=True)
        (builds / "build.json").write_text(json.dumps({"project-id": pid_a}))
        slug_b, _ = self.m.resolve_slug(self.root, repo_b)
        self.assertNotEqual(slug_b, slug_a)
        self.assertTrue(slug_b.startswith("demo-repo-"))
        self.assertLessEqual(len(slug_b), len("demo-repo-") + 8)
        # same project id resolves to the same slug again
        slug_a2, _ = self.m.resolve_slug(self.root, repo_a)
        self.assertEqual(slug_a2, slug_a)

    def test_base_slug_reserved(self):
        repo = self.root / "base"
        repo.mkdir()
        slug, _ = self.m.resolve_slug(self.root, repo)
        self.assertNotEqual(slug, "base")
        self.assertTrue(slug.startswith("base-"))


class TestGenerate(unittest.TestCase):
    def setUp(self):
        self.m = _load_module()
        self.reqs = self.m.parse_requirements("node>=20\njdk>=21 install=\"apt-get install -y jdk\"\n")

    def test_base_containerfile_contract(self):
        text = self.m.generate_base_containerfile()
        self.assertIn("FROM docker.io/library/node:24-bookworm-slim", text)
        self.assertIn("npm i -g @earendil-works/pi-coding-agent", text)
        self.assertIn("fd-find", text)
        self.assertIn("ripgrep", text)
        self.assertIn("uv", text)
        self.assertIn("useradd", text)
        self.assertIn("ssh-keygen -A", text)
        self.assertIn("COPY --chown=agent:agent skills/ /home/agent/.agents/skills/", text)
        self.assertIn("COPY --chown=agent:agent pi-agent/ /home/agent/.pi/agent/", text)
        self.assertIn("EXPOSE 22 8800 6080", text)
        self.assertIn('CMD ["/usr/sbin/sshd", "-D", "-e"]', text)
        self.assertIn("uv sync", text)

    def test_base_containerfile_fat_layering(self):
        """Stable layers before volatile copies (D014 fat principle)."""
        text = self.m.generate_base_containerfile()
        lines = [ln for ln in text.splitlines() if ln.strip()]
        idx = {key: next(i for i, ln in enumerate(lines) if key in ln) for key in
               ["FROM", "apt-get install", "npm i -g", "COPY --chown", "EXPOSE"]}
        self.assertLess(idx["FROM"], idx["apt-get install"])
        self.assertLess(idx["apt-get install"], idx["npm i -g"])
        self.assertLess(idx["npm i -g"], idx["COPY --chown"])
        self.assertLess(idx["COPY --chown"], idx["EXPOSE"])

    def test_no_gate_extensions_or_host_docs(self):
        """D014/D023: gate extensions, ~/AGENTS.md, ~/docs never enter images."""
        base = self.m.generate_base_containerfile()
        project = self.m.generate_project_containerfile(
            "localhost/x/base", "sha256:abc", self.reqs
        )
        for text in (base, project):
            for gate in self.m.GATE_EXTENSIONS:
                self.assertNotIn(gate, text)
        # no copy of host environment docs; only staged relative sources
        for text in (base, project):
            for line in text.splitlines():
                if line.startswith("COPY"):
                    source = line.split()[1]
                    self.assertFalse(source.startswith("/"), msg=line)
                    self.assertNotIn("docs", source, msg=line)
                    self.assertNotIn("AGENTS.md", source, msg=line)

    def test_project_containerfile_from_base_digest_ordered(self):
        text = self.m.generate_project_containerfile(
            "localhost/x/base", "sha256:abc", self.reqs
        )
        lines = [ln for ln in text.splitlines() if ln.strip()]
        self.assertEqual(lines[0], "FROM localhost/x/base@sha256:abc")
        run_lines = [ln for ln in lines if ln.startswith("RUN ")]
        self.assertEqual(run_lines, ["RUN apt-get install -y jdk"])

    def test_project_containerfile_no_install_lines(self):
        text = self.m.generate_project_containerfile(
            "localhost/x/base", "sha256:abc", self.m.parse_requirements("node>=20\n")
        )
        self.assertNotIn("RUN ", text)


class TestStageContextExcludes(unittest.TestCase):
    """D018: auth.json not baked, sessions excluded; pi-agent rest copied."""

    def setUp(self):
        self.m = _load_module()
        self.root = Path(mkdtemp())
        self.addCleanup(rmtree, self.root, True)
        self.skills = self.root / "skills-src"
        self.pi_agent = self.root / "pi-agent-src"
        (self.skills / "some-skill").mkdir(parents=True)
        (self.skills / "some-skill" / "SKILL.md").write_text("x")
        (self.skills / "__pycache__").mkdir()
        (self.skills / "__pycache__" / "junk.pyc").write_text("x")
        self.pi_agent.mkdir()
        for name in ("auth.json", "settings.json", "keybindings.json"):
            (self.pi_agent / name).write_text("{}")
        (self.pi_agent / "sessions").mkdir()
        (self.pi_agent / "sessions" / "s1.json").write_text("{}")
        self.ctx = self.root / "context"

    def test_staging_excludes_auth_and_sessions(self):
        self.m.stage_context(self.ctx, self.skills, self.pi_agent)
        staged_skills = self.ctx / "skills"
        staged_pi = self.ctx / "pi-agent"
        self.assertTrue((staged_skills / "some-skill" / "SKILL.md").exists())
        self.assertFalse((staged_skills / "__pycache__").exists())
        self.assertTrue((staged_pi / "settings.json").exists())
        self.assertTrue((staged_pi / "keybindings.json").exists())
        self.assertFalse((staged_pi / "auth.json").exists())
        self.assertFalse((staged_pi / "sessions").exists())


class TestMatchE2E(_PodmanTestCase):
    def setUp(self):
        self.m = _load_module()
        self.root = Path(mkdtemp())
        self.addCleanup(rmtree, self.root, True)
        self.records_root = self.root / "records"
        self.repo = self.root / "proj"
        self.repo.mkdir(parents=True)
        self.project_id = str(self.repo.resolve())
        # fake base image (scratch with build-id label) and its digest
        base_id = _build_scratch_image(
            f"{TEST_BASE_REF}:t1",
            {f"{self.m.LABEL_PREFIX}.build-id": "2026.09.01-1",
             f"{self.m.LABEL_PREFIX}.schema-version": self.m.SCHEMA_VERSION},
        )
        self.base_digest = self._digest_of(f"{TEST_BASE_REF}:t1")
        self.addCleanup(subprocess.run, ["podman", "rmi", "-f", base_id],
                        capture_output=True)
        self.contents = "node: 24.1.0\nfd: 1.0.1\nrg: 14.1.0\n"
        self._make_candidate("2026.09.05-1", self.contents)
        self._make_candidate("2026.09.05-2", self.contents)

    def _digest_of(self, ref: str) -> str:
        result = subprocess.run(
            ["podman", "inspect", ref, "--format", "{{.Digest}}"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()

    def _make_candidate(self, build_id: str, contents: str) -> str:
        tag = f"{TEST_PREFIX}/proj:{build_id}"
        image_id = _build_scratch_image(
            tag,
            {
                f"{self.m.LABEL_PREFIX}.project-id": self.project_id,
                f"{self.m.LABEL_PREFIX}.schema-version": self.m.SCHEMA_VERSION,
                f"{self.m.LABEL_PREFIX}.build-id": build_id,
                f"{self.m.LABEL_PREFIX}.contents-digest":
                    hashlib.sha256(contents.encode()).hexdigest(),
                f"{self.m.LABEL_PREFIX}.base-digest": self.base_digest,
            },
        )
        self.addCleanup(subprocess.run, ["podman", "rmi", "-f", image_id],
                        capture_output=True)
        build_dir = self.records_root / "proj" / "builds" / build_id
        build_dir.mkdir(parents=True)
        (build_dir / "contents.md").write_text(contents)
        (build_dir / "build.json").write_text(
            json.dumps({"project-id": self.project_id, "slug": "proj",
                        "build-id": build_id})
        )
        return image_id

    def _match(self, requirements: str, base_digest: str | None = None):
        req_file = self.root / "requirements.md"
        req_file.write_text(requirements)
        args = ["match", "--repo", str(self.repo), "--requirements", str(req_file),
                "--records-root", str(self.records_root), "--prefix", TEST_PREFIX,
                "--base-ref", TEST_BASE_REF]
        return _run(args)

    def test_reuse_newest_matching_candidate(self):
        result = self._match("node>=20\nfd>=1.0\n")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        values = _kv(result.stdout)
        self.assertEqual(values["verdict"], "REUSE")
        self.assertEqual(values["build-id"], "2026.09.05-2")
        self.assertEqual(values["digest"], self._digest_of(f"{TEST_PREFIX}/proj:2026.09.05-2"))

    def test_extra_contents_entries_tolerated(self):
        result = self._match("node>=20\n")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(_kv(result.stdout)["verdict"], "REUSE")

    def test_version_unsatisfied_builds_new(self):
        result = self._match("node>=99\n")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        values = _kv(result.stdout)
        self.assertEqual(values["verdict"], "BUILD-NEW")
        self.assertIn("version:node", result.stdout)

    def test_missing_requirement_builds_new(self):
        result = self._match("node>=20\njdk>=21\n")
        values = _kv(result.stdout)
        self.assertEqual(values["verdict"], "BUILD-NEW")
        self.assertIn("missing:jdk", result.stdout)

    def test_base_digest_hard_predicate(self):
        """Different current base => candidate unusable even if contents match."""
        _build_scratch_image(
            f"{TEST_BASE_REF}:t2",
            {f"{self.m.LABEL_PREFIX}.build-id": "2026.09.06-1",
             f"{self.m.LABEL_PREFIX}.schema-version": self.m.SCHEMA_VERSION},
        )
        self.addCleanup(subprocess.run, ["podman", "rmi", "-f", f"{TEST_BASE_REF}:t2"],
                        capture_output=True)
        result = self._match("node>=20\n")
        values = _kv(result.stdout)
        self.assertEqual(values["verdict"], "BUILD-NEW")
        self.assertIn("base-digest", result.stdout)

    def test_tampered_record_skips_candidate(self):
        build_dir = self.records_root / "proj" / "builds" / "2026.09.05-2"
        (build_dir / "contents.md").write_text("node: 23.0.0\n")
        result = self._match("node>=20\n")
        values = _kv(result.stdout)
        self.assertEqual(values["verdict"], "REUSE")
        self.assertEqual(values["build-id"], "2026.09.05-1")

    def test_no_base_image_exit_2(self):
        req_file = self.root / "requirements.md"
        req_file.write_text("node>=20\n")
        result = _run(["match", "--repo", str(self.repo),
                       "--requirements", str(req_file),
                       "--records-root", str(self.records_root),
                       "--prefix", TEST_PREFIX,
                       "--base-ref", f"{TEST_PREFIX}/no-such-base"])
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith("NO-BASE"))


class TestBuildFlowE2E(_PodmanTestCase):
    """Project build flow against a fake alpine base (fast, cached)."""

    FAKE_TOOL_INSTALL = (
        "printf '#!/bin/sh\\necho fake2 2.0.1\\n' > /usr/local/bin/fake2 "
        "&& chmod +x /usr/local/bin/fake2"
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        tmp = mkdtemp()
        try:
            ctx = Path(tmp)
            (ctx / "Containerfile").write_text(
                "FROM alpine:latest\n"
                "RUN printf '#!/bin/sh\\necho fake 1.2.3\\n' > /usr/local/bin/fake "
                "&& chmod +x /usr/local/bin/fake\n"
            )
            result = subprocess.run(
                ["podman", "build", "-q", "-f", "Containerfile",
                 "-t", f"{TEST_BASE_REF}:flow",
                 "--label", "run.sandbox-worktree.build-id=2026.09.01-1",
                 "--label", "run.sandbox-worktree.schema-version=1"],
                cwd=ctx, capture_output=True, text=True, check=False,
            )
            if result.returncode != 0:
                raise AssertionError(f"fixture base build failed: {result.stderr}")
        finally:
            rmtree(tmp, ignore_errors=True)

    @classmethod
    def tearDownClass(cls):
        subprocess.run(["podman", "rmi", "-f", f"{TEST_BASE_REF}:flow"],
                       capture_output=True)
        super().tearDownClass()

    def setUp(self):
        self.m = _load_module()
        self.root = Path(mkdtemp())
        self.addCleanup(rmtree, self.root, True)
        self.records_root = self.root / "records"
        self.repo = self.root / "proj"
        self.repo.mkdir(parents=True)

    def _requirements(self) -> Path:
        req = self.root / "requirements.md"
        req.write_text(
            "fake>=1.0\n"
            f'fake2>=2.0 install="{self.FAKE_TOOL_INSTALL}"\n'
        )
        return req

    def _build(self, requirements: Path):
        return _run(["build", "--repo", str(self.repo),
                     "--requirements", str(requirements),
                     "--records-root", str(self.records_root),
                     "--prefix", TEST_PREFIX, "--base-ref", TEST_BASE_REF])

    def test_build_verifies_and_records(self):
        result = self._build(self._requirements())
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        values = _kv(result.stdout)
        build_id = values["build-id"]
        self.assertRegex(build_id, r"\d{4}\.\d{2}\.\d{2}-\d+")
        record = self.records_root / "proj" / "builds" / build_id
        for name in ("Containerfile", "requirements.md", "contents.md", "build.json"):
            self.assertTrue((record / name).exists(), msg=name)
        contents = (record / "contents.md").read_text()
        self.assertIn("fake: 1.2.3", contents)
        self.assertIn("fake2: 2.0.1", contents)
        manifest = json.loads((record / "build.json").read_text())
        self.assertEqual(manifest["project-id"], str(self.repo.resolve()))
        self.assertEqual(manifest["base-ref"], TEST_BASE_REF)
        self.assertEqual(values["digest"], manifest["digest"])
        # label consistency on the tagged image
        ref = values["image"]
        inspect = subprocess.run(
            ["podman", "inspect", ref, "--format",
             '{{index .Labels "run.sandbox-worktree.contents-digest"}}|'
             '{{index .Labels "run.sandbox-worktree.project-id"}}|'
             '{{index .Labels "run.sandbox-worktree.base-digest"}}|'
             '{{index .Labels "run.sandbox-worktree.schema-version"}}'],
            capture_output=True, text=True, check=True,
        ).stdout.strip().split("|")
        self.assertEqual(inspect[0], _sha256_file(record / "contents.md"))
        self.assertEqual(inspect[1], str(self.repo.resolve()))
        self.assertTrue(inspect[2].startswith("sha256:"))
        self.assertEqual(inspect[3], self.m.SCHEMA_VERSION)
        self.addCleanup(subprocess.run, ["podman", "rmi", "-f", ref],
                        capture_output=True)
        # rematch reuses the built image
        match = _run(["match", "--repo", str(self.repo),
                      "--requirements", str(self._requirements()),
                      "--records-root", str(self.records_root),
                      "--prefix", TEST_PREFIX, "--base-ref", TEST_BASE_REF])
        self.assertEqual(match.returncode, 0, msg=match.stderr)
        self.assertEqual(_kv(match.stdout)["verdict"], "REUSE")
        self.assertEqual(_kv(match.stdout)["digest"], values["digest"])

    def test_build_predicate_failure_exit_1_untagged(self):
        req = self.root / "requirements.md"
        req.write_text("fake>=9.9\n")
        result = self._build(req)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stderr.startswith("VERIFY-FAIL"), msg=result.stderr)
        tagged = subprocess.run(
            ["podman", "images", "--filter",
             f"reference={TEST_PREFIX}/proj:*", "--format", "{{.ID}}"],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(tagged.stdout.strip(), "")

    def test_build_bad_requirements_exit_2(self):
        req = self.root / "requirements.md"
        req.write_text("this is not a requirement!!!\n")
        result = self._build(req)
        self.assertEqual(result.returncode, 2)

    def test_build_id_dedup_across_runs(self):
        first = _kv(self._build(self._requirements()).stdout)
        self.addCleanup(subprocess.run,
                        ["podman", "rmi", "-f", first["image"]],
                        capture_output=True)
        second = _kv(self._build(self._requirements()).stdout)
        self.addCleanup(subprocess.run,
                        ["podman", "rmi", "-f", second["image"]],
                        capture_output=True)
        self.assertNotEqual(first["build-id"], second["build-id"])
        seq = lambda bid: int(bid.rsplit("-", 1)[1])
        self.assertEqual(seq(second["build-id"]), seq(first["build-id"]) + 1)


class TestBaseBuildE2E(_PodmanTestCase):
    """TS-006: real base build (network heavy: apt/npm/uv)."""

    base_ref = f"{TEST_PREFIX}/base-it"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = Path(mkdtemp())
        cls.records_root = cls.root / "records"

    @classmethod
    def tearDownClass(cls):
        subprocess.run(
            ["bash", "-c",
             f"podman images --format '{{{{.ID}}}}' --filter reference={cls.base_ref} "
             "| xargs -r podman rmi -f"],
            capture_output=True,
        )
        rmtree(cls.root, ignore_errors=True)
        super().tearDownClass()

    def test_real_base_build_full_contract(self):
        real_skills = Path.home() / ".agents" / "skills"
        pi_agent_src = Path.home() / ".pi" / "agent"
        result = _run([
            "build-base",
            "--records-root", str(self.records_root),
            "--skills-dir", str(real_skills),
            "--pi-agent-dir", str(pi_agent_src),
            "--base-ref", self.base_ref,
        ])
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        values = _kv(result.stdout)
        build_id = values["build-id"]
        record = self.records_root / "base" / "builds" / build_id
        for name in ("Containerfile", "requirements.md", "contents.md", "build.json"):
            self.assertTrue((record / name).exists(), msg=name)
        contents = (record / "contents.md").read_text()
        for entry in ("git", "node", "pi", "uv", "fd", "rg", "sshd"):
            self.assertRegex(contents, rf"(?m)^{entry}: \d", msg=contents)
        # D018: auth.json never staged into build context
        self.assertFalse((record / "context" / "pi-agent" / "auth.json").exists())
        self.assertFalse((record / "context" / "pi-agent" / "sessions").exists())
        # runtime contract preserved: sshd foreground + fixed exposed ports
        inspect = subprocess.run(
            ["podman", "inspect", values["image"], "--format",
             "{{.Config.Cmd}}|{{.Config.ExposedPorts}}|"
             '{{index .Labels "run.sandbox-worktree.contents-digest"}}'],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        cmd, exposed, label_digest = inspect.split("|")
        self.assertIn("sshd", cmd)
        for port in ("22/tcp", "8800/tcp", "6080/tcp"):
            self.assertIn(port, exposed)
        self.assertEqual(label_digest, _sha256_file(record / "contents.md"))
        self.addCleanup(subprocess.run, ["podman", "rmi", "-f", values["image"]],
                        capture_output=True)


if __name__ == "__main__":
    unittest.main()
