"""验收草稿的真实 CLI, 校验复用, 原文嵌入和失败保护测试.

运行: uv run --with gherkin-official python -m unittest discover -s workflow/to-spec/tests -v
所有输入/输出均在独立临时目录, 不操作真实 agent 目录或常驻服务.
"""

import html.parser
from http.server import ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import ProxyHandler, build_opener

SKILL = Path(__file__).resolve().parents[1]
CHECK = SKILL / "check-ac.py"
HELPER = SKILL / "ac-draft.py"
BASE = """# 测试变更 Product Spec

## 背景

保留这段中文背景.

## 目标

- G-001: 读者能看到已确认的内容.

## 非目标

- NG-001: 不修改其他文档.

## 业务规则

- BR-001: 内容以当前版本为准.
- BR-002: 不新增第三方依赖. (审计)

## 验收标准

待确认, 此处暂不写入正式用例.

## 决策引用

- DECISIONS.md: D001.
"""
DRAFT = """```gherkin
# language: zh-CN
功能: 测试变更

背景:
假定 读者已打开当前文档

@AC-001 @normal @G-001 @BR-001
场景: 阅读内容
假定 文档包含 1 条验收标准
当 读者查看验收标准
那么 读者看到已确认的原文
```
"""
MARKER = "<!-- confirmed-flow: v1 -->"


