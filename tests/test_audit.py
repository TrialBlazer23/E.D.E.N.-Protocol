"""Regression tests for scripts/eden-audit.py bypasses (stdlib unittest; run: python3 -m unittest)."""

import os
import subprocess
import sys
import unittest

from helpers import audit, cleanup, init_repo, log_change, register, run


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.repo = init_repo()

    def tearDown(self):
        cleanup(self.repo)

    def write(self, rel, text="x = 1\n"):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_clean_scaffold_passes(self):
        self.assertEqual(audit(self.repo).returncode, 0)

    def test_file_in_new_untracked_dir_is_seen(self):
        self.write("src/pkg/mod.py")
        res = audit(self.repo)
        self.assertEqual(res.returncode, 1)
        self.assertIn("UNREGISTERED FILE: `src/pkg/mod.py`", res.stdout)

    def test_html_comment_does_not_register(self):
        self.write("src/mod.py")
        with open(self.repo / ".eden/REGISTRY.md", "a", encoding="utf-8") as fh:
            fh.write("\n<!-- | `src/mod.py` | fake | fake | fake | -->\n")
        log_change(self.repo, ["src/mod.py"])
        res = audit(self.repo)
        self.assertEqual(res.returncode, 1)
        self.assertIn("UNREGISTERED FILE: `src/mod.py`", res.stdout)

    def test_substring_does_not_register(self):
        self.write("src/mod.py")
        with open(self.repo / ".eden/REGISTRY.md", "a", encoding="utf-8") as fh:
            fh.write("\nSee src/mod.py for details.\n| `src/mod.pyc` | - | - | - |\n")
        log_change(self.repo, ["src/mod.py"])
        self.assertIn("UNREGISTERED FILE", audit(self.repo).stdout)

    def test_touching_other_eden_file_is_not_a_log_entry(self):
        self.write("src/mod.py")
        register(self.repo, "src/mod.py")
        with open(self.repo / ".eden/PLAN.md", "a", encoding="utf-8") as fh:
            fh.write("- [x] did a thing\n")
        res = audit(self.repo)
        self.assertEqual(res.returncode, 1)
        self.assertIn("MISSING AUDIT LOG", res.stdout)

    def test_log_entry_must_cover_changed_files(self):
        self.write("src/mod.py")
        register(self.repo, "src/mod.py")
        log_change(self.repo, ["src/other.py"])
        res = audit(self.repo)
        self.assertEqual(res.returncode, 1)
        self.assertIn("INCOMPLETE AUDIT LOG", res.stdout)

    def test_registered_and_logged_passes(self):
        self.write("src/mod.py")
        register(self.repo, "src/mod.py")
        log_change(self.repo, ["src/mod.py"])
        res = audit(self.repo)
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_rewriting_changelog_history_fails(self):
        self.write("src/mod.py")
        register(self.repo, "src/mod.py")
        log = self.repo / ".eden/CHANGELOG_AGENT.jsonl"
        log.write_text(log.read_text(encoding="utf-8").replace("Initialized", "Rewrote"), encoding="utf-8")
        log_change(self.repo, ["src/mod.py"])
        self.assertIn("CHANGELOG REWRITTEN", audit(self.repo).stdout)

    def test_staged_ignores_unstaged_and_needs_staged_log(self):
        self.write("src/mod.py")
        register(self.repo, "src/mod.py")
        log_change(self.repo, ["src/mod.py"])
        self.assertEqual(audit(self.repo, "--staged").returncode, 0)  # nothing staged yet
        run(["git", "add", "src/mod.py"], self.repo)
        res = audit(self.repo, "--staged")
        self.assertEqual(res.returncode, 1)  # .eden updates exist only in the working tree
        run(["git", "add", ".eden"], self.repo)
        self.assertEqual(audit(self.repo, "--staged").returncode, 0)

    def test_hook_blocks_bad_commit(self):
        self.write("src/mod.py")
        run(["git", "add", "-A"], self.repo)
        res = run(["git", "commit", "-q", "-m", "bad"], self.repo, check=False)
        self.assertNotEqual(res.returncode, 0)
        self.assertNotIn("can't open file", res.stderr + res.stdout)

    def test_base_mode_checks_committed_changes(self):
        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], self.repo).stdout.strip()
        run(["git", "checkout", "-q", "-b", "feature"], self.repo)
        self.write("src/mod.py")
        run(["git", "add", "-A"], self.repo)
        run(["git", "commit", "-q", "--no-verify", "-m", "sneaky"], self.repo)
        res = audit(self.repo, "--base", branch)
        self.assertEqual(res.returncode, 1)
        self.assertIn("src/mod.py", res.stdout)

    def test_banned_import(self):
        self.write("src/mod.py", "import requests\n")
        register(self.repo, "src/mod.py")
        reg = self.repo / ".eden/REGISTRY.md"
        reg.write_text(reg.read_text(encoding="utf-8").replace(
            "| Prefer before adding dependencies |", "| Prefer before adding dependencies. BANNED: requests |"),
            encoding="utf-8")
        log_change(self.repo, ["src/mod.py"])
        self.assertIn("BANNED DEPENDENCY", audit(self.repo).stdout)

    def test_verify_runs_when_present(self):
        verify = self.repo / ".eden/verify.py"
        verify.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
        self.assertEqual(audit(self.repo).returncode, 0)  # verify only runs on request
        res = audit(self.repo, "--verify")
        self.assertEqual(res.returncode, 1)
        self.assertIn("VERIFY FAILED", res.stdout)
        verify.write_text("print('ok')\n", encoding="utf-8")
        self.assertEqual(audit(self.repo, "--verify").returncode, 0)

    def test_verify_env_var(self):
        (self.repo / ".eden/verify.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
        env = dict(os.environ, EDEN_VERIFY="1")
        res = subprocess.run([sys.executable, "scripts/eden-audit.py"], cwd=self.repo, env=env,
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)


if __name__ == "__main__":
    unittest.main()
