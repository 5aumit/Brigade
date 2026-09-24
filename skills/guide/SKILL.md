---
name: guide
description: "Turn several competing project concerns into an outcome-focused priority and attention recommendation. Use for a high-level thought dump when no single next task is clear; not for a defined task that only needs workflow selection."
---

# Guide

Help the user regain orientation across competing medium-or-larger concerns. The goal is an agreed near-term focus and a useful division of attention, not a full roadmap or an implementation plan.

## Establish the situation

Inspect the repository, project documentation, tracker, current work, and available evidence before asking questions. Facts are the agent's job to find.

Identify the next meaningful outcome. If it is not clear from the user's request or project evidence, ask the smallest question that would establish it. Do not force a false choice when several outcomes can be jointly served by one narrow slice.

Classify each concern as one or more of:

- a user decision, where the outcome, policy, acceptable risk, or priority must be chosen;
- an agent investigation, where evidence can reduce uncertainty;
- an implementation candidate, where the intended behavior is sufficiently clear;
- a later investment, useful but not needed for the near-term outcome.

Do not invent questions merely to make the conversation feel thorough. For a material unresolved decision, state what it changes and give a recommendation with its tradeoff before asking the user. Use a proportionate grilling conversation when that decision needs further discussion.

## Recommend a workable order

Recommend the smallest coherent slice that advances the near-term outcome. A known defect or unknown fact should move ahead of that slice only when it blocks the promised result, threatens a material risk, or cheaply removes decisive uncertainty.

Explain the recommendation in terms of outcome impact, dependencies, reversibility, uncertainty, and the user's attention. Treat the order as a working hypothesis and name the evidence or decision that would change it.

Keep the active set small:

- **Now:** one outcome-focused slice.
- **Supporting:** only work that genuinely blocks or validates that slice.
- **Next:** the one or two concerns most likely to matter after it.
- **Later:** investments that do not yet earn attention.

## Allocate human attention deliberately

For each concern in Now, Supporting, or Next, make two separate calls.

First, state its immediate disposition:

- **Discuss:** a material product, policy, methodology, risk, or priority decision needs the user before the direction can be settled.
- **Investigate:** the agent can independently gather evidence, inspect the repository, diagnose, or conduct bounded research. This does not authorize an external change or a broad delegated effort.
- **Ready to act:** the behavior is clear enough to implement once the user authorizes the work. A thought dump alone does not authorize code changes.
- **Defer:** it does not currently earn attention.

Then assign the explicit Brigade ownership level to the resulting work:

- **DELEGATE:** after the Chef approves the work, explain why they do not need to read its code or raw output, and what evidence Expo will bring back.
- **REVIEW:** state the behavior or component the Chef will likely review, why it matters, and a rough LOC estimate. After inspection or implementation, give exact files, functions, and line ranges.
- **UNDERSTAND:** list the behavior, policy, measurement, or component the Chef will need to understand. Explain why it matters and give the expected review surface or rough LOC estimate when code is involved.

Set LIGHT, STANDARD, or HIGH assurance alongside the ownership level. Do not use ownership labels to obscure a user decision: a decision remains **Discuss** even if its eventual implementation could be delegated.

Separate what needs the user from what the agent can do independently:

- The user owns material product, policy, methodology, and risk decisions.
- The agent owns repository investigation, evidence gathering, diagnosis, and bounded research that does not make those decisions.
- Guide may inspect existing repository evidence to make its recommendation. Expo must ask the Chef before starting a separate investigation, audit, implementation task, or external action, including DELEGATE work.

Do not claim to objectively determine product priorities. Make a recommendation from the user's stated outcome and evidence, and surface the decision if the ranking depends on a value judgment.

## Tracking and handoff

Do not create todos, tickets, project documents, or delegated work merely because this skill ran. Suggest durable tracking only when work must survive sessions, involve other people, or has meaningful dependencies. Use the project's existing tracker or documentation convention.

When a durable breakdown would help, show the proposed slices and blockers, then ask for approval before using `to-tickets` or writing to a tracker. When a single concern is selected, recommend the appropriate next workflow, such as diagnosis, research, grilling, implementation, or review. Do not start broad work until the user confirms the direction or separately asks to proceed.

Use a compact result:

- **Near-term outcome:** what the priority serves.
- **Working order:** Now, Supporting, Next, and Later with concise reasons.
- **Attention map:** for each active concern, its disposition, assurance, ownership, the concrete user attention needed, and what the agent can take independently.
- **Ownership summary:** a short, cordial explanation of what the Chef does not need to worry about, may need to review, and should make time to understand.
- **Tracking:** whether durable tracking earns its cost.
- **Recommended next move:** one concrete action, with assurance and ownership, followed by a clear request for permission before the agent starts it.
