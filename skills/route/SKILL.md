---
name: route
description: Inspect a software-engineering request and project state, then recommend the smallest workflow that provides enough clarity and confidence.
---

# Route work

Inspect the request, relevant repository state, project instructions, existing documentation, referenced specs or issues, tracker state, and available skills. Get facts from tools rather than the user.

Recommend the next process. Do not automatically launch a large workflow.

Consider:

- clarity and hidden decisions;
- stakes, uncertainty, reversibility, and behavioral complexity;
- architectural and future importance;
- direct evidence that could establish success;
- token, documentation, interruption, review, and comprehension cost.

Possible recommendations include direct work, a short plan, grilling, a spec, tickets, debugging, TDD, independent review, manual review, feedback capture, retrospective reflection, or a relevant installed skill.

When one bounded coding worker would materially help, the route result may include a suggested backend, harness, model, and reasoning profile. This is a recommendation only. It never authorizes dispatch. The primary must still ask the User for explicit permission for that specific worker.

Prefer direct implementation for small clear tasks. Recommend added process only when its benefit exceeds its cost.

Use a compact result:

- **Recommendation:** the next action.
- **Why sufficient:** the relevant facts and risk.
- **Assurance:** LIGHT, STANDARD, or HIGH.
- **Ownership forecast:** DELEGATE, REVIEW, or UNDERSTAND.
- **Added process:** only steps that earn their cost, or `None`.

Use `review-5stack-feedback` only when the user explicitly invokes it in the 5stack repository.
