"""阅读卡片只换排版, 用官方 Gherkin 展开数据, 不另写一份验收正文.

运行方式与 test_ac_draft.py 相同, 全部产物仅写入本测试的临时目录.
"""

import html.parser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_ac_draft import BASE, DRAFT, load_helper


OUTLINE = """```gherkin
# language: zh-CN
功能: 数量边界

背景: 阅读前提
假定 读者已打开当前文档
而且 文档为当前版本

@AC-001 @edge @G-001 @BR-001
场景大纲: 阅读 <数量> 条用例
假定 文档包含 <数量> 条验收标准
当 读者查看验收标准
那么 读者看到 <数量> 条用例
而且 读者看到标题 <标题>
但是 文档不出现额外用例

例子: 少量
| 数量 | 标题 | 备注 |
| 1 | 首条 | 首次阅读 |
| 2 | 次条 | 再次阅读 |

例子: 边界
| 数量 | 标题 | 备注 |
| 10 | 末条 | 最大数量 |
```
"""


class Elements(html.parser.HTMLParser):
    """按 HTML 节点读取实际展示文本, 不拿 HTML 字符串包含关系代替正文核对."""

    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.nodes = []
        self.stack = []
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        card = self.stack[-1]["card"] if self.stack else None
        if "acceptance-card" in attrs.get("class", "").split():
            card = attrs["id"]
        node = {"tag": tag, "attrs": attrs, "card": card, "text": ""}
        self.nodes.append(node)
        if tag not in ("meta", "br", "hr", "link", "input"):
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        for node in self.stack:
            node["text"] += data

    def select(self, class_name, *, card=None):
        return [node for node in self.nodes
                if class_name in node["attrs"].get("class", "").split()
                and (card is None or node["card"] == card)]

    def texts(self, class_name, *, card=None):
        return [node["text"] for node in self.select(class_name, card=card)]


class ReadingPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="to-spec-reading-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = self.root / "PRODUCT.base.md"
        self.draft = self.root / "用例.md"
        self.base.write_bytes(BASE.encode())
        self.draft.write_bytes(DRAFT.encode())
        self.helper = load_helper()

    def preview(self, draft=None, base=None):
        if draft is not None:
            self.draft.write_bytes(draft.encode())
        if base is not None:
            self.base.write_bytes(base.encode())
        result = self.helper.preview(self.base, self.draft)
        return Elements(Path(result["preview"]).read_text(encoding="utf-8"))

    def test_plain_steps_and_references_are_exact_source_text(self):
        parsed = self.preview()
        self.assertEqual(1, len(parsed.select("acceptance-card")))
        self.assertEqual(["阅读内容"], parsed.texts("case-title"))
        self.assertEqual([
            "读者已打开当前文档", "文档包含 1 条验收标准",
            "读者查看验收标准", "读者看到已确认的原文",
        ], parsed.texts("step-text"))
        self.assertEqual(["已有情况", "已有情况", "做这件事", "应该看到"],
                         parsed.texts("step-label"))
        self.assertEqual([
            "- G-001: 读者能看到已确认的内容.",
            "- BR-001: 内容以当前版本为准.",
        ], parsed.texts("reference-text"))
        self.assertNotIn("不新增第三方依赖", "".join(parsed.texts("acceptance-card")))
        self.assertEqual(["AC-001"], [node["attrs"]["data-ac"]
                                    for node in parsed.select("acceptance-card")])

    def test_every_example_row_gets_background_steps_and_all_columns(self):
        parsed = self.preview(OUTLINE)
        cards = parsed.select("acceptance-card")
        self.assertEqual(3, len(cards))
        self.assertEqual(["阅读 1 条用例", "阅读 2 条用例", "阅读 10 条用例"],
                         parsed.texts("case-title"))
        for card, quantity, title, note in zip(cards, ("1", "2", "10"),
                                              ("首条", "次条", "末条"),
                                              ("首次阅读", "再次阅读", "最大数量")):
            card_id = card["attrs"]["id"]
            self.assertEqual("AC-001", card["attrs"]["data-ac"])
            self.assertEqual([
                "读者已打开当前文档", "文档为当前版本",
                f"文档包含 {quantity} 条验收标准", "读者查看验收标准",
                f"读者看到 {quantity} 条用例", f"读者看到标题 {title}",
                "文档不出现额外用例",
            ], parsed.texts("step-text", card=card_id))
            self.assertIn("阅读前提", card["text"])
            self.assertEqual([quantity, title, note], parsed.texts("example-value", card=card_id))
            self.assertEqual(["数量", "标题", "备注"], parsed.texts("example-header", card=card_id))
            self.assertEqual(2, len(parsed.select("reference-text", card=card_id)))
        self.assertEqual(["少量", "少量", "边界"], parsed.texts("example-name"))
        # 连接步骤继承所属阶段, 但保留 "但是" 的转折, 不擅自变成 "而且".
        self.assertEqual(["已有情况", "已有情况", "已有情况", "做这件事",
                          "应该看到", "应该看到", "应该看到"],
                         parsed.texts("step-label", card=cards[0]["attrs"]["id"]))
        self.assertIn("但是", cards[0]["text"])

    def test_step_tables_docstrings_and_media_types_are_not_dropped(self):
        draft = OUTLINE.replace("而且 读者看到标题 <标题>", '''而且 读者看到标题 <标题>
  | 字段 | 值 |
  | 数量 | <数量> |
而且 读者看到如下原文
  """text/plain
  标题: <标题>
  数量: <数量>
  """''')
        parsed = self.preview(draft)
        self.assertEqual(["标题: 首条\n数量: 1", "标题: 次条\n数量: 2", "标题: 末条\n数量: 10"],
                         parsed.texts("docstring-content"))
        self.assertEqual(["text/plain"] * 3, parsed.texts("docstring-media"))
        for card, quantity in zip(parsed.select("acceptance-card"), ("1", "2", "10")):
            self.assertEqual(["字段", "值", "数量", quantity],
                             parsed.texts("argument-cell", card=card["attrs"]["id"]))

    def test_conjunctions_after_actions_keep_action_labels(self):
        draft = DRAFT.replace("当 读者查看验收标准", "当 读者查看验收标准\n而且 读者请求显示全部内容")
        parsed = self.preview(draft)
        self.assertEqual(["已有情况", "已有情况", "做这件事", "做这件事", "应该看到"],
                         parsed.texts("step-label"))

    def test_multiple_scenarios_keep_shared_ac_and_correct_local_premises(self):
        extra = """@AC-001 @failure @G-001
场景: 文档不可读
假定 文档无法打开
当 读者查看验收标准
那么 读者看到读取失败说明
"""
        parsed = self.preview(DRAFT.replace("```\n", extra + "```\n"))
        self.assertEqual(["AC-001", "AC-001"], [node["attrs"]["data-ac"]
                                                for node in parsed.select("acceptance-card")])
        self.assertEqual(["读者已打开当前文档", "文档无法打开", "读者查看验收标准", "读者看到读取失败说明"],
                         parsed.texts("step-text", card=parsed.select("acceptance-card")[1]["attrs"]["id"]))

    def test_multiline_rule_is_shown_with_its_original_continuation(self):
        entry = "- BR-001: 内容以当前版本为准.\n  不得展示上一版正文.\n  - 链接也必须指向当前版."
        parsed = self.preview(base=BASE.replace("- BR-001: 内容以当前版本为准.", entry))
        self.assertIn(entry, parsed.texts("reference-text"))

    def test_multiline_audit_rule_cannot_be_referenced_by_a_scenario(self):
        base = BASE.replace("- BR-001: 内容以当前版本为准.",
                            "- BR-001: 内容以当前版本为准.\n  (审计)")
        self.base.write_bytes(base.encode())
        for label, validate in (
            ("草稿校验", lambda: self.helper.checker.validate_draft(base, DRAFT)),
            ("正式校验", lambda: self.helper.checker.validate_product(
                self.helper.checker.with_draft(base, DRAFT, confirmed=True))),
            ("阅读预览", lambda: self.helper.preview(self.base, self.draft)),
        ):
            with self.subTest(label=label):
                with self.assertRaisesRegex(self.helper.checker.ValidationError, "审计"):
                    validate()

    def test_every_user_controlled_field_is_escaped(self):
        dangerous = "</span><script>alert('x')</script> & 中文"
        draft = OUTLINE.replace("数量边界", dangerous).replace("阅读前提", dangerous)
        draft = draft.replace("少量", dangerous).replace("首条", dangerous)
        draft = draft.replace("文档不出现额外用例", dangerous).replace("备注", dangerous)
        base = BASE.replace("内容以当前版本为准.", dangerous)
        parsed = self.preview(draft, base)
        self.assertIn(dangerous, parsed.texts("step-text"))
        self.assertIn(dangerous, parsed.texts("example-value"))
        self.assertIn(dangerous, parsed.texts("example-header"))
        self.assertIn("- BR-001: " + dangerous, parsed.texts("reference-text"))
        scripts = [node for node in parsed.nodes if node["tag"] == "script"]
        self.assertEqual(1, len(scripts))  # 仅保留 present 所需的固定状态脚本.
        self.assertIn("__PRESENTATION_STATE__", scripts[0]["text"])

    def test_escaped_table_cells_and_docstring_are_safe_and_decoded_once(self):
        draft = DRAFT.replace("那么 读者看到已确认的原文", r'''那么 读者看到已确认的原文
  | 值 |
  | A\|B\nC\\D &amp; </td><script>x</script> |
而且 读者看到说明
  """text/plain
  </pre><script>x</script> &amp;
  """''')
        parsed = self.preview(draft)
        self.assertEqual(["值", "A|B\nC\\D &amp; </td><script>x</script>"], parsed.texts("argument-cell"))
        self.assertEqual(["</pre><script>x</script> &amp;"], parsed.texts("docstring-content"))
        self.assertEqual(1, len([node for node in parsed.nodes if node["tag"] == "script"]))

    def test_comments_are_visible_verbatim_not_silently_discarded(self):
        comment = "# 注意: 这条说明也需要审阅, 不能只在原文件里出现."
        parsed = self.preview(DRAFT.replace("@AC-001", comment + "\n@AC-001"))
        self.assertIn(comment, parsed.texts("source-comment"))

    def test_card_view_does_not_hide_constraints_in_collapsed_details(self):
        parsed = self.preview(OUTLINE)
        self.assertEqual(3, len(parsed.select("acceptance-card")))
        for card in parsed.select("acceptance-card"):
            # 正文, 前提, 数据和规则默认全部可读.
            descendants = [node for node in parsed.nodes if node["card"] == card["attrs"]["id"]]
            self.assertFalse(any(node["tag"] == "details" or "hidden" in node["attrs"]
                                 for node in descendants))
        self.assertTrue(any(node["attrs"].get("id") == "draft-content" for node in parsed.nodes))

    def test_empty_examples_and_scenarios_refuse_incomplete_preview(self):
        invalid = {
            "空场景": DRAFT.replace("假定 文档包含 1 条验收标准\n当 读者查看验收标准\n那么 读者看到已确认的原文\n", ""),
            "没有场景": "```gherkin\n# language: zh-CN\n功能: 空功能\n```\n",
            "大纲没有例子": OUTLINE[:OUTLINE.index("例子: 少量")] + "```\n",
            "例子只有表头": OUTLINE.replace("| 10 | 末条 | 最大数量 |\n", ""),
        }
        for label, draft in invalid.items():
            with self.subTest(label=label):
                self.draft.write_bytes(draft.encode())
                with self.assertRaises(self.helper.checker.ValidationError):
                    self.helper.preview(self.base, self.draft)
                self.assertFalse(list(self.root.glob("*.html")))

    def test_duplicate_rule_ids_refuse_ambiguous_rule_text(self):
        self.base.write_bytes(BASE.replace("- BR-001: 内容以当前版本为准.",
                                           "- BR-001: 内容以当前版本为准.\n- BR-001: 相反的另一条规则.").encode())
        with self.assertRaises(self.helper.checker.InputError):
            self.helper.checker.validate_draft(self.base.read_text(encoding="utf-8"), DRAFT)
        with self.assertRaises(self.helper.checker.InputError):
            self.helper.preview(self.base, self.draft)
        self.assertFalse(list(self.root.glob("*.html")))

    def test_plain_scenario_without_background_or_type_tag_still_renders(self):
        draft = DRAFT.replace("背景:\n假定 读者已打开当前文档\n", "").replace("@normal ", "")
        parsed = self.preview(draft)
        self.assertEqual(["文档包含 1 条验收标准", "读者查看验收标准", "读者看到已确认的原文"],
                         parsed.texts("step-text"))
        self.assertEqual(["AC-001 / 阅读卡片 1"], parsed.texts("case-meta"))
        self.assertFalse(parsed.select("step-note"))

    def test_two_arguments_on_one_step_keep_source_order(self):
        table = "  | 字段 | 值 |\n  | 消息 | 正文 |\n"
        docstring = '  """text/plain\n  同一步骤的多行内容\n  """\n'
        for first, second in ((table, docstring), (docstring, table)):
            with self.subTest(first=first):
                parsed = self.preview(DRAFT.replace("那么 读者看到已确认的原文\n",
                                                   "那么 读者看到已确认的原文\n" + first + second))
                self.assertEqual(["字段", "值", "消息", "正文"], parsed.texts("argument-cell"))
                self.assertEqual(["同一步骤的多行内容"], parsed.texts("docstring-content"))
                order = [node["attrs"]["class"] for node in parsed.nodes
                         if node["attrs"].get("class") in ("argument-table", "docstring-content")]
                self.assertEqual(["argument-table", "docstring-content"] if first == table
                                 else ["docstring-content", "argument-table"], order)

    def test_cli_reports_rendering_failure_without_publishing_html(self):
        draft = OUTLINE[:OUTLINE.index("例子: 少量")] + "```\n"
        self.draft.write_bytes(draft.encode())
        run = subprocess.run([sys.executable, str(self.helper.__file__), "preview", str(self.base), str(self.draft)],
                             cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(1, run.returncode, run.stdout + run.stderr)
        self.assertFalse(json.loads(run.stdout)["success"])
        self.assertIn("缺少例子数据", json.loads(run.stdout)["error"])
        self.assertFalse(list(self.root.glob("*.html")))

    def test_documented_example_is_valid_and_expands_to_three_cards(self):
        reference = Path(self.helper.__file__).with_name("GHERKIN.md").read_text(encoding="utf-8")
        draft = self.helper.checker.FENCE_RE.search(reference)[0] + "\n"
        base = BASE.replace("- BR-002: 不新增第三方依赖. (审计)",
                            "- BR-002: 同一订单的累计补发次数不超过 3 次.")
        parsed = self.preview(draft, base)
        self.assertEqual(3, len(parsed.select("acceptance-card")))
        self.assertEqual(["AC-001", "AC-002", "AC-002"],
                         [node["attrs"]["data-ac"] for node in parsed.select("acceptance-card")])

    def test_preview_still_binds_exact_input_bytes_and_does_not_rewrite_them(self):
        raw = OUTLINE.replace("\n", "\r\n").encode()
        self.draft.write_bytes(raw)
        base = self.base.read_bytes()
        result = self.helper.preview(self.base, self.draft)
        self.assertEqual(self.helper.review_id(base, raw), result["review_id"])
        output = self.root / "PRODUCT.md"
        self.helper.promote(self.base, self.draft, output, result["review_id"])
        self.assertIn(raw, output.read_bytes())
        self.assertEqual(raw, self.draft.read_bytes())
        self.assertEqual(base, self.base.read_bytes())


if __name__ == "__main__":
    unittest.main()
