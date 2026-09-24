---
name: implement
description: Implement a clear software task with proportionate evidence, optional checkpoints and review, and a trust-oriented handoff.
---

# Implement with Brigade

An explicit user invocation of `/implement` authorizes local implementation and review-fix checkpoint commits for the current task. It does not authorize branches, worktrees, pushes, merges, pull requests, or remote changes. If this skill was selected implicitly, do not infer commit authority.

## Before editing

Inspect Git status, project instructions, the requested behavior, existing documentation, and verification. Do not overwrite unrelated changes.

Silently assess intent, assurance, ownership, and whether checkpoints or independent review earn their cost. Surface a hidden decision before implementation. Use the abstraction checkpoint before adding a substantial maintained structure.

## Build and verify

Implement the smallest complete behavior. Use TDD when requested or when a red-green loop materially improves confidence. It is not the default for every change.

Gather evidence that would actually establish the result. Prefer direct behavior and observable output, then automated checks. Classify unexpected findings under the global contract and surface them at the appropriate time.

For substantial work with commit authority:

1. Stage only task-owned files and create an implementation checkpoint after initial evidence.
2. Run one independent review when STANDARD or HIGH assurance, uncertainty, or architectural importance warrants it.
3. Fix blocking and important findings.
4. Re-review those findings.
5. Create a review-fix checkpoint only when review caused meaningful changes.
6. Run final verification.

Skip ceremonial commits or review for small LIGHT work.

Finish with the trust handoff scaled to the task. Do not create Brigade-specific project artifacts.
