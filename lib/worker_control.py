"""Small, durable worker control plane for 5stack.

This module owns generic worker records and routes backend-specific operations
through adapters.  It deliberately does not schedule, retry, or clean up work.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_STATUSES = {"active", "blocked", "stopping", "unverifiable"}
TERMINAL_STATUSES = {"completed", "failed", "stopped", "disappeared"}
REASONING_LEVELS = {"low", "medium", "high", "xhigh", "max", "ultra"}

# Profiles are data, not backend behavior.  Add a model here without changing
# worker lifecycle code.  Models use the identifiers accepted by the Codex CLI.
PROFILES = {
    "codex-luna-medium": {
        "harness": "codex", "model": "gpt-5.6-luna", "reasoning": "medium",
        "description": "Localized work with straightforward verification.",
    },
    "codex-terra-high": {
        "harness": "codex", "model": "gpt-5.6-terra", "reasoning": "high",
        "description": "Higher implementation judgment or verification uncertainty.",
    },
}


class WorkerError(RuntimeError):
    pass


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def state_path() -> Path:
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    return root / "5stack" / "workers.json"


def load_state(path: Path | None = None) -> dict[str, Any]:
    path = path or state_path()
    if not path.exists():
        return {"version": 1, "workers": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise WorkerError(f"Worker state is not valid JSON: {path}") from error
    if value.get("version") != 1 or not isinstance(value.get("workers"), list):
        raise WorkerError(f"Worker state has an unsupported shape: {path}")
    return value


def save_state(state: dict[str, Any], path: Path | None = None) -> None:
    path = path or state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def find_worker(state: dict[str, Any], worker_id: str) -> dict[str, Any]:
    for worker in state["workers"]:
        if worker["id"] == worker_id:
            return worker
    raise WorkerError(f"Unknown worker: {worker_id}")


def event(worker: dict[str, Any], kind: str, detail: str, *, status: str | None = None) -> None:
    worker.setdefault("events", []).append({"at": now(), "kind": kind, "detail": detail})
    worker["updated_at"] = now()
    if status:
        worker["status"] = status


def run(command: list[str], *, cwd: str | None = None) -> Any:
    try:
        return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    except OSError as error:
        return subprocess.CompletedProcess(command, 127, "", str(error))


def require_ok(result: Any, description: str) -> str:
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise WorkerError(f"{description} failed: {detail or 'no output'}")
    return result.stdout


def json_output(command: list[str], description: str, *, cwd: str | None = None) -> dict[str, Any]:
    output = require_ok(run(command, cwd=cwd), description)
    try:
        value = json.loads(output)
    except json.JSONDecodeError as error:
        raise WorkerError(f"{description} did not return JSON: {output.strip()}") from error
    if value.get("ok") is False:
        raise WorkerError(f"{description} reported failure: {json.dumps(value)}")
    return value


def git_repository(cwd: str | None = None) -> dict[str, str]:
    root = require_ok(run(["git", "rev-parse", "--show-toplevel"], cwd=cwd), "Find repository").strip()
    common_dir = require_ok(run(["git", "rev-parse", "--git-common-dir"], cwd=root), "Find git common directory").strip()
    return {"path": str(Path(root).resolve()), "common_dir": str((Path(root) / common_dir).resolve())}


def git_worktrees(repository: str) -> set[str]:
    output = require_ok(run(["git", "worktree", "list", "--porcelain"], cwd=repository), "List Git worktrees")
    return {str(Path(line[9:]).resolve()) for line in output.splitlines() if line.startswith("worktree ")}


def canonical_worktree_path(path: str) -> str:
    # Orca may return a Windows path through its WSL bridge.  Keep that stable
    # rather than incorrectly treating it as a relative Linux path.
    if len(path) >= 3 and path[1:3] == ":\\":
        return path.lower()
    return str(Path(path).resolve())


def occupied_worktrees(state: dict[str, Any]) -> dict[str, str]:
    return {
        canonical_worktree_path(worker["worktree"]["path"]): worker["id"]
        for worker in state["workers"]
        if worker.get("status") in ACTIVE_STATUSES and worker.get("worktree", {}).get("path")
    }


def assert_available_worktree(state: dict[str, Any], path: str, *, exclude: str | None = None) -> None:
    occupier = occupied_worktrees(state).get(canonical_worktree_path(path))
    if occupier and occupier != exclude:
        raise WorkerError(f"Worktree is occupied by active worker {occupier}: {path}")


def new_worktree_path(repository: dict[str, str], worker_id: str) -> Path:
    token = hashlib.sha256(repository["common_dir"].encode()).hexdigest()[:12]
    return state_path().parent / "worktrees" / token / worker_id


def create_worktree(repository: dict[str, str], worker_id: str) -> str:
    path = new_worktree_path(repository, worker_id)
    if path.exists():
        raise WorkerError(f"Refusing to reuse existing worker worktree: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    require_ok(run(["git", "worktree", "add", "--detach", str(path), "HEAD"], cwd=repository["path"]), "Create worker worktree")
    return str(path.resolve())


def short_model(model: str) -> str:
    return model.removeprefix("gpt-5.6-")


def choose_profile(
    assurance: str,
    complexity: str = "low",
    uncertainty: str = "low",
    verification: str = "straightforward",
    judgment: str = "low",
) -> dict[str, str]:
    values = {"low": 0, "straightforward": 0, "moderate": 1, "high": 2, "hard": 2}
    assurance_score = {"LIGHT": 0, "STANDARD": 1, "HIGH": 2}.get(assurance.upper())
    if assurance_score is None:
        raise WorkerError("Assurance must be LIGHT, STANDARD, or HIGH")
    factors = [values.get(complexity), values.get(uncertainty), values.get(verification), values.get(judgment)]
    if any(value is None for value in factors):
        raise WorkerError("Complexity, uncertainty, verification, and judgment must be low, moderate, high, straightforward, or hard")
    score = assurance_score + sum(factors)
    profile_name = "codex-terra-high" if score >= 5 or assurance_score == 2 else "codex-luna-medium"
    profile = dict(PROFILES[profile_name])
    profile["name"] = profile_name
    profile["reason"] = profile["description"]
    return profile


def resolved_configuration(backend: str, harness: str, model: str, reasoning: str, profile: str | None) -> dict[str, str | None]:
    if harness != "codex":
        raise WorkerError(f"Harness is not supported in v0: {harness}")
    if reasoning not in REASONING_LEVELS:
        raise WorkerError(f"Unsupported reasoning level: {reasoning}")
    return {"backend": backend, "harness": harness, "model": model, "reasoning": reasoning, "profile": profile}


def orca_cli_command() -> str | None:
    """Follow Orca's version-matched CLI resolution without using Linux `orca`."""
    configured = os.environ.get("ORCA_CLI_COMMAND")
    if configured:
        return configured
    if os.environ.get("ORCA_DEV_REPO_ROOT") and shutil.which("orca-dev"):
        return "orca-dev"
    if platform.system() == "Linux":
        return "orca-ide" if shutil.which("orca-ide") else None
    return "orca" if shutil.which("orca") else None


