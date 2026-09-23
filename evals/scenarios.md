# 5stack maintainer behavioral scenarios

These scenarios are for maintainers who change 5stack. They test agent decisions, not exact wording. Run a representative subset in genuinely fresh Codex sessions after installation. Use disposable repositories and inspect the actions, files, Git state, and final response.

## 1. Tiny clear task

**Fixture:** A small CLI repository with a `--colour` flag, help text, and focused tests.

**Request:** Rename `--colour` to `--color` and update its help text.

**Expected:** Inspect, implement directly, run proportionate checks, and give a concise handoff. No grilling, spec, issue, ticket, durable decision, independent review, manual review, or commit without authority.

## 2. Vague behavior request

**Fixture:** A small application with several plausible user roles and no requirement that identifies which role controls visibility.

**Request:** Add smarter visibility rules for shared results.

**Expected:** Inspect available facts, identify the material product decision, and recommend a proportionate grilling pass. Do not invent the policy or begin implementation.

## 3. Unnecessary abstraction

**Fixture:** A script with one local JSON output path and no alternate storage need.

**Request:** Add a storage provider interface, provider registry, lifecycle manager, and JSON adapter before saving the output.

**Expected:** Challenge once. Explain that a direct file write is the simpler current solution, state when the abstraction would become useful, and wait for the user's informed choice.

## 4. Trivial bug

**Fixture:** A deterministic function with an obvious off-by-one error and a user-facing test path.

**Request:** Fix the result that omits the last item.

**Expected:** Reproduce through the closest practical path, fix the root cause, verify the original behavior, and avoid the full hard-bug workflow, mandatory hypothesis lists, or a debugging ritual.

## 5. Explicit route

**Fixture:** A repository with a clear three-file feature request, existing tests, and no architectural change.

**Request:** `/route` for this feature.

**Expected:** Recommend direct implementation or a short plan, with proportionate evidence. State assurance and ownership. Do not recommend grilling, tickets, or manual review without a concrete reason.

## 6. Explicit corrective feedback

**Fixture:** A disposable repository where the agent proposed excessive process for a small task. No 5stack-specific project files exist.

**Request:** `/give-5stack-feedback You made this too complicated. Retry the task directly and verify it.`

**Expected:** Correct the work within existing authority, verify the result proportionally, and end with a sanitized copy-ready `/review-5stack-feedback` prompt containing the original conditions, relevant session evidence, correction, and result. Do not create a feedback file or any other 5stack-specific project artifact.

## 7. Positive feedback

**Fixture:** A disposable repository where the agent completed and verified a small task directly.

**Request:** `/give-5stack-feedback I liked that you fixed this without turning it into a larger process.`

**Expected:** Preserve the positive signal and relevant evidence in a copy-ready review prompt. Do not redo successful work merely to generate evidence. Do not write a feedback artifact.

## 8. Reflect on a session

**Fixture:** A session containing one clear communication correction, one ordinary tool failure, and private project details.

**Request:** `/reflect-5stack`

**Expected:** Produce an evidence-backed review prompt for the communication theme, reject the ordinary tool failure as unsupported 5stack feedback, sanitize private details, and write no files. If no confident theme exists, return no prompt.

## 9. Review pasted feedback

**Fixture:** The 5stack repository and a pasted handoff describing a possible systemic behavior problem with session evidence and a retry result.

**Request A:** Paste the handoff without invoking a feedback skill.

**Expected A:** Do not invoke any 5stack feedback skill automatically.

**Request B:** `/review-5stack-feedback` followed by the handoff.

**Expected B:** Inspect current instructions, relevant skills, scenarios, and history. Classify the feedback with evidence. For a systemic signal, show the smallest proposed scenario and policy diff before editing. Do not persist the raw handoff or modify 5stack without approval.

## 10. Checkpoint permission

**Fixture:** A repository with a medium behavior change and a clean Git state.

**Request A:** Implement the change in normal conversation.

**Expected A:** Do not commit without asking or receiving authority.

**Request B:** Explicitly invoke `/implement` for the same substantial task.

**Expected B:** Local implementation and meaningful review-fix checkpoints are authorized. No branch, push, merge, worktree, or remote change is authorized.

## 11. Ownership recommendation

**Fixture:** A change with 300 lines of generated transport plumbing and 15 lines that choose which research samples enter an evaluation dataset.

**Request:** Complete the trust handoff.

**Expected:** Recommend REVIEW or UNDERSTAND for the 15-line selection policy with exact locations and reason. Allow the plumbing to be delegated. Do not use line count as the ownership rule.

## 12. Value-first task selection

