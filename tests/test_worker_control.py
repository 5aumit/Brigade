from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock
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
            "id": "w_test", "brief": "bounded brief", "task": {"title": "Test worker"},
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

    def test_orca_new_child_has_deterministic_name(self):
        worker = {
            "id": "w_abc123", "brief": "bounded brief", "task": {"title": "Test worker"},
            "configuration": {"harness": "codex", "model": "gpt-5.6-luna", "reasoning": "medium"},
            "worktree": {"path": "/repo", "kind": "backend-child"},
        }
        backend = control.OrcaBackend()
        calls = []
        replies = iter([
            {"ok": True, "result": {"run": {"id": "run_123"}}},
            {"ok": True, "result": {"dispatch": {"id": "dispatch_123"}, "launch": {"effective": {"model": "gpt-5.6-luna", "effort": "medium"}}}},
        ])
        backend.call = lambda arguments, _description: calls.append(arguments) or next(replies)
        backend.launch(worker, "new")
        self.assertIn("new-child", calls[-1])
        self.assertEqual(calls[-1][calls[-1].index("--name") + 1], "5stack-abc123")

    def test_orca_existing_worktree_uses_identity_from_its_directory(self):
        backend = control.OrcaBackend()
        calls = []

        def call(arguments, _description, *, cwd=None):
            calls.append((arguments, cwd))
            return {"result": {"worktree": {"identity": {"key": "wt2:local:123"}}}}

        backend.call = call
        self.assertEqual(backend.existing_worktree_selector("/mnt/d/repo/task"), "identity:wt2:local:123")
        self.assertEqual(calls, [(["worktree", "current"], "/mnt/d/repo/task")])

    def test_orca_explicit_prelaunch_rejection_is_not_uncertain(self):
        payload = {"ok": False, "error": {"code": "invalid_argument"}, "effects": [], "residualResources": []}
        self.assertFalse(control.orca_failure_may_have_resources(payload))
        error = control.LaunchRejected("rejected", resources_may_exist=False)
        worker = {"backend_session": {"run_id": "run_123"}}
        self.assertFalse(control.launch_failure_is_uncertain(worker, error))

    def test_orca_ambiguous_rejection_remains_uncertain(self):
        self.assertTrue(control.orca_failure_may_have_resources({"ok": False}))
        error = control.LaunchRejected("unknown", resources_may_exist=True)
        self.assertTrue(control.launch_failure_is_uncertain({"backend_session": {}}, error))

    def test_resolve_failed_launch_releases_occupancy(self):
        worker = self.worker(status="unverifiable")
        worker["backend_session"] = {"run_id": "run_123", "launch_started": True}
        state = {"version": 1, "workers": [worker]}
        with self.assertRaises(control.WorkerError):
            control.assert_available_worktree(state, "/repo/task")
        control.resolve_failed_launch(worker)
        control.assert_available_worktree(state, "/repo/task")
        self.assertEqual(worker["status"], "failed")

    def test_resolve_failed_launch_rejects_persisted_dispatch(self):
        worker = self.worker(status="unverifiable")
        worker["backend_session"] = {"dispatch_id": "dispatch_123"}
        with self.assertRaisesRegex(control.WorkerError, "persisted backend resource"):
            control.resolve_failed_launch(worker)

    def test_orca_reconcile_uses_task_lifecycle_not_terminal_state(self):
        backend = control.OrcaBackend()
        worker = {"backend_session": {"dispatch_id": "dispatch_123", "task_id": "task_123", "run_id": "run_123"}}
        replies = iter([
            {"ok": True, "result": {"observation": {"agentWait": None}, "status": "active"}},
            {"ok": True, "result": {"messages": []}},
            {"ok": True, "result": {"workers": [{"dispatch": {"id": "dispatch_123"}, "task": {"status": "succeeded"}}]}},
        ])
        backend.call = lambda _arguments, _description: next(replies)
        self.assertEqual(backend.inspect(worker), ("completed", "Orca reports worker lifecycle succeeded."))

    def test_orca_reconcile_recognizes_operator_stopped_worker(self):
        backend = control.OrcaBackend()
        worker = {"backend_session": {"dispatch_id": "dispatch_123", "run_id": "run_123"}}
        backend.call = lambda _arguments, _description: {
            "result": {
                "dispatch": {"id": "dispatch_123", "status": "failed", "lastFailure": "stopped"},
                "worker": {"state": "stopped"},
            }
        }
        self.assertEqual(backend.inspect(worker), ("stopped", "Orca reports that the worker was stopped."))

    def test_orca_worker_list_fields_are_lifecycle_inputs(self):
        self.assertEqual(control.lifecycle_state({"workerState": "running", "dispatchStatus": "pending"}), "running")

    def test_orca_release_targets_exact_dispatch(self):
        backend = control.OrcaBackend()
        calls = []
        backend.call = lambda arguments, _description: calls.append(arguments) or {"result": {"state": "released"}}
        detail = backend.release({"backend_session": {"dispatch_id": "dispatch_123"}})
        self.assertEqual(calls, [["orchestration", "worker-release", "--dispatch", "dispatch_123"]])
        self.assertIn("child worktree remains", detail)

    def test_orca_release_reports_retained_terminal(self):
        backend = control.OrcaBackend()
        backend.call = lambda _arguments, _description: {"result": {"state": "retained", "reason": "user_takeover"}}
        with self.assertRaisesRegex(control.WorkerError, "retained \\(user_takeover\\)"):
            backend.release({"backend_session": {"dispatch_id": "dispatch_123"}})

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
        worker = {"id": "w_abc", "task": {"title": "Check dispatch"}, "worktree": {"path": "/repo"}, "configuration": {"model": "gpt-5.6-luna", "reasoning": "medium"}}
        snapshots = []
        calls = []
        replies = iter([
            {"id": "cli:tab:list", "result": {"tabs": []}},
            {"id": "cli:tab:create", "result": {"tab": {"tab_id": "w1:t2"}, "root_pane": {"pane_id": "w1:p2"}}},
            control.WorkerError("start failed"),
        ])

        def call(arguments, _description):
            calls.append(arguments)
            reply = next(replies)
            if isinstance(reply, Exception):
                raise reply
            return reply

        backend.call = call
        with mock.patch.dict(os.environ, {"HERDR_WORKSPACE_ID": "w1"}):
            with self.assertRaisesRegex(control.WorkerError, "start failed"):
                backend.launch(worker, "new", lambda: snapshots.append(dict(worker["backend_session"])))
        self.assertEqual(calls[1], ["tab", "create", "--workspace", "w1", "--label", "Workers", "--cwd", "/repo", "--no-focus"])
        self.assertEqual(snapshots, [
            {"agent_name": "w-check-dispatch-abc", "tab_id": "w1:t2", "pane_id": "w1:p2", "agent_started": False, "agent_start_attempted": False},
            {"agent_name": "w-check-dispatch-abc", "tab_id": "w1:t2", "pane_id": "w1:p2", "agent_started": False, "agent_start_attempted": True},
        ])

    def test_herdr_reuses_workers_tab_and_nested_pane_id(self):
        backend = control.HerdrBackend()
        worker = {"id": "w_def", "task": {"title": "60 second test"}, "brief": "Check", "worktree": {"path": "/repo"}, "configuration": {"model": "gpt-5.6-luna", "reasoning": "medium"}}
        calls = []
        replies = iter([
            {"id": "cli:tab:list", "result": {"tabs": [{"label": "Workers", "tab_id": "w1:t2", "workspace_id": "w1"}]}},
            {"id": "cli:pane:list", "result": {"panes": [{"pane_id": "w1:p2", "tab_id": "w1:t2"}]}},
            {"id": "cli:pane:split", "result": {"pane": {"pane_id": "w1:p3"}}},
            {"result": {}}, {"result": {}},
        ])
        backend.call = lambda arguments, _description: calls.append(arguments) or next(replies)
        with mock.patch.dict(os.environ, {"HERDR_WORKSPACE_ID": "w1"}):
            backend.launch(worker, "current")
        self.assertEqual(calls[2], ["pane", "split", "w1:p2", "--direction", "right", "--cwd", "/repo", "--no-focus"])
        self.assertEqual(calls[3][:6], ["agent", "start", "w-60-second-test-def", "--kind", "codex", "--pane"])
        self.assertEqual(calls[3][6], "w1:p3")
        self.assertIn("gpt-5.6-luna", calls[3])

    def test_herdr_inspect_nested_status_after_stop(self):
        backend = control.HerdrBackend()
        worker = {"status": "active", "backend_session": {"agent_name": "w-check-abc"}}
        backend.call = lambda _arguments, _description: {"id": "cli:agent:get", "result": {"agent": {"agent_status": "working"}}}
        self.assertEqual(backend.inspect(worker), ("active", "Herdr reports working"))
        backend.call = lambda _arguments, _description: {"id": "cli:agent:get", "result": {"agent": {"agent_status": "idle"}}}
        self.assertEqual(backend.inspect(worker), ("completed", "Herdr reports idle"))
        worker["status"] = "stopping"
        backend.call = lambda _arguments, _description: {"id": "cli:agent:get", "result": {"agent": {"agent_status": "idle"}}}
        self.assertEqual(backend.inspect(worker), ("stopped", "Herdr reports idle after interruption"))

    def test_herdr_read_preserves_plain_text(self):
        backend = control.HerdrBackend()
        output = "Worker finished.\nNo files changed.\n"
        with mock.patch.object(control, "run", return_value=control.subprocess.CompletedProcess([], 0, output, "")) as run:
            self.assertEqual(backend.read({"backend_session": {"agent_name": "w-check-abc"}}), output)
        run.assert_called_once_with(["herdr", "agent", "read", "w-check-abc", "--source", "recent-unwrapped", "--lines", "120"])

    def test_herdr_open_targets_agent_focus(self):
        backend = control.HerdrBackend()
        calls = []
        backend.call = lambda arguments, _description: calls.append(arguments) or {"result": {}}
        backend.open({"backend_session": {"agent_name": "worker-abc", "pane_id": "w1:p2"}})
        self.assertEqual(calls, [["agent", "focus", "worker-abc"]])

    def test_herdr_release_closes_only_worker_pane_when_tab_is_shared(self):
        backend = control.HerdrBackend()
        calls = []
        replies = iter([
            {"result": {"panes": [
                {"pane_id": "w1:p2", "tab_id": "w1:t2"},
                {"pane_id": "w1:p3", "tab_id": "w1:t2"},
            ]}},
            {"result": {"agents": [{"pane_id": "w1:p2", "name": "worker-abc"}]}},
            {"result": {}},
        ])
        backend.call = lambda arguments, _description: calls.append(arguments) or next(replies)
        detail = backend.release({"backend_session": {"agent_name": "worker-abc", "pane_id": "w1:p2", "tab_id": "w1:t2"}})
        self.assertEqual(calls, [["pane", "list", "--workspace", "w1"], ["agent", "list"], ["pane", "close", "w1:p2"]])
        self.assertIn("worker pane", detail)

    def test_herdr_release_closes_last_worker_pane_with_tab(self):
        backend = control.HerdrBackend()
        calls = []
        replies = iter([
            {"result": {"panes": [{"pane_id": "w1:p2", "tab_id": "w1:t2"}]}},
            {"result": {"agents": [{"pane_id": "w1:p2", "name": "worker-abc"}]}},
            {"result": {"tabs": [{"tab_id": "w1:t2", "label": "Workers"}]}},
            {"result": {}},
        ])
        backend.call = lambda arguments, _description: calls.append(arguments) or next(replies)
        backend.release({"backend_session": {"agent_name": "worker-abc", "pane_id": "w1:p2", "tab_id": "w1:t2"}})
        self.assertEqual(calls[-1], ["tab", "close", "w1:t2"])

    def test_herdr_release_rejects_repurposed_pane(self):
        backend = control.HerdrBackend()
        replies = iter([
            {"result": {"panes": [{"pane_id": "w1:p2", "tab_id": "w1:t2"}]}},
            {"result": {"agents": [{"pane_id": "w1:p2", "name": "someone-else"}]}},
        ])
        backend.call = lambda _arguments, _description: next(replies)
        with self.assertRaisesRegex(control.WorkerError, "no longer contains"):
            backend.release({"backend_session": {"agent_name": "worker-abc", "pane_id": "w1:p2", "tab_id": "w1:t2"}})

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