def discover_backend(requested: str) -> str:
    if requested not in {"auto", "orca", "herdr"}:
        raise WorkerError("Backend must be auto, orca, or herdr")
    capabilities = capability_report()
    orca = capabilities["orca"]["available"]
    herdr = capabilities["herdr"]["available"]
    if requested == "orca":
        if not orca:
            raise WorkerError("Orca is unavailable here. Run inside Orca with its managed CLI available.")
        return "orca"
    if requested == "herdr":
        if not herdr:
            raise WorkerError("Herdr is unavailable here. Run inside a Herdr-managed pane.")
        return "herdr"
    inside_orca = bool(os.environ.get("ORCA_TERMINAL_HANDLE") or os.environ.get("ORCA_PANE_KEY"))
    inside_herdr = os.environ.get("HERDR_ENV") == "1"
    if inside_orca and orca:
        return "orca"
    if inside_herdr and herdr:
        return "herdr"
    if orca:
        return "orca"
    if herdr:
        return "herdr"
    raise WorkerError("No supported worker backend is usable. Start inside Orca or Herdr, or select one explicitly.")


def capability_report() -> dict[str, dict[str, Any]]:
    orca_command = orca_cli_command()
    orca_available = False
    orca_reason = "requires the version-matched Orca CLI and a ready runtime"
    if orca_command:
        result = run([orca_command, "status", "--json"])
        try:
            status = json.loads(result.stdout) if result.returncode == 0 else {}
        except json.JSONDecodeError:
            status = {}
        orca_available = bool(status.get("ok") and nested(status, "reachable") is True)
        orca_reason = "Orca runtime is ready" if orca_available else "Orca CLI is present, but its runtime is not ready"
    herdr_context = os.environ.get("HERDR_ENV") == "1" and shutil.which("herdr") is not None
    herdr_available = False
    herdr_reason = "requires HERDR_ENV=1 and the herdr CLI"
    if herdr_context:
        result = run(["herdr", "status"])
        herdr_available = result.returncode == 0
        herdr_reason = "Herdr-managed pane and CLI found" if herdr_available else "Herdr context exists, but its session is not ready"
    return {
        "orca": {
            "available": orca_available,
            "reason": orca_reason,
        },
        "herdr": {
            "available": herdr_available,
            "reason": herdr_reason,
        },
    }


