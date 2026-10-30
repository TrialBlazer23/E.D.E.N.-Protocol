"""Tests for adopt vs new, EDEN merge markers, --tools/--legacy, hook-config merging, and command detection."""

import importlib.util
import json
import unittest
from pathlib import Path

from helpers import PROTOCOL_ROOT, audit, cleanup, make_repo, run

_spec = importlib.util.spec_from_file_location("eden_install", PROTOCOL_ROOT / "scripts/eden-install.py")
eden_install = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eden_install)

BEGIN, END = "<!-- EDEN:BEGIN v1 -->", "<!-- EDEN:END -->"


class InstallTestCase(unittest.TestCase):
    def setUp(self):
        self.repo = make_repo()

    def tearDown(self):
        cleanup(self.repo)

    def init(self, *args):
        return run(["bash", str(PROTOCOL_ROOT / "init-eden.sh"), *args], self.repo)

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, msg="base"):
        run(["git", "add", "-A"], self.repo)
        run(["git", "commit", "-q", "-m", msg], self.repo)

    def changelog(self):
        lines = (self.repo / ".eden/CHANGELOG_AGENT.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]


class ModeTests(InstallTestCase):
    def test_empty_repo_defaults_to_new(self):
        out = self.init().stdout
        self.assertIn("mode: new", out)
        self.assertEqual((self.repo / "AGENTS.md").read_bytes(), (PROTOCOL_ROOT / "AGENTS.md").read_bytes())
        self.assertEqual(self.changelog()[0]["task_id"], "TASK-00")

    def test_repo_with_commits_defaults_to_adopt(self):
        self.write("README.md", "hi\n")
        self.commit()
        out = self.init().stdout
        self.assertIn("mode: adopt", out)
        entry = self.changelog()[0]
        self.assertEqual(entry["task_id"], "EDEN-ADOPT")
        self.assertIn("EDEN-ADOPT", (self.repo / ".eden/PLAN.md").read_text(encoding="utf-8"))

    def test_changelog_lists_only_files_written(self):
        self.write("CLAUDE.md", "# Mine\n")
        self.write(".github/copilot-instructions.md", (PROTOCOL_ROOT / ".github/copilot-instructions.md").read_text())
        self.commit()
        self.init()
        files = self.changelog()[0]["files"]
        self.assertIn("CLAUDE.md", files)        # merged
        self.assertIn("AGENTS.md", files)        # written
        self.assertNotIn(".github/copilot-instructions.md", files)  # identical, untouched
        self.assertNotIn(".cursorrules", files)  # legacy files are opt-in
        self.assertFalse(any("pre-commit" in f for f in files))

    def test_rerun_is_a_no_op(self):
        self.write("AGENTS.md", "# Team rules\n\nUse tabs.\n")
        self.commit()
        self.init()
        before = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file() and ".git" not in p.parts}
        out = self.init().stdout
        after = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(before, after, out)
        self.assertEqual(len(self.changelog()), 1)


class MarkerTests(InstallTestCase):
    def test_adopt_keeps_text_outside_markers(self):
        self.write("AGENTS.md", "# Team rules\n\nUse tabs.\n")
        self.commit()
        self.init()
        text = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Team rules\n\nUse tabs.\n"))
        self.assertEqual(text.count(BEGIN), 1)
        self.assertEqual(text.count(END), 1)
        self.assertIn("## E.D.E.N. Protocol", text)
        self.assertIn("### Commands", text)  # headings demoted under the block heading

    def test_block_is_updated_in_place(self):
        self.write("AGENTS.md", f"# Team\n\nbefore\n\n{BEGIN}\nstale rules\n{END}\n\nafter\n")
        self.commit()
        self.init()
        text = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("stale rules", text)
        self.assertIn("before", text)
        self.assertTrue(text.rstrip().endswith("after"))
        self.assertEqual(text.count(BEGIN), 1)

    def test_crlf_files_stay_crlf(self):
        (self.repo / "AGENTS.md").write_bytes(b"# Team\r\n\r\nrules\r\n")
        self.commit()
        self.init()
        data = (self.repo / "AGENTS.md").read_bytes()
        self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))

    def test_unbalanced_markers_are_left_alone(self):
        self.write("AGENTS.md", f"# Team\n{BEGIN}\nno end\n")
        self.commit()
        self.init()
        self.assertEqual((self.repo / "AGENTS.md").read_text(encoding="utf-8"), f"# Team\n{BEGIN}\nno end\n")

    def test_force_replaces_with_backup(self):
        self.write("AGENTS.md", "# Team rules\n")
        self.commit()
        self.init("--force")
        self.assertEqual((self.repo / "AGENTS.md.eden-bak").read_text(encoding="utf-8"), "# Team rules\n")
        self.assertEqual((self.repo / "AGENTS.md").read_bytes(), (PROTOCOL_ROOT / "AGENTS.md").read_bytes())

    def test_merge_block_unit(self):
        body = eden_install.block_body("# Title\n\n## A\n```\n# not a heading\n```\n")
        self.assertIn("### A", body)
        self.assertIn("\n# not a heading\n", body)  # code fences are not demoted
        merged = eden_install.merge_block("x\n", body)
        self.assertEqual(eden_install.merge_block(merged, body), merged)


