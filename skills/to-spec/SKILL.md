---
name: to-spec
description: Turn sufficiently settled requirements into a concise engineering spec that forecasts evidence, abstraction cost, and human attention.
---

# Write a Brigade spec

Inspect the repository, relevant existing documentation, and referenced issues or prior discussion. If a material decision is still hidden, state it and recommend grilling instead of pretending the work is ready.

Write only the sections that add information:

## What and why

What is being built and the problem it solves.

## Done behavior

Observable behavior that counts as complete.

## Out of scope

Important exclusions.

## Settled decisions

Decisions already approved. Do not reopen them.

## Likely implementation shape

Affected areas and the simplest likely design. State whether a substantial new maintained abstraction is expected and its comprehension cost. Do not write a line-by-line blueprint unless the design itself must be settled.

## Evidence plan

The direct behavior, observable outputs, tests, and review that would provide real confidence.

## Human attention forecast

- Assurance: LIGHT, STANDARD, or HIGH.
- Ownership: DELEGATE, REVIEW, or UNDERSTAND.
- Likely review target and reason.
- Whether a guided manual review is expected.

Use the project tracker convention. A local draft or explicit request to write a spec authorizes that local artifact. Creating or changing a GitHub issue is remote state and requires explicit authority. Show a draft before publishing when that authority was not already clear.

Do not require user stories or ticket creation.