def nested(value: Any, *names: str) -> Any:
    """Find the first matching key in a backend response without coupling to its full schema."""
    if isinstance(value, dict):
        for name in names:
            if value.get(name) is not None:
                return value[name]
        for child in value.values():
            found = nested(child, *names)
            if found is not None:
                return found
    if isinstance(value, list):
        for child in value:
            found = nested(child, *names)
            if found is not None:
                return found
    return None


def text_value(value: Any, *names: str) -> str | None:
    found = nested(value, *names)
    return found if isinstance(found, str) else None


def named_object(value: Any, *names: str) -> dict[str, Any] | None:
    if isinstance(value, dict):
        for name in names:
            candidate = value.get(name)
            if isinstance(candidate, dict):
                return candidate
        for child in value.values():
            found = named_object(child, *names)
            if found is not None:
                return found
    if isinstance(value, list):
        for child in value:
            found = named_object(child, *names)
            if found is not None:
                return found
    return None


def dispatch_matches(row: Any, dispatch_id: str) -> bool:
    if not isinstance(row, dict):
        return False
    if row.get("dispatch_id") == dispatch_id or row.get("dispatchId") == dispatch_id:
        return True
    dispatch = row.get("dispatch")
    return isinstance(dispatch, dict) and dispatch.get("id") == dispatch_id


def lifecycle_state(row: dict[str, Any]) -> str | None:
    task = row.get("task")
    values = [row.get("task_status"), row.get("taskStatus")]
    if isinstance(task, dict):
        values.extend([task.get("status"), task.get("state")])
    for value in values:
        if isinstance(value, str):
            return value.lower()
    return None


def run_has_worker_escalation(value: Any, worker: dict[str, Any]) -> bool:
    encoded = json.dumps(value)
    identifiers = [worker["backend_session"].get("dispatch_id"), worker["backend_session"].get("task_id")]
    return any(identifier and identifier in encoded for identifier in identifiers) and any(
        marker in encoded for marker in ('"type": "escalation"', '"type": "question"', '"type": "decision_gate"')
    )


def effective_launch_configuration(value: Any) -> dict[str, str] | None:
    launch = named_object(value, "launch")
    effective = (launch or {}).get("effective")
    if not isinstance(effective, dict):
        return None
    model = effective.get("model") or effective.get("modelId")
    reasoning = effective.get("effort") or effective.get("reasoning")
    if not isinstance(model, str) or not isinstance(reasoning, str):
        return None
    return {"model": model, "reasoning": reasoning}


@dataclass
class LaunchResult:
    session: dict[str, Any]
    worktree: str


