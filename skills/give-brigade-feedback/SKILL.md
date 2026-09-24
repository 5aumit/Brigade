---
name: give-brigade-feedback
description: Respond to explicit feedback about Brigade, safely correct the current work when needed, and draft an evidence-backed prompt for review in the Brigade repository. Use only when the Chef explicitly invokes give-brigade-feedback.
disable-model-invocation: true
---

# Give Brigade feedback

Treat the Chef's message as both feedback about Brigade and, when negative or mixed, a correction to the current work. Do not edit Brigade from the project session. Do not create or update any file solely to capture feedback.

## Respond to the feedback

Preserve the substance of the Chef's wording. Classify the signal as positive, negative, or mixed without arguing against it.

- For positive feedback, continue normally. Do not redo successful work merely to produce evidence.
- For negative or mixed feedback, correct or retry the affected work in the current response when it is safe and still within the authority already granted.
- A communication correction means restating the answer more effectively.
- A code-quality correction means inspecting the concrete problem, fixing only authorized work, and rerunning relevant verification.
- A missing-finding correction means surfacing the omitted fact and its significance.
- An ownership correction means revising the recommendation and naming the exact human attention that matters.

Feedback grants no new authority. Do not commit, push, delete, publish, contact external systems, repeat a destructive action, or broaden the task unless that action was already authorized. If a safe retry needs a Chef decision or new authority, explain the boundary and still draft the review prompt.

## Build a small evidence capsule

Use the current session to include only evidence that helps Expo distinguish a Brigade problem from a model mistake, project-specific issue, or misunderstanding:

- the original goal and relevant task conditions;
- the Brigade workflow or skill involved;
- a short exact excerpt or faithful summary of the affected agent response;
- the concrete code, verification, finding, or ownership evidence when relevant;
- the Chef's correction;
- what changed after the correction and whether it worked;
- the installed Brigade commit or best available version description.

For communication feedback, prefer a short before-and-after excerpt. For code feedback, summarize affected files or functions, the concrete defect, and verification instead of copying a diff. For omitted information, identify the fact available in the session and what the response left out. For ownership feedback, identify the risk-bearing decision or code and the recommendation that was given.

Never include a full transcript, chain of thought, complete diff, large tool output, secret, credential, personal data, private remote URL, absolute path, or unnecessary private source. Do not fabricate evidence. If an important detail is unavailable, say so in the prompt.

## Reply

Lead with the corrected outcome or normal task response. End with one copy-ready fenced text block using this structure:

```text
/review-brigade-feedback

Signal:
<positive | negative | mixed>

Brigade version:
<commit or best available description>

Original task:
<short description>

Relevant conditions:
<task size, risk, repository state, and workflow or skill involved>

Observed behavior:
<what the agent did>

Chef feedback:
<the Chef's feedback, quoted or closely preserved>

Session evidence:
- Agent response: <short excerpt or faithful summary>
- Available evidence: <fact, diff summary, verification, or review finding>
- Why this mattered: <concrete effect>

Correction or retry:
<what changed, or why no retry was needed or safe>

Result:
<outcome and supporting evidence>

Preferred future behavior:
<what Brigade should encourage>

Review request:
Inspect the relevant Brigade instructions, skills, scenarios, and history.
Classify this as already addressed, a usage or routing issue, project-specific,
or systemic. If systemic, propose the smallest regression scenario and system
change. Show proposed changes before editing.
```

Do not save or send the prompt. The Chef decides whether to copy it into a Brigade development session.
