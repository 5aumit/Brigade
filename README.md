![5stack banner](assets/5stack-banner.png)

# 5stack

Develop with trust in yourself and your agent.

5stack gives agents room to investigate, implement, and verify routine work. Its ownership mapping keeps you in control of meaningful decisions, scope, risk, and irreversible actions, and shows when to delegate, review, or understand the work yourself.

## Principles

- Start with repository evidence and use the [smallest workflow that fits the task](AGENTS.md#implicit-routing-and-intent).
- Set [assurance](AGENTS.md#assurance-and-human-ownership) to LIGHT, STANDARD, or HIGH based on the task's size, risk, and reversibility.
- Set [ownership](AGENTS.md#assurance-and-human-ownership) to DELEGATE, REVIEW, or UNDERSTAND so users know their required involvement.
- [Classify unexpected findings](AGENTS.md#findings-during-work) as MINOR, MEANINGFUL, DECISION, or CRITICAL, then act accordingly.

## Commands to remember

- `/route`: recommend the smallest sufficient workflow.
- `$delegate`: recommend and, after explicit approval, dispatch one bounded coding worker.
- `/give-5stack-feedback <text>`: correct the current work and draft a feedback handoff.
- `/review-5stack-feedback`: investigate a pasted feedback handoff in this repository.
- `/reflect-5stack`: inspect the current session and draft useful feedback handoffs.

Other workflows are selected through normal conversation or `/route`.

5stack owns only skills whose behavior is part of its core contract or directly conflicts with that contract. It does not replace or fork unrelated upstream skills.

## Install

From this repository:

```bash
bash scripts/check.sh
bash scripts/install.sh
```

The installer links the repository at `~/.agents/5stack`, then links 5stack-owned instructions and skills into `~/.agents`. It also links the optional `5stack` command into `~/.local/bin`. Before creating or replacing `~/.agents/AGENTS.md`, it shows the change and asks for confirmation before making any changes. When replacing an existing path, it also shows its backup path. It backs up conflicting files and does not remove unrelated skills. Start a fresh Codex session after installation.

Worker backends are optional. Check them with:

```bash
5stack worker capabilities
```

For noninteractive use, pass `--yes` to explicitly approve installing global instructions:

```bash
bash scripts/install.sh --yes
```

To preview changes:

```bash
bash scripts/install.sh --dry-run
```

To remove 5stack-owned links and restore safe backups:

```bash
bash scripts/uninstall.sh
```

Run the uninstaller before moving this repository. If it was already moved, restore the old path temporarily or inspect and remove the broken 5stack links manually. The uninstaller deliberately leaves links it cannot prove belong to the current checkout.

## Target projects

5stack does not add its own persistent files or directories to target projects. Agents recover context from code, tests, Git, existing documentation, trackers, and the active session. Normal project artifacts are created only when the task requests them and should follow the repository's conventions.

Feedback about 5stack stays in chat. A project session produces a sanitized prompt that the user may copy into a 5stack development session. Nothing is stored or sent automatically.

## Maintaining 5stack

Normal users install and use 5stack. They do not need to run the scenarios in `evals/`.

Maintainers use the scenarios to check 5stack behavior after a change. Changes should update or add a focused scenario in `evals/scenarios.md`, then exercise relevant scenarios in fresh sessions. Pasted feedback should be investigated with `/review-5stack-feedback` before changing 5stack.
