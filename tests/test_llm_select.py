import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "general/llm-select/score.py"
SPEC = importlib.util.spec_from_file_location("llm_score", SCRIPT_PATH)
score = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(score)

FULL_DIMS = {"coding": 1.0, "knowledge": 1.0, "longctx": 1.0, "multimodal": 1.0,
             "stability": 1.0, "price": 1.0, "speed": 1.0}


class UnitCostTests(unittest.TestCase):
    def test_formula(self):
        self.assertEqual(score.unit_cost({"input": 4, "output": 20}), 0.75 * 4 + 0.25 * 20)

    def test_missing_input_or_output_returns_none(self):
        self.assertIsNone(score.unit_cost({}))
        self.assertIsNone(score.unit_cost({"input": 4}))
        self.assertIsNone(score.unit_cost({"output": 4}))

    def test_non_numeric_cost_returns_none(self):
        self.assertIsNone(score.unit_cost({"input": 4, "output": "x"}))

    def test_all_zero_returns_zero(self):
        self.assertEqual(score.unit_cost({"input": 0, "output": 0, "cacheRead": 0}), 0.0)


class PriceScoreTests(unittest.TestCase):
    def test_baseline_price_is_one(self):
        models = {"a/base": {"cost": {"input": 1, "output": 1}}}
        prices = score.price_scores(models, ["a/base"], "a/base")
        self.assertEqual(prices["a/base"], 1.0)

    def test_free_model_caps_not_none(self):
        models = {"a/base": {"cost": {"input": 1, "output": 1}},
                  "a/free": {"cost": {"input": 0, "output": 0}}}
        prices = score.price_scores(models, ["a/base", "a/free"], "a/base")
        self.assertEqual(prices["a/free"], score.PRICE_CAP)

    def test_missing_cost_returns_none(self):
        models = {"a/base": {"cost": {"input": 1, "output": 1}},
                  "a/novalue": {"cost": {}}}
        prices = score.price_scores(models, ["a/base", "a/novalue"], "a/base")
        self.assertIsNone(prices["a/novalue"])

    def test_baseline_free_returns_none(self):
        models = {"a/free": {"cost": {"input": 0, "output": 0}}}
        self.assertIsNone(score.price_scores(models, ["a/free"], "a/free"))

    def test_baseline_not_in_catalog_returns_none(self):
        self.assertIsNone(score.price_scores({}, [], "a/missing"))


class GlobTests(unittest.TestCase):
    def test_star_does_not_cross_provider(self):
        self.assertTrue(score.glob_match("a/*", "a/x"))
        self.assertFalse(score.glob_match("a/*", "a/b/x"))

    def test_question_single_char(self):
        self.assertTrue(score.glob_match("a/x?", "a/x1"))
        self.assertFalse(score.glob_match("a/x?", "a/x"))
        self.assertFalse(score.glob_match("a/?", "a/xy"))


class ResolveScopeTests(unittest.TestCase):
    def test_default_uses_table_keys(self):
        args = mock.Mock(scope=None)
        self.assertCountEqual(score.resolve_scope(args, {"a/b": {}, "c/d": {}}), ["a/b", "c/d"])

    def test_glob_expands(self):
        args = mock.Mock(scope="openai/*")
        self.assertCountEqual(score.resolve_scope(args, {"openai/x": {}, "openai/y": {}, "z/a": {}}),
                              ["openai/x", "openai/y"])

    def test_literal_kept_even_outside_table(self):
        args = mock.Mock(scope="free/m1")
        self.assertEqual(score.resolve_scope(args, {"z/a": {}}), ["free/m1"])

    def test_scope_no_match_returns_empty(self):
        args = mock.Mock(scope="nomatch/*")
        self.assertEqual(score.resolve_scope(args, {"a/b": {}}), [])


