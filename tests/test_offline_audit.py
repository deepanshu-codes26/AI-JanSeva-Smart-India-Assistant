"""Offline AI JanSeva checks that do not require Flask or network access."""
import ast
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

# Load only the pure scheme catalogue and guide functions so this suite can run
# even when Flask cannot be installed in an offline environment.
nodes = []
for node in TREE.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "SCHEMES"
        for target in node.targets
    ):
        nodes.append(node)
    if isinstance(node, ast.FunctionDef) and node.name in {
        "scheme_application_guide", "format_application_guide"
    }:
        nodes.append(node)
namespace = {"re": re}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(ROOT / "app.py"), "exec"), namespace)
SCHEMES = namespace["SCHEMES"]
guide_for = namespace["scheme_application_guide"]
format_guide = namespace["format_application_guide"]


class OfflineAudit(unittest.TestCase):
    def test_python_parses(self):
        ast.parse(SOURCE)

    def test_exactly_41_scheme_records(self):
        self.assertEqual(len(SCHEMES), 41)

    def test_scheme_names_unique(self):
        names = [item[0] for item in SCHEMES]
        self.assertEqual(len(names), len(set(names)))

    def test_all_scheme_portals_are_https(self):
        for name, category, description, url, audience in SCHEMES:
            with self.subTest(scheme=name):
                self.assertTrue(url.startswith("https://"), url)

    def test_all_41_schemes_match_and_format_in_5_languages(self):
        for name, *_ in SCHEMES:
            with self.subTest(scheme=name):
                guide = guide_for(f"How do I apply for {name}?")
                self.assertIsNotNone(guide)
                for language in ("en", "hi", "bn", "te", "ta"):
                    answer = format_guide(guide, language)
                    self.assertTrue(answer and len(answer) > 100)

    def test_regression_queries(self):
        cases = [
            ("Explain the rooftop solar subsidy process", "PM Surya Ghar"),
            ("How can I download my documents?", "DigiLocker"),
            ("How do I apply for Central Sector Scholarship?", "Central Sector Scholarship"),
            ("How do I apply for Ayushman Arogya Mandirs?", "Ayushman Arogya Mandirs"),
            ("How do I apply for PM-KISAN?", "PM-KISAN"),
            ("How do I apply for Beti Bachao Beti Padhao?", "Beti Bachao Beti Padhao"),
            ("How do I apply for National Scholarship Portal?", "National Scholarship Portal"),
            ("How do I apply for Disability Support?", "Disability Support"),
        ]
        for question, expected in cases:
            with self.subTest(question=question):
                guide = guide_for(question)
                self.assertIsNotNone(guide)
                self.assertIn(expected.lower(), guide["title"].lower())

    def test_assistant_endpoint_is_login_protected(self):
        route = re.search(
            r'@app\.route\("/api/assistant", methods=\["POST"\]\)\s+@api_login_required\s+def assistant\(',
            SOURCE,
        )
        self.assertIsNotNone(route)

    def test_health_endpoint_exists(self):
        self.assertIn('@app.route("/health")', SOURCE)

    def test_secret_key_can_be_configured_from_environment(self):
        self.assertIn('os.environ.get("SECRET_KEY"', SOURCE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
