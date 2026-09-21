from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import worker_control as control


class WorkerControlTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.state = Path(self.temporary.name) / "state" / "workers.json"

    def tearDown(self):
        self.temporary.cleanup()

    def worker(self, worker_id="w_one", path="/repo/task", status="active"):
        return {"id": worker_id, "status": status, "worktree": {"path": path}, "events": [], "updated_at": "now"}

    def test_state_round_trip(self):
        value = {"version": 1, "workers": [self.worker()]}
        control.save_state(value, self.state)
        self.assertEqual(control.load_state(self.state), value)
        self.assertEqual(json.loads(self.state.read_text())["version"], 1)

    def test_occupancy_blocks_only_active_writer(self):
        state = {"version": 1, "workers": [self.worker()]}
        with self.assertRaisesRegex(control.WorkerError, "w_one"):
            control.assert_available_worktree(state, "/repo/task")
        state["workers"][0]["status"] = "completed"
        control.assert_available_worktree(state, "/repo/task")

    def test_profile_selection_considers_multiple_factors(self):
        simple = control.choose_profile("STANDARD", "low", "low", "straightforward", "low")
        difficult = control.choose_profile("STANDARD", "high", "high", "hard", "high")
        self.assertEqual(simple["name"], "codex-luna-medium")
        self.assertEqual(difficult["name"], "codex-terra-high")
        self.assertEqual(difficult["reasoning"], "high")

    def test_configuration_preserves_selected_values(self):
        config = control.resolved_configuration("orca", "codex", "gpt-5.6-terra", "high", "codex-terra-high")
        self.assertEqual(config, {"backend": "orca", "harness": "codex", "model": "gpt-5.6-terra", "reasoning": "high", "profile": "codex-terra-high"})

    def test_capabilities_are_optional(self):
        original = {key: os.environ.get(key) for key in ("ORCA_CLI_COMMAND", "ORCA_TERMINAL_HANDLE", "HERDR_ENV")}
        original_orca_command = control.orca_cli_command
        try:
            for key in original:
                os.environ.pop(key, None)
            control.orca_cli_command = lambda: None
            capabilities = control.capability_report()
            self.assertFalse(capabilities["orca"]["available"])
            self.assertFalse(capabilities["herdr"]["available"])
        finally:
            control.orca_cli_command = original_orca_command
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_reconcile_persists_terminal_change(self):
        worker = self.worker()
        worker["configuration"] = {"backend": "orca"}
        original = control.backend_for

        class Finished:
            def inspect(self, _worker):
                return "completed", "test backend reports completion"

            def read(self, _worker):
                return "worker handoff"

        control.backend_for = lambda _name: Finished()
        try:
            status, detail = control.reconcile_worker(worker)
        finally:
            control.backend_for = original
        self.assertEqual(status, "completed")
        self.assertEqual(detail, "test backend reports completion")
        self.assertEqual(worker["status"], "completed")
        self.assertEqual(worker["handoff"]["output"], "worker handoff")

    def test_windows_orca_worktree_path_stays_stable(self):
        self.assertEqual(
            control.canonical_worktree_path(r"D:\tech_stuff\worker"),
            r"d:\tech_stuff\worker",
        )

    def test_orca_launch_uses_durable_run_and_dispatch_identifier(self):
        worker = {
            "brief": "bounded brief", "task": {"title": "Test worker"},
            "configuration": {"harness": "codex", "model": "gpt-5.6-luna", "reasoning": "medium"},
            "worktree": {"path": "/repo", "kind": "current"},
        }
        backend = control.OrcaBackend()
        calls = []
        replies = iter([
            {"id": "request-one", "ok": True, "result": {"run": None}},
            {"id": "request-two", "ok": True, "result": {"run": {"id": "run_123"}}},
            {"id": "request-three", "ok": True, "result": {"dispatch": {"id": "dispatch_123"}, "task": {"id": "task_123"}, "worktree": {"path": "/repo"}, "terminalHandle": "term_123", "launch": {"effective": {"model": "gpt-5.6-luna", "effort": "medium"}}}},
        ])
        backend.call = lambda arguments, _description: calls.append(arguments) or next(replies)
        result = backend.launch(worker, "current")
        self.assertEqual(result.session, {"dispatch_id": "dispatch_123", "task_id": "task_123", "terminal_id": "term_123", "run_id": "run_123", "launch_started": True})
        self.assertIn(["orchestration", "run-create", "--objective", "5stack worker: Test worker"], calls)
        self.assertIn("--run", calls[-1])
        self.assertIn("run_123", calls[-1])

    def test_orca_reconcile_uses_task_lifecycle_not_terminal_state(self):
        backend = control.OrcaBackend()
        worker = {"backend_session": {"dispatch_id": "dispatch_123", "task_id": "task_123", "run_id": "run_123"}}
        replies = iter([
            {"ok": True, "result": {"observation": {"agentWait": None}, "status": "active"}},
            {"ok": True, "result": {"messages": []}},
            {"ok": True, "result": {"workers": [{"dispatch": {"id": "dispatch_123"}, "task": {"status": "succeeded"}}]}},
        ])
        backend.call = lambda _arguments, _description: next(replies)
        self.assertEqual(backend.inspect(worker), ("completed", "Orca reports task succeeded."))

    def test_orca_backend_failure_is_unverifiable_not_disappeared(self):
        backend = control.OrcaBackend()
        backend.call = lambda _arguments, _description: (_ for _ in ()).throw(control.WorkerError("runtime down"))
        worker = {"backend_session": {"dispatch_id": "dispatch_123", "run_id": "run_123"}}
        self.assertEqual(backend.inspect(worker)[0], "unverifiable")

    def test_orca_reconcile_follows_worker_list_pages(self):
        backend = control.OrcaBackend()
        worker = {"backend_session": {"dispatch_id": "dispatch_123", "task_id": "task_123", "run_id": "run_123"}}
        calls = []
        replies = iter([
            {"ok": True, "result": {"observation": {"agentWait": None}}},
            {"ok": True, "result": {"messages": []}},
            {"ok": True, "result": {"workers": [{"dispatch": {"id": "other"}, "task": {"status": "running"}}], "page": {"nextCursor": "next"}}},
            {"ok": True, "result": {"workers": [{"dispatch": {"id": "dispatch_123"}, "task": {"status": "failed"}}], "page": {"nextCursor": None}}},
        ])
        backend.call = lambda arguments, _description: calls.append(arguments) or next(replies)
        self.assertEqual(backend.inspect(worker)[0], "failed")
        self.assertIn(["orchestration", "worker-list", "--run", "run_123", "--cursor", "next"], calls)

    def test_orca_effective_configuration_mismatch_is_persisted_and_reported(self):
        backend = control.OrcaBackend()
        worker = {
            "brief": "bounded brief", "task": {"title": "Test worker"},
            "configuration": {"harness": "codex", "model": "gpt-5.6-terra", "reasoning": "high"},
            "worktree": {"path": "/repo", "kind": "current"},
        }
        replies = iter([
            {"ok": True, "result": {"run": {"id": "run_123"}}},
            {"ok": True, "result": {"dispatch": {"id": "dispatch_123"}, "task": {"id": "task_123"}, "launch": {"effective": {"model": "gpt-5.6-luna", "effort": "medium"}}}},
        ])
        backend.call = lambda _arguments, _description: next(replies)
        snapshots = []
        with self.assertRaisesRegex(control.WorkerError, "different configuration"):
            backend.launch(worker, "current", lambda: snapshots.append(dict(worker["backend_session"])))
        self.assertEqual(worker["effective_configuration"], {"model": "gpt-5.6-luna", "reasoning": "medium"})
        self.assertEqual(snapshots[-1]["dispatch_id"], "dispatch_123")

    def test_orca_missing_effective_configuration_is_unconfirmed(self):
        backend = control.OrcaBackend()
        worker = {
            "brief": "bounded brief", "task": {"title": "Test worker"},
            "configuration": {"harness": "codex", "model": "gpt-5.6-luna", "reasoning": "medium"},
            "worktree": {"path": "/repo", "kind": "current"},
        }
        replies = iter([
            {"ok": True, "result": {"run": {"id": "run_123"}}},
            {"ok": True, "result": {"dispatch": {"id": "dispatch_123"}, "task": {"id": "task_123"}}},
        ])
        backend.call = lambda _arguments, _description: next(replies)
        with self.assertRaisesRegex(control.WorkerError, "did not confirm"):
            backend.launch(worker, "current", lambda: None)
        self.assertIsNone(worker["effective_configuration"])

    def test_herdr_launch_persists_pane_before_agent_start(self):
        backend = control.HerdrBackend()
        worker = {"id": "w_abc", "worktree": {"path": "/repo"}, "configuration": {"model": "gpt-5.6-luna", "reasoning": "medium"}}
        snapshots = []
        replies = iter([{"result": {"pane": {"pane_id": "w1:p2"}}}, control.WorkerError("start failed")])

        def call(_arguments, _description):
            reply = next(replies)
            if isinstance(reply, Exception):
                raise reply
            return reply

        backend.call = call
        with self.assertRaisesRegex(control.WorkerError, "start failed"):
            backend.launch(worker, "new", lambda: snapshots.append(dict(worker["backend_session"])))
        self.assertEqual(snapshots, [
            {"agent_name": "worker-abc", "pane_id": "w1:p2", "agent_started": False, "agent_start_attempted": False},
            {"agent_name": "worker-abc", "pane_id": "w1:p2", "agent_started": False, "agent_start_attempted": True},
        ])

    def test_herdr_open_targets_agent_focus(self):
        backend = control.HerdrBackend()
        calls = []
        backend.call = lambda arguments, _description: calls.append(arguments) or {"result": {}}
        backend.open({"backend_session": {"agent_name": "worker-abc", "pane_id": "w1:p2"}})
        self.assertEqual(calls, [["agent", "focus", "worker-abc"]])

    def test_orca_linux_resolution_avoids_bare_orca(self):
        previous_command = os.environ.pop("ORCA_CLI_COMMAND", None)
        previous_dev = os.environ.pop("ORCA_DEV_REPO_ROOT", None)
        original_which, original_system = control.shutil.which, control.platform.system
        control.shutil.which = lambda name: "/tmp/orca-ide" if name == "orca-ide" else None
        control.platform.system = lambda: "Linux"
        try:
            self.assertEqual(control.orca_cli_command(), "orca-ide")
        finally:
            control.shutil.which, control.platform.system = original_which, original_system
            if previous_command is not None:
                os.environ["ORCA_CLI_COMMAND"] = previous_command
            if previous_dev is not None:
                os.environ["ORCA_DEV_REPO_ROOT"] = previous_dev

    def test_auto_backend_prefers_herdr_inside_herdr(self):
        original_report = control.capability_report
        original_herdr = os.environ.get("HERDR_ENV")
        original_orca = os.environ.pop("ORCA_TERMINAL_HANDLE", None)
        original_orca_pane = os.environ.pop("ORCA_PANE_KEY", None)
        control.capability_report = lambda: {"orca": {"available": True}, "herdr": {"available": True}}
        os.environ["HERDR_ENV"] = "1"
        try:
            self.assertEqual(control.discover_backend("auto"), "herdr")
        finally:
            control.capability_report = original_report
            if original_herdr is None:
                os.environ.pop("HERDR_ENV", None)
            else:
                os.environ["HERDR_ENV"] = original_herdr
            if original_orca is not None:
                os.environ["ORCA_TERMINAL_HANDLE"] = original_orca
            if original_orca_pane is not None:
                os.environ["ORCA_PANE_KEY"] = original_orca_pane


if __name__ == "__main__":
    unittest.main()