class Backend:
    name: str

    def launch(self, worker: dict[str, Any], worktree_mode: str, persist=None) -> LaunchResult:
        raise NotImplementedError

    def inspect(self, worker: dict[str, Any]) -> tuple[str, str]:
        raise NotImplementedError

    def send(self, worker: dict[str, Any], message: str) -> str:
        raise NotImplementedError

    def open(self, worker: dict[str, Any]) -> str:
        raise NotImplementedError

    def stop(self, worker: dict[str, Any]) -> str:
        raise NotImplementedError

    def read(self, worker: dict[str, Any]) -> str:
        raise NotImplementedError


class OrcaBackend(Backend):
    name = "orca"

    def command(self) -> str:
        command = orca_cli_command()
        if not command:
            raise WorkerError("Orca CLI is not available through its documented resolution")
        return command

    def call(self, arguments: list[str], description: str) -> dict[str, Any]:
        return json_output([self.command(), *arguments, "--json"], description)

    def launch(self, worker: dict[str, Any], worktree_mode: str, persist=None) -> LaunchResult:
        config = worker["configuration"]
        run_response = self.call(["orchestration", "run-current"], "Inspect Orca run")
        run = named_object(run_response, "run")
        if not run or not isinstance(run.get("id"), str):
            run_response = self.call(["orchestration", "run-create", "--objective", f"5stack worker: {worker['task']['title']}"], "Create Orca run")
            run = named_object(run_response, "run")
        run_id = run.get("id") if run else None
        if not isinstance(run_id, str):
            raise WorkerError("Orca did not return a durable Run identifier")
        worker["backend_session"] = {"run_id": run_id, "launch_started": True}
        if persist:
            persist()
        selected_worktree = "new-child" if worktree_mode == "new" else ("current" if worker["worktree"]["kind"] == "current" else f"path:{worker['worktree']['path']}")
        arguments = [
            "orchestration", "worker-start", "--spec", worker["brief"], "--task-title", worker["task"]["title"],
            "--worktree", selected_worktree, "--run", run_id,
            "--agent", config["harness"], "--model", config["model"], "--effort", config["reasoning"],
        ]
        response = self.call(arguments, "Launch Orca worker")
        dispatch = named_object(response, "dispatch")
        dispatch_id = text_value(response, "dispatchId", "dispatch_id") or (dispatch or {}).get("id")
        if not dispatch_id:
            raise WorkerError("Orca did not return a dispatch identifier")
        worktree = named_object(response, "worktree")
        actual_worktree = text_value(response, "worktreePath") or (worktree or {}).get("path") or worker["worktree"]["path"]
        terminal_id = text_value(response, "terminalHandle", "terminal_id", "terminal")
        task = named_object(response, "task")
        task_id = (task or {}).get("id")
        session = {"dispatch_id": dispatch_id, "task_id": task_id, "terminal_id": terminal_id, "run_id": run_id, "launch_started": True}
        worker["backend_session"] = session
        effective = effective_launch_configuration(response)
        if effective:
            worker["effective_configuration"] = effective
        else:
            worker["effective_configuration"] = None
        if persist:
            persist()
        if not effective:
            raise WorkerError("Orca did not confirm the effective model and reasoning configuration")
        if effective and (effective["model"] != config["model"] or effective["reasoning"] != config["reasoning"]):
            raise WorkerError(f"Orca launched a different configuration: requested {config['model']} / {config['reasoning']}, effective {effective['model']} / {effective['reasoning']}")
        return LaunchResult(session, actual_worktree)

    def inspect(self, worker: dict[str, Any]) -> tuple[str, str]:
        dispatch_id = worker["backend_session"].get("dispatch_id")
        if not isinstance(dispatch_id, str):
            return "unverifiable", "Orca launch began but no Dispatch identifier was persisted."
        try:
            response = self.call(["orchestration", "worker-show", "--dispatch", dispatch_id], "Inspect Orca worker")
        except WorkerError as error:
            return "unverifiable", f"Cannot inspect Orca worker: {error}"
        if nested(response, "agentWait", "agent_wait") is not None:
            return "blocked", "Orca observed the worker waiting for a human answer."
        run_id = worker["backend_session"].get("run_id")
        if not run_id:
            return "unverifiable", "Worker has no persisted Orca Run identifier."
        try:
            mailbox = self.call(["orchestration", "check", "--run", run_id, "--peek", "--types", "escalation,question,decision_gate"], "Check Orca worker mailbox")
            if run_has_worker_escalation(mailbox, worker):
                return "blocked", "Orca Run has an escalation or decision request from this worker."
        except WorkerError:
            # Lifecycle truth comes from worker-list. An unreadable mailbox
            # must not turn a healthy worker into a synthetic disappearance.
            pass
        cursor = None
        row = None
        for _ in range(100):
            arguments = ["orchestration", "worker-list", "--run", run_id]
            if cursor:
                arguments.extend(["--cursor", cursor])
            try:
                listing = self.call(arguments, "List Orca worker lifecycle")
            except WorkerError as error:
                return "unverifiable", f"Cannot list Orca worker lifecycle: {error}"
            rows = nested(listing, "workers")
            if not isinstance(rows, list):
                return "unverifiable", "Orca returned no worker lifecycle rows."
            row = next((candidate for candidate in rows if dispatch_matches(candidate, dispatch_id)), None)
            if row is not None:
                break
            page = named_object(listing, "page")
            cursor = (page or {}).get("nextCursor") or text_value(listing, "nextCursor")
            if not isinstance(cursor, str) or not cursor:
                break
        if row is None:
            return "disappeared", "Orca Run is reachable but no longer lists this Dispatch."
        state = lifecycle_state(row)
        if not state:
            return "unverifiable", "Orca lists the worker but did not expose a task lifecycle state."
        mapping = {"succeeded": "completed", "success": "completed", "done": "completed", "completed": "completed", "failed": "failed", "blocked": "blocked", "stopped": "stopped", "active": "active", "working": "active", "running": "active", "pending": "active", "queued": "active", "unverifiable": "unverifiable"}
        return mapping.get(state, "unverifiable"), f"Orca reports task {state}."

    def send(self, worker: dict[str, Any], message: str) -> str:
        dispatch_id = worker["backend_session"]["dispatch_id"]
        self.call(["orchestration", "send", "--to", f"dispatch:{dispatch_id}", "--subject", "5stack follow-up", "--body", message, "--type", "status"], "Send Orca worker message")
        return "Follow-up delivered through Orca orchestration mail."

    def open(self, worker: dict[str, Any]) -> str:
        terminal = worker["backend_session"].get("terminal_id")
        if not terminal:
            raise WorkerError("Orca did not expose a terminal for this worker. Open it from Orca's worker view.")
        self.call(["terminal", "switch", "--terminal", terminal], "Focus Orca worker")
        return "Focused Orca worker terminal."

    def stop(self, worker: dict[str, Any]) -> str:
        self.call(["orchestration", "worker-stop", "--dispatch", worker["backend_session"]["dispatch_id"]], "Stop Orca worker")
        return "Orca fenced and stopped the supervised worker."

    def read(self, worker: dict[str, Any]) -> str:
        response = self.call(["orchestration", "worker-read", "--dispatch", worker["backend_session"]["dispatch_id"], "--source", "auto", "--limit", "120"], "Read Orca worker handoff")
        return json.dumps(response.get("result", response), ensure_ascii=False)[:12000]


