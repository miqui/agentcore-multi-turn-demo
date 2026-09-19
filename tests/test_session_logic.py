"""Offline unit tests for session_logic.py.

Pure stdlib unittest, no network, no AWS, no SDK imports -- runnable in
any Python 3 environment.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from session_logic import (  # noqa: E402
    SessionState,
    SessionStore,
    parse_invocation_payload,
)


class SessionStateTests(unittest.TestCase):
    def test_record_turn_increments_counter_and_history(self):
        state = SessionState(session_id="s1")
        state.record_turn("hello")
        state.record_turn("world")

        self.assertEqual(state.turn_count, 2)
        self.assertEqual(state.history, ["hello", "world"])


class SessionStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = SessionStore()

    def test_handle_turn_creates_session_on_first_call(self):
        resp = self.store.handle_turn("abc", "hi")
        self.assertEqual(resp["session_id"], "abc")
        self.assertEqual(resp["turn_count"], 1)
        self.assertEqual(resp["echo"], "hi")
        self.assertEqual(resp["history"], ["hi"])
        self.assertEqual(self.store.session_count(), 1)

    def test_handle_turn_persists_across_multiple_invocations(self):
        self.store.handle_turn("abc", "turn one")
        second = self.store.handle_turn("abc", "turn two")

        self.assertEqual(second["turn_count"], 2)
        self.assertEqual(second["history"], ["turn one", "turn two"])
        self.assertEqual(self.store.session_count(), 1)

    def test_distinct_session_ids_are_isolated(self):
        self.store.handle_turn("session-a", "hello a")
        self.store.handle_turn("session-b", "hello b")
        resp_a = self.store.handle_turn("session-a", "again a")

        self.assertEqual(resp_a["turn_count"], 2)
        self.assertEqual(self.store.session_count(), 2)

    def test_handle_turn_rejects_empty_session_id(self):
        with self.assertRaises(ValueError):
            self.store.handle_turn("", "hi")

    def test_handle_turn_rejects_none_message(self):
        with self.assertRaises(ValueError):
            self.store.handle_turn("abc", None)

    def test_reset_removes_session(self):
        self.store.handle_turn("abc", "hi")
        self.store.reset("abc")
        self.assertEqual(self.store.session_count(), 0)

        # A new turn after reset starts the counter over.
        resp = self.store.handle_turn("abc", "hi again")
        self.assertEqual(resp["turn_count"], 1)


class ParseInvocationPayloadTests(unittest.TestCase):
    def test_parses_prompt_and_session_id(self):
        session_id, message = parse_invocation_payload(
            {"prompt": "hello", "session_id": "abc-123"}
        )
        self.assertEqual(session_id, "abc-123")
        self.assertEqual(message, "hello")

    def test_accepts_input_alias_and_runtime_session_id_alias(self):
        session_id, message = parse_invocation_payload(
            {"input": "hi", "runtimeSessionId": "rt-1"}
        )
        self.assertEqual(session_id, "rt-1")
        self.assertEqual(message, "hi")

    def test_raises_on_missing_message(self):
        with self.assertRaises(ValueError):
            parse_invocation_payload({"session_id": "abc"})

    def test_raises_on_missing_session_id(self):
        with self.assertRaises(ValueError):
            parse_invocation_payload({"prompt": "hi"})

    def test_raises_on_non_dict_payload(self):
        with self.assertRaises(TypeError):
            parse_invocation_payload("not-a-dict")


if __name__ == "__main__":
    unittest.main()
