"""Smoke tests for init-eden.sh and the single-source-of-truth rule."""

import shutil
import unittest

from helpers import PROTOCOL_ROOT, cleanup, make_repo, run

POINTERS = ["CLAUDE.md", "GEMINI.md", ".cursorrules", ".windsurfrules",
            ".cursor/rules/eden.mdc", ".github/copilot-instructions.md"]
DEFAULT_POINTERS = ["GEMINI.md", ".cursor/rules/eden.mdc", ".github/copilot-instructions.md"]


class InitTests(unittest.TestCase):
    def setUp(self):
        self.repo = make_repo()

    def tearDown(self):
        cleanup(self.repo)

    def init(self, *args):
        return run(["bash", str(PROTOCOL_ROOT / "init-eden.sh"), *args], self.repo)

    def test_fresh_repo_can_commit(self):
        self.init()
        self.assertTrue((self.repo / "scripts/eden-audit.py").is_file())
        self.assertTrue((self.repo / "scripts/eden-index.py").is_file())
        run(["git", "add", "-A"], self.repo)
        res = run(["git", "commit", "-q", "-m", "init"], self.repo, check=False)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertNotIn("can't open file", res.stdout + res.stderr)

    def test_generated_files_match_committed_sources(self):
        self.init("--tools", "antigravity,cursor,grok,vscode,claude", "--legacy")
        for rel in ["AGENTS.md"] + POINTERS:
            self.assertEqual((self.repo / rel).read_bytes(), (PROTOCOL_ROOT / rel).read_bytes(), rel)

    def test_existing_files_are_kept_without_force(self):
        (self.repo / "CLAUDE.md").write_text("mine\n", encoding="utf-8")
        hook = self.repo / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
        self.init()
        # Instruction files get an EDEN block appended; the user's text is kept.
        self.assertTrue((self.repo / "CLAUDE.md").read_text(encoding="utf-8").startswith("mine\n"))
        self.assertIn("custom", hook.read_text(encoding="utf-8"))

    def test_generated_ps1_matches_sh(self):
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if not pwsh:
            self.skipTest("PowerShell not installed")
        other = make_repo()
        try:
            self.init()
            run([pwsh, "-NoProfile", "-File", str(PROTOCOL_ROOT / "init-eden.ps1"), str(other)], other)
            for rel in ["AGENTS.md", ".cursor/hooks.json", ".agents/hooks.json"] + DEFAULT_POINTERS:
                self.assertEqual((other / rel).read_bytes(), (self.repo / rel).read_bytes(), rel)
        finally:
            cleanup(other)

    def test_force_backs_up(self):
        (self.repo / "CLAUDE.md").write_text("mine\n", encoding="utf-8")
        self.init("--force")
        self.assertEqual((self.repo / "CLAUDE.md.eden-bak").read_text(encoding="utf-8"), "mine\n")
        self.assertEqual((self.repo / "CLAUDE.md").read_bytes(), (PROTOCOL_ROOT / "CLAUDE.md").read_bytes())

    def test_force_keeps_project_state(self):
        self.init()
        plan = self.repo / ".eden/PLAN.md"
        plan.write_text("# PLAN\nmine\n", encoding="utf-8")
        self.init("--force")
        self.assertEqual(plan.read_text(encoding="utf-8"), "# PLAN\nmine\n")


class EncodingTests(unittest.TestCase):
    def test_agent_files_are_ascii_without_bom(self):
        for rel in ["AGENTS.md", "init-eden.ps1"] + POINTERS + [
                ".agents/skills/eden-normalize/SKILL.md", ".agents/skills/eden-architect/SKILL.md",
                ".agents/skills/eden-adopt/SKILL.md"]:
            data = (PROTOCOL_ROOT / rel).read_bytes()
            self.assertFalse(data.startswith(b"\xef\xbb\xbf"), f"{rel} has a BOM")
            data.decode("ascii")  # raises if non-ASCII crept in

    def test_learnings_template_has_no_live_facts(self):
        text = (PROTOCOL_ROOT / "templates/eden/LEARNINGS.md").read_text(encoding="utf-8")
        body = text.split("-->", 1)[-1]
        self.assertNotIn("- [20", body)


if __name__ == "__main__":
    unittest.main()