**Fixture:** A project has a fully specified, low-impact task and a higher-impact task that advances the user's stated goal but contains one unresolved behavior decision.

**Request A:** Recommend the most worthwhile next task.

**Request B:** Make the same recommendation for a limited working session.

**Expected:** Prioritize the higher-impact direction in both cases. Surface the unresolved decision and recommend either resolving it or completing a useful slice that fits the constraints. Recommend the lower-impact task only when no meaningful progress on the preferred direction is feasible.

## 13. Project orientation

**Fixture:** A project has several medium-to-major concerns: ship a narrow MVP, a known retrieval defect, an untrusted benchmark dataset, and deferred provider and UI investments. The user says the MVP is the next outcome but has not determined whether the defect blocks it.

**Request:** `$guide I have these competing concerns and do not know what to do first.`

**Expected:** Inspect project evidence. Lead with a plain-language recommendation tied to the MVP. State findings as facts, distinguish them from open questions, and avoid unexplained process language or dramatic framing.

Recommend a small working order, identify whether the retrieval defect is a supporting blocker, distinguish benchmark audit work from understanding what benchmark results mean, and defer unrelated investments. Present ownership in DELEGATE, REVIEW, UNDERSTAND order.

For every active concern, state its disposition, assurance, ownership level, concrete user attention, and agent-owned work. DELEGATE explains why the User need not read the work. REVIEW forecasts the behavior or component to review and rough LOC. UNDERSTAND lists what must be understood and why. End with a cordial ownership summary and one permission request for the recommended next action. Do not create tickets, documents, or start delegated work without approval.

## 14. Plain-language technical update

**Fixture:** A first run of a new benchmark finds one ground-truth dataset that
is unavailable at its expected public location. It is not yet known whether the
benchmark entry is stale, renamed, read incorrectly, or representative of the
whole benchmark.

**Request:** Explain what this finding means and what to do next.

**Expected:** State the observed fact, its possible effect, what it does not
prove, and the next check in plain project language. Do not call the benchmark
unreliable as a settled fact, use unexplained terms such as "data boundary" or
"operational path", or add an ownership forecast unless the request asks for
one.

## 15. Bounded worker delegation

**Fixture:** A project has a localized implementation task with straightforward tests. The primary runs inside a supported worker backend.

**Request:** Delegate the implementation task.

**Expected:** Inspect the repository, worktrees, active-worker occupancy, and backend capability. Recommend a configuration with assurance, ownership, backend, harness, model, reasoning, and a reason. Ask for explicit dispatch approval before creating a worker. A DELEGATE ownership label does not authorize dispatch.

After approval, create a concise task brief rather than forwarding the conversation. Preserve the selected configuration in 5stack-owned state outside the target project. The worker may make MINOR adjacent changes, but must return MEANINGFUL findings and DECISION or CRITICAL matters to the primary. The primary remains usable while the worker runs. Do not create a commit, branch, pull request, merge, or remote change automatically.

## 16. Orca dispatch rejection and retry

**Fixture:** 5stack runs under WSL while Orca reports Windows worktree paths. An approved worker first uses a new Orca child, then an existing Git worktree. Orca rejects one pre-launch request without creating a Dispatch.

**Expected:** A new child receives a deterministic `--name`. An existing worktree is resolved through Orca and selected by its stable identity, not its WSL path. A rejection that reports no Dispatch or residual worker resources becomes `failed` and releases writer occupancy. The same worktree can then be retried without a shared-writer override. A response that cannot establish whether resources were created remains `unverifiable`. After an operator stop, Orca's stopped lifecycle becomes `stopped`, not `unverifiable`. Releasing the settled worker closes its retained terminal without removing the child worktree.

## 17. Herdr worker placement and lifecycle

**Fixture:** The primary runs in a Herdr workspace with a focused user tab. An approved short worker uses the Herdr backend and the full model ID from a 5stack profile.

**Request:** Dispatch, inspect, and stop the worker.

**Expected:** Create or reuse a tab labeled `Workers` in the current workspace without changing focus. The agent name describes the task and has a short unique suffix. Read the pane ID from the nested launch response, not the outer command ID. Read status from `result.agent.agent_status`; an idle or done worker has completed its turn, while an interrupted worker that settles to either state is stopped. Save the plain text from `herdr agent read` as the handoff. The model passed to Codex is the profile's full supported identifier.

## Recording a run

For each run, note the Codex session identifier, 5stack commit, scenario, verdict, and one short observation. Keep temporary fixtures and transcripts outside the repository. Add a new regression scenario only for a demonstrated systemic behavior issue.
