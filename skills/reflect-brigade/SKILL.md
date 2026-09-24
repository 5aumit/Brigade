---
name: reflect-brigade
description: Inspect the current session for useful feedback about Brigade and draft evidence-backed prompts for review in the Brigade repository without saving artifacts. Use only when the Chef explicitly invokes reflect-brigade.
disable-model-invocation: true
---

# Reflect on Brigade

Review the current session for feedback about Brigade behavior. Do not edit Brigade from a project session. Do not create or update files solely to capture feedback.

Look for confident positive, negative, or mixed signals involving:

- clarity, tone, explanation order, or reader effort;
- unnecessary or missing process;
- routing and skill selection;
- code quality or verification discipline influenced by Brigade;
- important findings surfaced too late or not at all;
- appropriate or inappropriate pushback;
- human ownership and review burden;
- actions taken after the Chef corrected Expo.

Separate candidates into:

- confident Brigade feedback supported by the session;
- ambiguous feedback that lacks enough evidence;
- project-specific or model-specific behavior with no demonstrated Brigade connection.

One observation is not automatic proof of a systemic problem. Do not manufacture criticism, turn routine friction into a lesson, or reinterpret neutral comments as feedback. Ask at most one concise question when an ambiguous candidate is important enough to resolve.

For each confident theme, build the same small evidence capsule required by `give-brigade-feedback`: original goal, relevant conditions, involved workflow or skill, observed behavior, Chef response, short session evidence, correction and result when one occurred, preferred future behavior, and the installed Brigade commit or best available version description.

Never include a full transcript, chain of thought, complete diff, large tool output, secret, credential, personal data, private remote URL, absolute path, or unnecessary private source. Do not fabricate evidence.

## Reply

Start with a short list of confident themes and candidates you rejected or could not establish. Then provide one copy-ready fenced text block per distinct confident theme. Combine closely related observations. Use this structure:

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

Session evidence:
- Chef response: <short excerpt or faithful summary>
- Agent response: <short excerpt or faithful summary>
- Available evidence: <fact, diff summary, verification, or review finding>
- Why this mattered: <concrete effect>

Correction or retry:
<what changed, or state that no correction occurred>

Result:
<outcome and supporting evidence, or unknown>

Preferred future behavior:
<what Brigade should preserve or change>

Review request:
Inspect the relevant Brigade instructions, skills, scenarios, and history.
Classify this as already addressed, a usage or routing issue, project-specific,
or systemic. If systemic, propose the smallest regression scenario and system
change. Show proposed changes before editing.
```

If there is no confident feedback, say so and produce no prompt. Do not save or send any prompt. The Chef decides what to copy into a Brigade development session.