class HerdrBackend(Backend):
    name = "herdr"

    def call(self, arguments: list[str], description: str) -> dict[str, Any]:
        return json_output(["herdr", *arguments], description)

    def launch(self, worker: dict[str, Any], worktree_mode: str, persist=None) -> LaunchResult:
        # Herdr owns the visible pane and agent.  5stack selected the worktree
        # before this call, so no worker can move itself elsewhere.
        pane = self.call(["pane", "split", "--current", "--direction", "right", "--cwd", worker["worktree"]["path"], "--no-focus"], "Create Herdr worker pane")
        pane_id = text_value(pane, "pane_id", "paneId", "id")
        if not pane_id:
            raise WorkerError("Herdr did not return a pane identifier")
        name = f"worker-{worker['id'].replace('w_', '')[:20]}"
        worker["backend_session"] = {"agent_name": name, "pane_id": pane_id, "agent_started": False, "agent_start_attempted": False}
        if persist:
            persist()
        config = worker["configuration"]
        worker["backend_session"]["agent_start_attempted"] = True
        if persist:
            persist()
        self.call(["agent", "start", name, "--kind", "codex", "--pane", pane_id, "--", "--model", config["model"], "-c", f'model_reasoning_effort="{config["reasoning"]}"'], "Start Herdr worker")
        worker["backend_session"]["agent_started"] = True
        if persist:
            persist()
        self.call(["agent", "prompt", name, worker["brief"]], "Send Herdr worker brief")
        return LaunchResult({"agent_name": name, "pane_id": pane_id}, worker["worktree"]["path"])

    def inspect(self, worker: dict[str, Any]) -> tuple[str, str]:
        name = worker["backend_session"]["agent_name"]
        try:
            response = self.call(["agent", "get", name], "Inspect Herdr worker")
        except WorkerError as error:
            return "disappeared", str(error)
        state = (text_value(response, "state", "status") or "unknown").lower()
        mapping = {"done": "completed", "idle": "active", "working": "active", "blocked": "blocked", "unknown": "active"}
        return mapping.get(state, "active"), f"Herdr reports {state}"

    def send(self, worker: dict[str, Any], message: str) -> str:
        self.call(["agent", "prompt", worker["backend_session"]["agent_name"], message], "Send Herdr worker follow-up")
        return "Follow-up submitted to the Herdr agent."

    def open(self, worker: dict[str, Any]) -> str:
        self.call(["agent", "focus", worker["backend_session"]["agent_name"]], "Focus Herdr worker")
        return "Focused Herdr worker pane."

    def stop(self, worker: dict[str, Any]) -> str:
        self.call(["agent", "send-keys", worker["backend_session"]["agent_name"], "ctrl+c"], "Interrupt Herdr worker")
        return "Sent Ctrl+C to the Herdr worker. Reconcile to confirm its settled state."

    def read(self, worker: dict[str, Any]) -> str:
        response = self.call(["agent", "read", worker["backend_session"]["agent_name"], "--source", "recent-unwrapped", "--lines", "120"], "Read Herdr worker handoff")
        return json.dumps(response.get("result", response), ensure_ascii=False)[:12000]