class ToolTests(InstallTestCase):
    def test_default_tools_and_no_legacy(self):
        self.init()
        for rel in ["GEMINI.md", ".cursor/rules/eden.mdc", ".github/copilot-instructions.md",
                    ".cursor/hooks.json", ".github/hooks/eden.json", ".agents/hooks.json",
                    ".agents/skills/eden-normalize/SKILL.md", "scripts/eden-hook.py"]:
            self.assertTrue((self.repo / rel).is_file(), rel)
        for rel in [".cursorrules", ".windsurfrules", "CLAUDE.md", ".grok", ".claude"]:
            self.assertFalse((self.repo / rel).exists(), rel)

    def test_tools_subset_and_legacy(self):
        self.init("--tools", "cursor", "--legacy")
        self.assertTrue((self.repo / ".cursor/hooks.json").is_file())
        self.assertTrue((self.repo / ".cursorrules").is_file())
        self.assertFalse((self.repo / "GEMINI.md").exists())
        self.assertFalse((self.repo / ".github/hooks/eden.json").exists())
        self.assertFalse((self.repo / ".agents/hooks.json").exists())

    def test_unknown_tool_fails(self):
        res = run(["bash", str(PROTOCOL_ROOT / "init-eden.sh"), "--tools", "emacs"], self.repo, check=False)
        self.assertNotEqual(res.returncode, 0)

    def test_existing_hook_config_is_merged_once(self):
        self.write(".cursor/hooks.json", '{"version": 1, "hooks": {"afterFileEdit": [{"command": "./fmt.sh"}]}}')
        self.commit()
        self.init()
        self.init()
        data = json.loads((self.repo / ".cursor/hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(data["hooks"]["afterFileEdit"], [{"command": "./fmt.sh"}])
        self.assertEqual(len(data["hooks"]["stop"]), 1)

    def test_hook_manager_skips_git_hook(self):
        (self.repo / ".husky").mkdir()
        out = self.init().stdout
        self.assertIn("Hook manager found", out)
        self.assertFalse((self.repo / ".git/hooks/pre-commit").exists())

    def test_hook_configs_are_valid_json(self):
        for rel in [".cursor/hooks.json", ".github/hooks/eden.json", ".agents/hooks.json"]:
            data = json.loads((PROTOCOL_ROOT / rel).read_text(encoding="utf-8"))
            self.assertIn("eden-hook.py", json.dumps(data))
        ag = json.loads((PROTOCOL_ROOT / ".agents/hooks.json").read_text(encoding="utf-8"))
        handlers = next(iter(ag.values()))["Stop"]
        self.assertIsInstance(handlers, list)  # flat handler list; a nested "hooks" key is discarded
        self.assertNotIn("hooks", handlers[0])


class DetectionTests(InstallTestCase):
    def test_node_with_pnpm(self):
        self.write("package.json", json.dumps({"scripts": {"build": "tsc", "test": "vitest run", "lint": "eslint ."}}))
        self.write("pnpm-lock.yaml", "")
        self.write("src/index.ts", "export const x = 1;\n")
        self.commit()
        self.init()
        agents = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("- Setup: `pnpm install --frozen-lockfile`", agents)
        self.assertIn("- Test: `pnpm run test`", agents)
        verify = (self.repo / ".eden/verify").read_text(encoding="utf-8")
        self.assertIn("pnpm run lint\npnpm run test\n", verify)

    def test_npm_default_test_is_ignored(self):
        self.write("package.json", json.dumps({"scripts": {"test": "echo \"Error: no test specified\" && exit 1"}}))
        self.assertNotIn("test", eden_install.detect_node(self.repo))

    def test_other_ecosystems(self):
        cases = [("Cargo.toml", "cargo test"), ("go.mod", "go test ./..."), ("gradlew", "./gradlew test")]
        for rel, test_cmd in cases:
            self.write(rel, "")
            self.assertEqual(eden_install.detect_commands(self.repo)["test"], test_cmd, rel)
            (self.repo / rel).unlink()
        self.write("pyproject.toml", "[tool.poetry]\n[tool.pytest.ini_options]\n")
        self.assertEqual(eden_install.detect_commands(self.repo)["test"], "poetry run pytest")

    def test_makefile_wins(self):
        self.write("Makefile", "test:\n\tgo test ./...\nlint:\n\tgolangci-lint run\n")
        self.write("go.mod", "")
        cmds = eden_install.detect_commands(self.repo)
        self.assertEqual(cmds["test"], "make test")
        self.assertEqual(cmds["build"], "go build ./...")

    def test_new_mode_skips_detection_unless_asked(self):
        self.write("go.mod", "")
        self.init("--new")
        self.assertIn("`<fill in>`", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertFalse((self.repo / ".eden/verify").exists())


class JavaRegistrationTests(InstallTestCase):
    def test_java_file_is_indexed_and_audited(self):
        self.write("src/main/java/com/x/App.java", "package com.x;\npublic class App {}\n")
        self.commit()
        self.init()
        registry = (self.repo / ".eden/REGISTRY.md").read_text(encoding="utf-8")
        self.assertIn("`src/main/java/com/x/App.java` | `App`", registry)
        self.assertNotIn("scripts/eden-audit.py", registry.split("## 2.", 1)[-1])  # E.D.E.N.'s own files
        self.commit("adopt")
        self.write("src/main/java/com/x/Util.java", "package com.x;\nclass Util {}\n")
        res = audit(self.repo)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Util.java", res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
