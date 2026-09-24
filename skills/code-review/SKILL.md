---
name: code-review
description: Independently review a fixed software change for behavior, evidence, scope, complexity, maintainability, and human ownership.
---

# Independent Brigade review

Resolve the review range from the user's fixed point, implementation checkpoint, referenced branch or PR, or the current task diff. Include relevant uncommitted task changes when requested. Verify that the range exists and is not empty.

Find the requirements from the request, spec, issue, commits, and existing project documentation. Read documented repository standards.

Use one independent reviewer by default. Give it the raw requirements, diff range, evidence produced so far, and these lenses:

- behavioral correctness and failure cases;
- missing or partial requirements;
- scope creep;
- unnecessary complexity and speculative abstractions;
- maintainability and project conventions;
- meaningfulness of tests and evidence gaps;
- important assumptions and remaining uncertainty;
- proportionality to project stakes;
- DELEGATE, REVIEW, or UNDERSTAND recommendation, with exact human review targets.

The reviewer should inspect and run focused checks when useful. It must not treat implementation-authored tests as independent proof by themselves.

Aggregate into one verdict. Rank findings as blocking, important, or optional. Cite exact files and lines. Do not preserve separate axes when one combined priority makes action clearer.

Fix only when the user or an active implementation workflow authorizes fixes. After important fixes, re-review those findings once. Do not loop over naming or style preferences.

Report the review in the current session or in the normal project deliverable the user requested. Do not create a Brigade-specific review artifact.
