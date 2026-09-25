![Brigade](assets/wordmark-cream.png)

# Brigade

Develop with trust in yourself and your agent.

Brigade gives Expo room to investigate, implement, and verify routine work. Its ownership mapping keeps the Chef in control of meaningful decisions, scope, risk, and irreversible actions, and shows when to delegate, review, or understand the work personally.

## Principles

- Start with repository evidence and use the [smallest workflow that fits the task](AGENTS.md#implicit-routing-and-intent).
- Set [assurance](AGENTS.md#assurance-and-human-ownership) to LIGHT, STANDARD, or HIGH based on the task's size, risk, and reversibility.
- Set [ownership](AGENTS.md#assurance-and-human-ownership) to DELEGATE, REVIEW, or UNDERSTAND so users know their required involvement.
- [Classify unexpected findings](AGENTS.md#findings-during-work) as MINOR, MEANINGFUL, DECISION, or CRITICAL, then act accordingly.

## Commands to remember

- `/route`: recommend the smallest sufficient workflow.
- `$delegate`: recommend and, after explicit approval, dispatch one bounded coding worker.
- `/give-brigade-feedback <text>`: correct the current work and draft a feedback handoff.
- `/review-brigade-feedback`: investigate a pasted feedback handoff in this repository.
- `/reflect-brigade`: inspect the current session and draft useful feedback handoffs.

Other workflows are selected through normal conversation or `/route`.

Brigade owns only skills whose behavior is part of its core contract or directly conflicts with that contract. It does not replace or fork unrelated upstream skills.

## Install

From this repository:

```bash
bash scripts/check.sh
bash scripts/install.sh
```

The installer links the repository at `~/.agents/brigade`, then links Brigade-owned instructions and skills into `~/.agents`. It installs `brigade` into `~/.local/bin` and keeps `5stack` as a temporary compatibility alias. Existing worker history remains in the old state path when present, and existing `5stack-backups` remain available for safe restoration. Before creating or replacing `~/.agents/AGENTS.md`, it shows the change and asks for confirmation before making any changes. When replacing an existing path, it also shows its backup path. It backs up conflicting files and does not remove unrelated skills. Start a fresh Codex session after installation.

Worker backends are optional. Check them with:

```bash
brigade worker capabilities
```

For noninteractive use, pass `--yes` to explicitly approve installing global instructions:

```bash
bash scripts/install.sh --yes
```

To preview changes:

```bash
bash scripts/install.sh --dry-run
```

To remove Brigade-owned links and restore safe backups:

```bash
bash scripts/uninstall.sh
```

Run the uninstaller before moving this repository. If it was already moved, restore the old path temporarily or inspect and remove the broken Brigade links manually. The uninstaller deliberately leaves links it cannot prove belong to the current checkout.

## Target projects

Brigade does not add its own persistent files or directories to target projects. Expo recovers context from code, tests, Git, existing documentation, trackers, and the active session. Normal project artifacts are created only when the task requests them and should follow the repository's conventions.

Feedback about Brigade stays in chat. A project session produces a sanitized prompt that the Chef may copy into a Brigade development session. Nothing is stored or sent automatically.

## Maintaining Brigade

Normal users install and use Brigade. They do not need to run the scenarios in `evals/`.

Maintainers use the scenarios to check Brigade behavior after a change. Changes should update or add a focused scenario in `evals/scenarios.md`, then exercise relevant scenarios in fresh sessions. Pasted feedback should be investigated with `/review-brigade-feedback` before changing Brigade.
