"""Smoke tests for scripts/eden-hook.py: caller detection, per-tool replies, and the round cap."""

import json
import os
import sys
import unittest

from helpers import cleanup, init_repo, run

PAYLOADS = {
    "cursor": {"status": "completed", "loop_count": 0, "conversation_id": "c1", "cursor_version": "2.0"},
    "grok": {"hookEventName": "Stop", "stopHookActive": False, "sessionId": "g1", "reason": "end_turn"},
    "copilot": {"sessionId": "p1", "stopReason": "end_turn", "stop_hook_active": False},
    "antigravity": {"executionNum": 1, "terminationReason": "model_stop", "fullyIdle": True,
                    "conversationId": "a1"},
}


def is_block(tool, reply):
    if tool == "cursor":
        return "followup_message" in reply
    if tool == "antigravity":
        return reply.get("decision") == "continue"
    return reply.get("decision") == "block"


class HookTests(unittest.TestCase):
    def setUp(self):
        self.repo = init_repo()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("GROK_", "EDEN_HOOK"))}

    def tearDown(self):
        cleanup(self.repo)

    def hook(self, payload, *args, env=None):
        res = run([sys.executable, "scripts/eden-hook.py", *args], self.repo, check=False,
                  input=json.dumps(payload), env=env or self.env)
        self.assertEqual(res.returncode, 0, res.stderr)
        return json.loads(res.stdout)

    def test_clean_tree_allows_every_tool(self):
        for tool, payload in PAYLOADS.items():
            self.assertFalse(is_block(tool, self.hook(payload)), tool)

    def test_unregistered_change_blocks_in_each_format(self):
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        for tool, payload in PAYLOADS.items():
            reply = self.hook(payload)
            self.assertTrue(is_block(tool, reply), f"{tool}: {reply}")
            self.assertIn("app.py", json.dumps(reply))

    def test_round_cap(self):
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        first = dict(PAYLOADS["grok"])
        again = dict(first, stopHookActive=True)
        self.assertTrue(is_block("grok", self.hook(first)))
        self.assertTrue(is_block("grok", self.hook(again)))
        self.assertFalse(is_block("grok", self.hook(again)))  # cap reached: let the agent report
        self.assertTrue(is_block("grok", self.hook(first)))   # a new user turn resets the budget

    def test_non_completion_stops_are_ignored(self):
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        self.assertEqual(self.hook(dict(PAYLOADS["cursor"], status="aborted")), {})
        self.assertEqual(self.hook(dict(PAYLOADS["grok"], reason="shutdown")), {})
        self.assertEqual(self.hook(dict(PAYLOADS["grok"], subagentType="explore")), {})

    def test_disable_and_bad_input_fail_open(self):
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        self.assertEqual(self.hook(PAYLOADS["cursor"], env=dict(self.env, EDEN_HOOK_DISABLE="1")), {})
        res = run([sys.executable, "scripts/eden-hook.py"], self.repo, check=False, input="not json")
        self.assertEqual(res.returncode, 0)
        self.assertEqual(json.loads(res.stdout), {})

    def test_grok_env_detection(self):
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        reply = self.hook({"sessionId": "e1"}, env=dict(self.env, GROK_HOOK_EVENT="Stop"))
        self.assertEqual(reply.get("decision"), "block")


if __name__ == "__main__":
    unittest.main()
