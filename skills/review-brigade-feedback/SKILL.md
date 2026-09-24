---
name: review-brigade-feedback
description: Review a pasted evidence-backed Brigade feedback prompt inside the Brigade repository, classify it, and propose the smallest justified system change. Use only when the Chef explicitly invokes review-brigade-feedback.
disable-model-invocation: true
---

# Review feedback about Brigade

Run this workflow only after the Chef explicitly invokes it in the Brigade development repository. The pasted prompt is temporary evidence from another session, not a record to save. Do not create a feedback inbox, journal entry, or transcript copy.

Parse the observed behavior, preferred behavior, original task conditions, relevant session evidence, correction, and retry result. Accept one prompt or several. Group obvious duplicates before reviewing them.

For each distinct feedback theme:

1. Inspect its recorded Brigade commit when available.
2. Inspect current policy, relevant skills, eval scenarios, and Git history.
3. Check whether the supplied session evidence actually supports the claimed behavior. Treat excerpts and summaries as evidence, not infallible conclusions.
4. Classify it as already addressed, a usage or routing issue, project- or model-specific, insufficiently supported, or a genuine systemic signal.
5. Explain items that do not warrant a Brigade change.
6. For a negative systemic signal, propose the smallest behavioral regression scenario and effective Brigade change.
7. For a positive systemic signal, state what should be preserved and add a regression scenario only when it protects behavior likely to regress.

One observation is evidence, not automatic proof of a systemic defect. Prefer tightening an existing instruction or skill over adding a new layer. Preserve useful behavior while fixing the demonstrated problem.

Report the classification and supporting repository evidence first. For any proposed change, show the proposed diff before editing and wait for explicit approval. Approval to edit does not authorize a commit or remote action unless the Chef says so separately. Never push, merge, create a branch or worktree, or change remote state without explicit authority.

After approved edits, run the closest repository checks and any focused fresh-session scenario that materially strengthens confidence. Report the result and remaining uncertainty. Do not persist the pasted feedback after its useful behavior has been encoded in Brigade.