def backend_for(name: str) -> Backend:
    if name == "orca":
        return OrcaBackend()
    if name == "herdr":
        return HerdrBackend()
    raise WorkerError(f"Unsupported backend: {name}")


def new_worker(title: str, brief: str, configuration: dict[str, str | None], repository: dict[str, str], worktree: str, worktree_kind: str) -> dict[str, Any]:
    worker_id = "w_" + uuid.uuid4().hex[:12]
    created = now()
    return {
        "id": worker_id,
        "task": {"id": worker_id, "title": title},
        "brief": brief,
        "configuration": configuration,
        "repository": repository,
        "worktree": {"path": worktree, "kind": worktree_kind},
        "backend_session": {},
        "status": "active",
        "events": [{"at": created, "kind": "dispatched", "detail": "Worker record created."}],
        "handoff": None,
        "created_at": created,
        "updated_at": created,
    }


def reconcile_worker(worker: dict[str, Any]) -> tuple[str, str]:
    backend = backend_for(worker["configuration"]["backend"])
    status, detail = backend.inspect(worker)
    if status != worker["status"]:
        event(worker, "reconciled", detail, status=status)
    else:
        worker["updated_at"] = now()
    if status in TERMINAL_STATUSES and status != "disappeared":
        try:
            output = backend.read(worker)
        except WorkerError as error:
            output = f"Handoff output unavailable: {error}"
        worker["handoff"] = {"at": now(), "status": status, "summary": detail, "output": output}
    return status, detail


def handoff(worker: dict[str, Any]) -> str:
    session = worker.get("backend_session", {})
    return json.dumps({"worker": worker["id"], "status": worker["status"], "worktree": worker["worktree"]["path"], "backend": worker["configuration"]["backend"], "session": session, "events": worker.get("events", [])[-3:]}, indent=2)
