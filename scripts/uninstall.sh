#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
STACK_REPO=$(dirname -- "$SCRIPT_DIR")
AGENTS_DIR="${HOME}/.agents"
BIN_DIR="${HOME}/.local/bin"
DRY_RUN=0

usage() {
  echo "Usage: $0 [--dry-run] [--agents-dir PATH] [--bin-dir PATH]"
}

while (($#)); do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --agents-dir)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      AGENTS_DIR=$2
      shift 2
      ;;
    --bin-dir)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      BIN_DIR=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

BACKUP_DIR="$AGENTS_DIR/5stack-backups/v1"
SKILLS_DIR="$AGENTS_DIR/skills"
ROOT_LINK="$AGENTS_DIR/5stack"
BIN_LINK="$BIN_DIR/5stack"
mapfile -t OWNED_SKILLS < "$STACK_REPO/skills/owned.txt"
LEGACY_SKILLS=(5stack-setup feedback reflect)

say_action() {
  if ((DRY_RUN)); then
    echo "DRY RUN: $*"
  else
    echo "$*"
  fi
}

remove_owned_link() {
  local source_path=$1 target_path=$2 backup_path=$3 resolved_source resolved_target
  resolved_source=$(readlink -f -- "$source_path")

  if [[ -L "$target_path" ]]; then
    resolved_target=$(readlink -f -- "$target_path" 2>/dev/null || true)
    if [[ "$resolved_target" == "$resolved_source" ]]; then
      say_action "Remove 5stack link $target_path"
      ((!DRY_RUN)) && rm -- "$target_path"
    else
      echo "Leave non-5stack link unchanged: $target_path"
      return
    fi
  elif [[ -e "$target_path" ]]; then
    echo "Leave non-link path unchanged: $target_path"
    return
  fi

  if [[ -e "$backup_path" || -L "$backup_path" ]]; then
    say_action "Restore $backup_path -> $target_path"
    if ((!DRY_RUN)); then
      mkdir -p -- "$(dirname -- "$target_path")"
      mv -- "$backup_path" "$target_path"
    fi
  fi
}

remove_legacy_link() {
  local source_path=$1 target_path=$2 backup_path=$3 expected_target actual_target
  expected_target=$(readlink -m -- "$source_path")

  if [[ -L "$target_path" ]]; then
    actual_target=$(readlink -m -- "$target_path")
    if [[ "$actual_target" != "$expected_target" ]]; then
      echo "Leave non-5stack legacy link unchanged: $target_path"
      return
    fi
    say_action "Remove legacy 5stack link $target_path"
    ((!DRY_RUN)) && rm -- "$target_path"
  elif [[ -e "$target_path" ]]; then
    echo "Leave non-link legacy path unchanged: $target_path"
    return
  fi

  if [[ -e "$backup_path" || -L "$backup_path" ]]; then
    say_action "Restore $backup_path -> $target_path"
    if ((!DRY_RUN)); then
      mkdir -p -- "$(dirname -- "$target_path")"
      mv -- "$backup_path" "$target_path"
    fi
  fi
}

for skill in "${OWNED_SKILLS[@]}"; do
  remove_owned_link \
    "$STACK_REPO/skills/$skill" \
    "$SKILLS_DIR/$skill" \
    "$BACKUP_DIR/skills/$skill"
done

for skill in "${LEGACY_SKILLS[@]}"; do
  remove_legacy_link \
    "$STACK_REPO/skills/$skill" \
    "$SKILLS_DIR/$skill" \
    "$BACKUP_DIR/skills/$skill"
done

remove_owned_link "$STACK_REPO/AGENTS.md" "$AGENTS_DIR/AGENTS.md" "$BACKUP_DIR/AGENTS.md"
remove_owned_link "$STACK_REPO" "$ROOT_LINK" "$BACKUP_DIR/root"
remove_owned_link "$STACK_REPO/bin/5stack" "$BIN_LINK" "$BACKUP_DIR/bin/5stack"

echo "5stack-owned links removed. Non-5stack paths were left unchanged."