class DescribeTests(unittest.TestCase):
    def test_unscored_wins_over_free(self):
        out = score.describe({}, "", {"unscored": True, "free": True})
        self.assertIn("免费", out)
        self.assertIn("未评分", out)

    def test_partial_marks_missing_dims(self):
        out = score.describe(FULL_DIMS, "", {"partial": ["speed", "knowledge"]})
        self.assertIn("[部分评分]", out)
        self.assertIn("速度", out)
        self.assertIn("知识", out)

    def test_weak_evidence_annotated(self):
        out = score.describe(FULL_DIMS, "", {"weak": ["speed"]})
        self.assertIn("[弱依据]", out)
        self.assertIn("速度", out)

    def test_free_message(self):
        out = score.describe(FULL_DIMS, "", {"free": True})
        self.assertIn("免费", out)


class BuildRowsTests(unittest.TestCase):
    def _models(self):
        return {
            "a/base": {"cost": {"input": 1, "output": 1}, "thinking": ["off", "high"]},
            "a/x": {"cost": {"input": 0.5, "output": 0.5}, "thinking": ["high"]},
            "a/free": {"cost": {"input": 0, "output": 0}, "thinking": ["off"]},
        }

    def _table(self):
        return {"a/base": {"coding": 1, "knowledge": 1},
                "a/x": {"coding": 1.5, "knowledge": 1},
                "a/partial": {"coding": 1}}

    def test_price_dim_not_flagged_partial(self):
        models = self._models()
        prices = score.price_scores(models, ["a/base", "a/x"], "a/base")
        rows = score.build_rows(models, self._table(), ["a/base", "a/x"], prices)
        for r in rows:
            self.assertNotIn("price", r["flags"].get("partial", []))

    def test_free_model_flagged_free(self):
        models = self._models()
        prices = score.price_scores(models, ["a/base", "a/free"], "a/base")
        rows = score.build_rows(models, self._table(), ["a/base", "a/free"], prices)
        freerow = next(r for r in rows if r["full"] == "a/free")
        self.assertTrue(freerow["flags"]["free"])
        self.assertEqual(freerow["scores"]["price"], score.PRICE_CAP)

    def test_missing_manual_dim_is_partial(self):
        models = self._models()
        prices = score.price_scores(models, ["a/base", "a/partial"], "a/base")
        rows = score.build_rows(models, self._table(), ["a/base", "a/partial"], prices)
        partial = next(r for r in rows if r["full"] == "a/partial")
        self.assertIn("knowledge", partial["flags"]["partial"])

    def test_outside_table_is_unscored_not_partial(self):
        models = {"a/base": {"cost": {"input": 1, "output": 1}}}
        prices = score.price_scores(models, ["a/base", "a/new"], "a/base")
        rows = score.build_rows(models, {"a/base": {"coding": 1}}, ["a/base", "a/new"], prices)
        new = next(r for r in rows if r["full"] == "a/new")
        self.assertTrue(new["unscored"])
        self.assertEqual(new["flags"].get("partial"), [])

    def test_sort_unscored_last(self):
        models = {"a/base": {"cost": {"input": 1, "output": 1}},
                  "a/strong": {"cost": {"input": 0.1, "output": 0.1}}}
        table = {"a/base": {"coding": 1}, "a/strong": {"coding": 3}}
        prices = score.price_scores(models, ["a/base", "a/strong", "a/new"], "a/base")
        rows = score.build_rows(models, table, ["a/base", "a/strong", "a/new"], prices)
        self.assertTrue(rows[-1]["unscored"])