def load_helper():
    spec = importlib.util.spec_from_file_location("to_spec_ac_draft_test", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PreText(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_draft = False
        self.text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "pre" and dict(attrs).get("id") == "draft-content":
            self.in_draft = True

    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_draft = False

    def handle_data(self, data):
        if self.in_draft:
            self.text += data


class AcDraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="to-spec-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = self.root / "PRODUCT.base.md"
        self.public = self.root / "review"
        self.public.mkdir()
        self.draft = self.public / "验收用例草稿-v1.md"
        self.output = self.root / "正式目录" / "PRODUCT.md"
        self.base.write_bytes(BASE.encode("utf-8"))
        self.draft.write_bytes(DRAFT.encode("utf-8"))

    def cli(self, script, *args):
        return subprocess.run(
            [sys.executable, str(script), *(str(arg) for arg in args)],
            cwd=self.root, capture_output=True, text=True, timeout=10,
        )

    def check(self, draft=None):
        return self.cli(CHECK, self.base, "--draft", draft or self.draft)

    def preview(self):
        run = self.cli(HELPER, "preview", self.base, self.draft)
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)
        return json.loads(run.stdout)

    def promote(self, review_id):
        return self.cli(HELPER, "promote", self.base, self.draft, self.output, "--review", review_id)

    def keep_old_output(self):
        self.output.parent.mkdir()
        self.output.write_bytes(b"old canonical content\r\n")
        return self.output.read_bytes()

    def test_draft_cli_passes_without_marker_and_does_not_write(self):
        before = self.base.read_bytes()
        run = self.check()
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertIn("1 个场景, 1 个 AC", run.stdout)
        self.assertEqual(before, self.base.read_bytes())
        self.assertFalse(self.output.exists())
        self.assertNotIn(MARKER, self.draft.read_text(encoding="utf-8"))

    def test_formal_cli_still_requires_marker(self):
        self.base.write_text(BASE.replace("待确认, 此处暂不写入正式用例.", DRAFT), encoding="utf-8")
        run = self.cli(CHECK, self.base)
        self.assertEqual(2, run.returncode)
        self.assertIn("确认流程标记", run.stderr)

    def test_formal_cli_preserves_legacy_confirmed_file_support(self):
        self.base.write_text(BASE.replace("待确认, 此处暂不写入正式用例.", MARKER + "\n" + DRAFT), encoding="utf-8")
        self.assertEqual(0, self.cli(CHECK, self.base).returncode)

    def test_draft_reuses_all_existing_checks(self):
        invalid = {
            "未知目标": DRAFT.replace("@G-001", "@G-999"),
            "未知规则": DRAFT.replace("@BR-001", "@BR-999"),
            "审计规则": DRAFT.replace("@BR-001", "@BR-002"),
            "多AC": DRAFT.replace("@AC-001", "@AC-001 @AC-002"),
            "无AC": DRAFT.replace("@AC-001 ", ""),
            "无覆盖": DRAFT.replace("@G-001 @BR-001", ""),
            "自由标签": DRAFT.replace("@normal", "@smoke"),
            "变体关键字": DRAFT.replace("假定", "假设"),
            "非关键字": DRAFT.replace("那么", "则"),
            "功能标签": DRAFT.replace("功能:", "@G-001\n功能:"),
            "规则分组": DRAFT.replace("背景:", "规则: 分组\n背景:"),
            "解析错误": DRAFT.replace("功能: 测试变更\n", ""),
        }
        for label, draft in invalid.items():
            with self.subTest(label=label):
                self.draft.write_text(draft, encoding="utf-8")
                run = self.check()
                self.assertEqual(1, run.returncode, run.stdout + run.stderr)

    def test_draft_rejects_extra_sections_prose_blocks_and_fake_marker(self):
        for draft in (DRAFT + "## 决策引用\n改写正文\n", "说明\n" + DRAFT, DRAFT + DRAFT, MARKER + "\n" + DRAFT, "", "```gherkin\n未闭合"):
            with self.subTest(draft=draft):
                self.draft.write_text(draft, encoding="utf-8")
                self.assertEqual(2, self.check().returncode)

    def test_missing_duplicate_or_fenced_acceptance_heading(self):
        for base in (BASE.replace("## 验收标准", "## 别的节"), BASE + "\n## 验收标准\n", BASE.replace("## 验收标准", "```markdown\n## 验收标准\n```"), BASE.replace("待确认, 此处暂不写入正式用例.", "```gherkin\n未闭合的旧代码块")):
            with self.subTest(base=base):
                self.base.write_text(base, encoding="utf-8")
                self.assertEqual(2, self.check().returncode)

    def test_multiscenario_outline_keeps_shared_ac(self):
        extra = """@AC-001 @edge @G-001
场景大纲: 数量边界
假定 文档包含 <数量> 条验收标准
当 读者查看验收标准
那么 读者看到 <数量> 条用例
例子:
| 数量 |
| 1 |
| 2 |
"""
        self.draft.write_text(DRAFT.replace("```\n", "\n" + extra + "```\n"), encoding="utf-8")
        run = self.check()
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertIn("2 个场景, 1 个 AC", run.stdout)

    def test_preview_is_safe_exact_text_and_never_overwrites(self):
        draft = DRAFT.replace("已确认的原文", "</pre><script>alert('x')</script> & 中文")
        self.draft.write_text(draft, encoding="utf-8")
        first = self.preview()
        second = self.preview()
        self.assertTrue(first["success"])
        self.assertEqual(first["review_id"], second["review_id"])
        self.assertNotEqual(first["preview"], second["preview"])
        page = Path(first["preview"]).read_text(encoding="utf-8")
        parser = PreText()
        parser.feed(page)
        self.assertEqual(draft, parser.text)
        self.assertNotIn("</pre><script>alert", page)
        self.assertIn("__PRESENTATION_STATE__", page)
        self.assertIn("charset=\"utf-8\"", page)
        self.assertEqual(self.public, Path(first["preview"]).parent)
        self.assertEqual(str(self.draft), first["draft"])
        self.assertNotIn(str(self.base), page)

    def test_preview_refuses_invalid_draft(self):
        self.draft.write_text(DRAFT.replace("@G-001", "@G-999"), encoding="utf-8")
        run = self.cli(HELPER, "preview", self.base, self.draft)
        self.assertEqual(1, run.returncode)
        self.assertFalse(json.loads(run.stdout)["success"])
        self.assertEqual([self.draft], list(self.public.iterdir()))

    def test_promote_embeds_exact_bytes_and_preserves_surrounding_sections(self):
        for newline in ("\n", "\r\n"):
            for trailing in (True, False):
                with self.subTest(newline=newline, trailing=trailing):
                    raw = DRAFT.replace("\n", newline).encode("utf-8")
                    if not trailing:
                        raw = raw.rstrip(b"\r\n")
                    self.draft.write_bytes(raw)
                    base = BASE.replace("\n", newline).encode("utf-8")
                    self.base.write_bytes(base)
                    review = self.preview()
                    run = self.promote(review["review_id"])
                    self.assertEqual(0, run.returncode, run.stdout + run.stderr)
                    output = self.output.read_bytes()
                    self.assertIn(raw, output)
                    self.assertEqual(base.split("## 验收标准".encode())[0], output.split("## 验收标准".encode())[0])
                    self.assertEqual(base.split("## 决策引用".encode())[1], output.split("## 决策引用".encode())[1])
                    self.assertEqual(1, output.count(MARKER.encode()))
                    self.assertEqual(0, self.cli(CHECK, self.output).returncode)
                    self.assertEqual(base, self.base.read_bytes())
                    self.assertEqual(raw, self.draft.read_bytes())

    def test_stale_review_rejects_changed_draft_or_product_context(self):
        old = self.keep_old_output()
        review = self.preview()["review_id"]
        self.draft.write_bytes(DRAFT.replace("1 条", "2 条").encode())
        self.assertEqual(2, self.promote(review).returncode)
        self.assertEqual(old, self.output.read_bytes())
        self.draft.write_bytes(DRAFT.encode())
        self.base.write_bytes(BASE.replace("保留这段中文背景", "背景已改变").encode())
        self.assertEqual(2, self.promote(review).returncode)
        self.assertEqual(old, self.output.read_bytes())

    def test_promote_requires_review_and_rejects_bad_hash(self):
        self.assertEqual(2, self.cli(HELPER, "promote", self.base, self.draft, self.output).returncode)
        self.assertEqual(2, self.promote("wrong").returncode)
        self.assertFalse(self.output.exists())

    def test_invalid_utf8_and_missing_file_are_input_errors(self):
        self.draft.write_bytes(b"\xff")
        self.assertEqual(2, self.check().returncode)
        self.assertEqual(2, self.cli(HELPER, "preview", self.base, self.draft).returncode)
        self.draft.unlink()
        self.assertEqual(2, self.check().returncode)

    def test_existing_ac_replaced_not_appended(self):
        self.base.write_text(BASE.replace("待确认, 此处暂不写入正式用例.", MARKER + "\n" + DRAFT.replace("AC-001", "AC-999")), encoding="utf-8")
        review = self.preview()["review_id"]
        self.assertEqual(0, self.promote(review).returncode)
        self.assertNotIn(b"AC-999", self.output.read_bytes())
        self.assertEqual(1, self.output.read_bytes().count(b"AC-001"))

    def test_gherkin_comment_heading_does_not_cut_section(self):
        self.draft.write_text(DRAFT.replace("@AC-001", "## 这是一条 Gherkin 注释, 不是 Markdown 节\n@AC-001"), encoding="utf-8")
        review = self.preview()["review_id"]
        self.assertEqual(0, self.promote(review).returncode)
        self.assertIn(self.draft.read_bytes(), self.output.read_bytes())

    def test_replace_failure_preserves_old_output_and_cleans_temp_file(self):
        helper = load_helper()
        old = self.keep_old_output()
        review = helper.preview(self.base, self.draft)["review_id"]
        before = set(self.output.parent.iterdir())
        with patch.object(helper.os, "replace", side_effect=OSError("replace failed")):
            with self.assertRaises(OSError):
                helper.promote(self.base, self.draft, self.output, review)
        self.assertEqual(old, self.output.read_bytes())
        self.assertEqual(before, set(self.output.parent.iterdir()))

    def test_formal_recheck_failure_preserves_old_output(self):
        helper = load_helper()
        old = self.keep_old_output()
        review = helper.preview(self.base, self.draft)["review_id"]
        original = helper.checker.validate_product

        def fail_formal(markdown, *, require_marker=True):
            if require_marker:
                raise helper.checker.ValidationError("正式复检失败")
            return original(markdown, require_marker=require_marker)

        with patch.object(helper.checker, "validate_product", side_effect=fail_formal):
            with self.assertRaises(helper.checker.ValidationError):
                helper.promote(self.base, self.draft, self.output, review)
        self.assertEqual(old, self.output.read_bytes())

    def test_change_during_validation_aborts_publication(self):
        helper = load_helper()
        old = self.keep_old_output()
        review = helper.preview(self.base, self.draft)["review_id"]
        original = helper.checker.validate_product

        def change_after_formal(markdown, *, require_marker=True):
            result = original(markdown, require_marker=require_marker)
            if require_marker:
                self.draft.write_bytes(DRAFT.replace("1 条", "2 条").encode())
            return result

        with patch.object(helper.checker, "validate_product", side_effect=change_after_formal):
            with self.assertRaises(helper.checker.InputError):
                helper.promote(self.base, self.draft, self.output, review)
        self.assertEqual(old, self.output.read_bytes())

    def test_output_cannot_overwrite_input_or_follow_symlink(self):
        helper = load_helper()
        review = helper.preview(self.base, self.draft)["review_id"]
        for target in (self.base, self.draft):
            with self.subTest(target=target):
                with self.assertRaises(helper.checker.InputError):
                    helper.promote(self.base, self.draft, target, review)
        self.output.parent.mkdir()
        self.output.symlink_to(self.base)
        with self.assertRaises(helper.checker.InputError):
            helper.promote(self.base, self.draft, self.output, review)
        self.assertEqual(BASE.encode(), self.base.read_bytes())

    def test_changed_output_is_not_overwritten_during_atomic_write(self):
        helper = load_helper()
        self.keep_old_output()
        review = helper.preview(self.base, self.draft)["review_id"]
        changed = b"another writer changed canonical content"
        original = helper.os.fsync

        def change_output(fd):
            self.output.write_bytes(changed)
            original(fd)

        with patch.object(helper.os, "fsync", side_effect=change_output):
            with self.assertRaises(helper.checker.InputError):
                helper.promote(self.base, self.draft, self.output, review)
        self.assertEqual(changed, self.output.read_bytes())
        self.assertEqual([self.output], list(self.output.parent.iterdir()))

    def test_formal_marker_must_precede_gherkin_block(self):
        self.base.write_text(BASE.replace("待确认, 此处暂不写入正式用例.", DRAFT + MARKER), encoding="utf-8")
        run = self.cli(CHECK, self.base)
        self.assertEqual(2, run.returncode)
        self.assertIn("必须位于", run.stderr)

    @unittest.skipIf(os.name == "nt", "present web 服务依赖 POSIX")
    def test_preview_and_original_are_reachable_through_present_handler(self):
        # 只起本测试的 loopback HTTP 服务, 不读写真实 present 常驻实例.
        web = SKILL.parents[1] / "general/present/scripts/web_server.py"
        spec = importlib.util.spec_from_file_location("to_spec_present_probe", web)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        raw = self.draft.read_bytes()
        self.draft = self.draft.with_name("草稿 #1?.md")
        self.draft.write_bytes(raw)
        result = self.preview()
        handler = type("ProbeHandler", (module._Handler,), {
            "roots": [str(self.public)], "roots_lock": threading.RLock(),
            "runtime_dir": self.root, "bind": "127.0.0.1",
        })
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            opener = build_opener(ProxyHandler({}))
            url = f"http://127.0.0.1:{server.server_port}/"
            with opener.open(url + Path(result["preview"]).name, timeout=5) as response:
                page = response.read().decode("utf-8")
                self.assertEqual("text/html", response.headers.get_content_type())
            class Links(html.parser.HTMLParser):
                hrefs = []

                def handle_starttag(self, tag, attrs):
                    if tag == "a":
                        self.hrefs.append(dict(attrs)["href"])

            links = Links()
            links.feed(page)
            raw_link = next(href for href in links.hrefs if not href.startswith("#"))
            with opener.open(url + raw_link, timeout=5) as response:
                self.assertEqual(200, response.status)
                self.assertEqual(raw, response.read())
                self.assertIn(response.headers.get_content_type(), ("text/markdown", "text/plain", "application/octet-stream"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    @unittest.skipIf(os.name == "nt", "Windows 不提供相同的 POSIX 权限语义")
    def test_preserves_existing_output_permissions(self):
        self.keep_old_output()
        self.output.chmod(0o640)
        self.assertEqual(0, self.promote(self.preview()["review_id"]).returncode)
        self.assertEqual(0o640, self.output.stat().st_mode & 0o777)


if __name__ == "__main__":
    unittest.main()
