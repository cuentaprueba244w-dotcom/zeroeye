import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_PY = ROOT / "build.py"

TARGET_FUNCTIONS = {
    "current_commit_id",
    "diagnostic_paths_for_commit",
    "split_diagnostic_logd",
    "check_encryptly_runs",
    "check_prerequisites",
    "build_module",
    "clean_module",
    "verify_binary",
    "run_cmd",
    "collect_system_info",
    "build_diagnostic_report",
    "write_diagnostic_report",
    "commit_diagnostic_artifacts",
    "generate_logd",
    "print_summary",
    "main",
}


def parse_build_module():
    return ast.parse(BUILD_PY.read_text(encoding="utf-8"))


class BuildTypeHintsTests(unittest.TestCase):
    def test_public_functions_have_complete_type_annotations(self):
        module = parse_build_module()
        functions = {
            node.name: node
            for node in module.body
            if isinstance(node, ast.FunctionDef) and node.name in TARGET_FUNCTIONS
        }

        self.assertGreaterEqual(len(functions), 10)
        missing = []
        for name, function in sorted(functions.items()):
            if function.returns is None:
                missing.append(f"{name}: missing return type")
            for arg in function.args.args:
                if arg.arg != "self" and arg.annotation is None:
                    missing.append(f"{name}: missing parameter type for {arg.arg}")

        self.assertEqual(missing, [])

    def test_build_py_does_not_use_any_type(self):
        module = parse_build_module()
        any_uses = [
            getattr(node, "lineno", "?")
            for node in ast.walk(module)
            if isinstance(node, ast.Name) and node.id == "Any"
        ]

        self.assertEqual(any_uses, [])

    def test_build_result_type_aliases_are_used_for_diagnostics(self):
        source = BUILD_PY.read_text(encoding="utf-8")

        self.assertIn("BuildResult = tuple", source)
        self.assertIn("DiagnosticReport = dict", source)
        self.assertIn("results: list[BuildResult]", source)


if __name__ == "__main__":
    unittest.main()
