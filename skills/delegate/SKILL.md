---
name: delegate
description: Recommend and, only after explicit permission, dispatch one bounded coding worker through the 5stack worker control plane.
---

# Delegate bounded work

Use this skill when a separate coding agent would materially help with one bounded work unit. Do not delegate cheap deterministic inspection such as Git status, worktree listing, capability checks, or reading a small config file.

The primary remains the User's interface. A worker is disposable and belongs to one work unit. Never use a completed worker for unrelated work. Workers cannot dispatch other workers.

## Recommend before dispatch

Inspect the repository, current worktree occupancy, backend capability, task complexity, uncertainty, stakes, reversibility, implementation judgment, expected cost, and verification difficulty. Use `5stack worker recommend` when its deterministic profile selection helps present the result.

State the suggested configuration separately:

```text
Assurance: STANDARD
Ownership: DELEGATE

Suggested worker:
  backend: current/default
  harness: codex
  model: gpt-5.6-luna
  reasoning: medium

Reason: Localized implementation with straightforward verification.
```

The primary recommends. The User may accept, override the backend, harness, model, or reasoning, or decline delegation. A recommendation, a DELEGATE ownership label, a route result, or backend availability never authorizes dispatch.

Ask for explicit permission for every dispatch. After approval, preserve the exact selected configuration in the worker record. Do not silently replace a requested configuration when a backend cannot honor it. Surface the limitation instead.

## Write the brief

Give the worker a concise self-contained brief, not the primary transcript. Include only relevant context:

- Goal and completion criteria.
- Relevant files or existing project artifacts.
- Constraints, non-goals, and important paths not to touch.
- Assurance, ownership, selected configuration, and expected verification.
- Scope rule: handle MINOR adjacent implementation details when safe. Report MEANINGFUL findings. Stop for DECISION or CRITICAL findings.
- State that the worker cannot dispatch other workers and must not create Git commits, branches, pull requests, merges, or remote changes unless existing task authority explicitly permits them.

Reference existing specifications, issues, commits, or documentation instead of copying long material into the brief.

## Dispatch and supervise

Before dispatch, inspect `git worktree list`, active `5stack worker list` records, and backend capability. Do not permit two active writers in one worktree unless the User expressly overrides the protection.

Use the shared control plane:

```bash
5stack worker dispatch --approved --title "..." --brief-file /path/to/brief --profile codex-luna-medium
5stack worker list
5stack worker status <id> --refresh
5stack worker send <id> "Follow-up for this work unit"
5stack worker open <id>
5stack worker release <id>
5stack worker reconcile
5stack worker resolve-failed <id>
```

The `--approved` flag records the User's approval. It is not a substitute for asking first. The default `new` worktree is conservative. Explicitly selecting `current` or an existing worktree requires checking occupancy first. Use `--allow-shared-worktree` only when the User explicitly accepts concurrent writers, and state that override in the dispatch contract.

Use `resolve-failed` only for an `unverifiable` pre-launch record after confirming that no backend worker identifier was persisted. The command refuses records that could identify a launched worker and releases occupancy by marking only the rejected launch as failed.

Use `release` after a worker settles. For Orca, it closes the retained agent terminal while preserving archived output. For Herdr, it closes the worker pane, or the Workers tab when that pane is the last one. Releasing a worker does not remove its child worktree. Worktree removal remains a separate destructive action that requires explicit User authority.

Keep the primary usable. Do not block it on normal worker progress. Report completed, failed, blocked, disappeared, and decision-needed states to the User when reconciliation or native backend mail exposes them. A worker's completion report means only that the worker says implementation work is finished. It is not independent proof of correctness.

Workers may receive same-work-unit follow-up. They may not be steered into unrelated work. For a meaningful scope expansion or any product, behavior, policy, methodology, compatibility, or architecture decision, bring the decision back through the primary.

## Reconcile later sessions

At the start of a later primary session, run `5stack worker reconcile` and inspect any active or blocked records. Compare persisted state with the selected backend. Mark a missing backend session as disappeared rather than assuming success or failure.

Orca provides a durable run inbox and native worker state. Herdr provides native agent state. This v0 has no background watcher, so native UI plus reconcile deliver meaningful events without routine progress polling.