class MainFailReasonTests(unittest.TestCase):
    """CLI 主流程失败分支. 用子进程跑真实脚本, 断言退出码与 stderr 前缀."""

    def _tmp(self, content):
        tmp = tempfile.TemporaryDirectory()
        p = Path(tmp.name) / "t.json"
        p.write_text(content, encoding="utf-8")
        return tmp, p

    def _run(self, scores, catalog):
        cmd = ["uv", "run", "python", str(SCRIPT_PATH), "--scores", scores, "--catalog", catalog]
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)

    def test_no_catalog_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            table = Path(tmp) / "t.json"
            table.write_text(json.dumps({"baseline": "a/b", "models": {}}), encoding="utf-8")
            result = self._run(str(table), "/nonexistent/catalog.json")
            self.assertEqual(1, result.returncode)
            self.assertTrue(result.stderr.startswith("no-catalog"), result.stderr)

    def test_no_table_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = Path(tmp) / "c.json"
            cat.write_text(json.dumps({"models": {}}), encoding="utf-8")
            result = self._run("/nonexistent/table.json", str(cat))
            self.assertEqual(1, result.returncode)
            self.assertTrue(result.stderr.startswith("no-table"), result.stderr)

    def test_bad_baseline_empty(self):
        self._assert_reason(json.dumps({"baseline": "", "models": {}}), "bad-baseline")

    def test_bad_json_non_numeric_scores(self):
        self._assert_reason(json.dumps({"baseline": "a/b", "models": {"a/b": {"coding": "strong"}}}),
                            "bad-json", needle="a/b")

    def test_bad_json_broken(self):
        self._assert_reason("{broken", "bad-json")

    def test_bad_json_valid_json_non_object(self):
        # 合法 JSON 但非对象 (如 []), load_table 之前误判不可达而裸 traceback, 现应报 bad-json.
        self._assert_reason("[]", "bad-json")

    def test_bad_scope_no_match(self):
        self._assert_reason(json.dumps({"baseline": "a/b", "models": {"a/b": {"coding": 1}}}),
                            "bad-scope", scope="nomatch/*",
                            needle="--scope")

    def test_bad_baseline_baseline_free_in_catalog(self):
        # baseline 免费(cost=0) 是无效分母, 且 scope 非空时才报 bad-baseline (而非 bad-scope).
        self._assert_reason(json.dumps({"baseline": "a/free", "models": {"a/x": {"coding": 1}}}),
                            "bad-baseline", cat={"models": {"a/free": {"cost": {"input": 0, "output": 0}},
                                                                 "a/x": {"cost": {"input": 1, "output": 1}}}})

    def _assert_reason(self, scores_json, reason, scope=None, needle=None, cat=None):
        with tempfile.TemporaryDirectory() as tmp:
            table = Path(tmp) / "t.json"
            table.write_text(scores_json, encoding="utf-8")
            catalog_path = Path(tmp) / "c.json"
            if cat is None:
                cat = {"models": {"a/b": {"cost": {"input": 1, "output": 1}}}}
            catalog_path.write_text(json.dumps(cat), encoding="utf-8")
            extra = ["--scope", scope] if scope else []
            result = subprocess.run(
                ["uv", "run", "python", str(SCRIPT_PATH), "--scores", str(table),
                 "--catalog", str(catalog_path), *extra],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(1, result.returncode, result.stderr)
            self.assertTrue(result.stderr.startswith(reason), result.stderr)
            if needle:
                self.assertIn(needle, result.stderr)


class SmokeTests(unittest.TestCase):
    """端到端冒烟: 用独立 fixture 跑, 不依赖本机数据, 输出含 baseline 且成功."""

    def test_end_to_end_output_contains_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            baseline = "acme/base"
            scores = Path(tmp) / "llm-scores.json"
            scores.write_text(json.dumps({"baseline": baseline, "models": {baseline: {"coding": 1}}}),
                              encoding="utf-8")
            catalog = Path(tmp) / "model-catalog.json"
            catalog.write_text(json.dumps({"models": {baseline: {"cost": {"input": 1, "output": 1}}}}),
                               encoding="utf-8")
            result = subprocess.run(
                ["uv", "run", "python", str(SCRIPT_PATH),
                 "--scores", str(scores), "--catalog", str(catalog)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(baseline, result.stdout)
            self.assertIn("thinking 支持", result.stdout)


if __name__ == "__main__":
    unittest.main()
