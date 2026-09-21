#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
STACK_REPO=$(dirname -- "$SCRIPT_DIR")
mapfile -t OWNED_SKILLS < "$STACK_REPO/skills/owned.txt"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

for required in \
  AGENTS.md \
  README.md \
  bin/5stack \
  lib/worker_control.py \
  references/trust-handoff.md \
  scripts/worker.py \
  evals/scenarios.md; do
  [[ -f "$STACK_REPO/$required" ]] || fail "missing $required"
done

skill_names=()
for skill in "${OWNED_SKILLS[@]}"; do
  skill_file="$STACK_REPO/skills/$skill/SKILL.md"
  [[ -f "$skill_file" ]] || fail "missing skill $skill"
  [[ "$(sed -n '1p' "$skill_file")" == "---" ]] || fail "$skill has no opening frontmatter delimiter"
  closing_line=$(awk 'NR > 1 && $0 == "---" { print NR; exit }' "$skill_file")
  [[ -n "$closing_line" ]] || fail "$skill has no closing frontmatter delimiter"
  declared=$(sed -n 's/^name: *//p' "$skill_file" | head -n 1)
  [[ "$declared" == "$skill" ]] || fail "$skill declares name '$declared'"
  [[ "$(sed -n 's/^description: *//p' "$skill_file" | wc -l)" -eq 1 ]] || fail "$skill needs one description"
  skill_names+=("$declared")
done

duplicates=$(printf '%s\n' "${skill_names[@]}" | sort | uniq -d)
[[ -z "$duplicates" ]] || fail "duplicate skill names: $duplicates"

for skill in give-5stack-feedback reflect-5stack review-5stack-feedback; do
  skill_file="$STACK_REPO/skills/$skill/SKILL.md"
  ui_file="$STACK_REPO/skills/$skill/agents/openai.yaml"
  grep -qx 'disable-model-invocation: true' "$skill_file" || fail "$skill must require explicit invocation"
  grep -qx '  allow_implicit_invocation: false' "$ui_file" || fail "$skill UI metadata must disable implicit invocation"
done

if command -v ruby >/dev/null; then
  ruby -ryaml -e '
    ARGV.each do |file|
      parts = File.read(file).split(/^---\s*$\n?/, 3)
      raise "invalid frontmatter: #{file}" unless parts.length == 3
      data = YAML.safe_load(parts[1])
      raise "invalid skill metadata: #{file}" unless data.is_a?(Hash) && data["name"] && data["description"]
    end
  ' "$STACK_REPO"/skills/*/SKILL.md || fail "skill YAML validation failed"
fi

if LC_ALL=C grep -RIl $'\342\200\224' \
  "$STACK_REPO/AGENTS.md" \
  "$STACK_REPO/README.md" \
  "$STACK_REPO/references" \
  "$STACK_REPO/skills" \
  "$STACK_REPO/templates" \
  "$STACK_REPO/evals" >/dev/null; then
  fail "em dash character found"
fi

bash -n "$STACK_REPO/scripts/install.sh"
bash -n "$STACK_REPO/scripts/uninstall.sh"
bash -n "$STACK_REPO/scripts/check.sh"
bash -n "$STACK_REPO/bin/5stack"
python3 -m py_compile "$STACK_REPO/lib/worker_control.py" "$STACK_REPO/scripts/worker.py"
python3 -m unittest discover -s "$STACK_REPO/tests"

CHECK_TMP=$(mktemp -d)
case "$CHECK_TMP" in
  /tmp/*) ;;
  *) fail "unexpected temporary path: $CHECK_TMP" ;;
esac
trap 'rm -rf -- "$CHECK_TMP"' EXIT

TEST_AGENTS_DIR="$CHECK_TMP/agents"
TEST_BIN_DIR="$CHECK_TMP/bin"
mkdir -p "$TEST_AGENTS_DIR/skills/implement"
printf 'original global instructions\n' > "$TEST_AGENTS_DIR/AGENTS.md"
printf 'original implement skill\n' > "$TEST_AGENTS_DIR/skills/implement/SKILL.md"

EMPTY_AGENTS_DIR="$CHECK_TMP/empty-agents"
if bash "$STACK_REPO/scripts/install.sh" --agents-dir "$EMPTY_AGENTS_DIR" --bin-dir "$TEST_BIN_DIR" >/dev/null 2>&1; then
  fail "installer created AGENTS.md without confirmation"
fi
[[ ! -e "$EMPTY_AGENTS_DIR/AGENTS.md" && ! -L "$EMPTY_AGENTS_DIR/AGENTS.md" ]] || fail "installer changed empty agents directory without confirmation"
bash "$STACK_REPO/scripts/install.sh" --yes --agents-dir "$EMPTY_AGENTS_DIR" --bin-dir "$TEST_BIN_DIR" >/dev/null
[[ -L "$EMPTY_AGENTS_DIR/AGENTS.md" ]] || fail "installer did not create AGENTS.md with explicit approval"

if bash "$STACK_REPO/scripts/install.sh" --agents-dir "$TEST_AGENTS_DIR" --bin-dir "$TEST_BIN_DIR" >/dev/null 2>&1; then
  fail "installer replaced AGENTS.md without confirmation"
fi
grep -q 'original global instructions' "$TEST_AGENTS_DIR/AGENTS.md" || fail "installer changed AGENTS.md after missing confirmation"
[[ ! -e "$TEST_AGENTS_DIR/5stack" && ! -L "$TEST_AGENTS_DIR/5stack" ]] || fail "installer changed files before confirmation"

bash "$STACK_REPO/scripts/install.sh" --yes --agents-dir "$TEST_AGENTS_DIR" --bin-dir "$TEST_BIN_DIR" >/dev/null
[[ -L "$TEST_AGENTS_DIR/AGENTS.md" ]] || fail "installer did not link AGENTS.md"
[[ -L "$TEST_AGENTS_DIR/5stack" ]] || fail "installer did not link the 5stack repository"
[[ -L "$TEST_BIN_DIR/5stack" ]] || fail "installer did not link the 5stack command"
XDG_STATE_HOME="$CHECK_TMP/state" "$TEST_BIN_DIR/5stack" worker list >/dev/null || fail "installed 5stack command did not run"
for skill in "${OWNED_SKILLS[@]}"; do
  [[ -L "$TEST_AGENTS_DIR/skills/$skill" ]] || fail "installer did not link $skill"
done

mkdir -p "$TEST_AGENTS_DIR/5stack-backups/v1/skills/feedback"
printf 'original feedback skill\n' > "$TEST_AGENTS_DIR/5stack-backups/v1/skills/feedback/SKILL.md"
ln -s "$STACK_REPO/skills/5stack-setup" "$TEST_AGENTS_DIR/skills/5stack-setup"
ln -s "$STACK_REPO/skills/feedback" "$TEST_AGENTS_DIR/skills/feedback"
ln -s "$STACK_REPO/skills/reflect" "$TEST_AGENTS_DIR/skills/reflect"

bash "$STACK_REPO/scripts/install.sh" --yes --agents-dir "$TEST_AGENTS_DIR" --bin-dir "$TEST_BIN_DIR" >/dev/null
[[ ! -e "$TEST_AGENTS_DIR/skills/5stack-setup" && ! -L "$TEST_AGENTS_DIR/skills/5stack-setup" ]] || fail "installer left legacy 5stack-setup"
[[ -f "$TEST_AGENTS_DIR/skills/feedback/SKILL.md" ]] || fail "installer did not restore legacy feedback backup"
[[ ! -e "$TEST_AGENTS_DIR/skills/reflect" && ! -L "$TEST_AGENTS_DIR/skills/reflect" ]] || fail "installer left legacy reflect"
grep -q 'original feedback skill' "$TEST_AGENTS_DIR/skills/feedback/SKILL.md" || fail "installer restored wrong legacy feedback backup"

bash "$STACK_REPO/scripts/uninstall.sh" --agents-dir "$TEST_AGENTS_DIR" --bin-dir "$TEST_BIN_DIR" >/dev/null
[[ -f "$TEST_AGENTS_DIR/AGENTS.md" ]] || fail "uninstaller did not restore AGENTS.md"
[[ ! -e "$TEST_AGENTS_DIR/5stack" && ! -L "$TEST_AGENTS_DIR/5stack" ]] || fail "uninstaller left the 5stack repository link"
[[ ! -e "$TEST_BIN_DIR/5stack" && ! -L "$TEST_BIN_DIR/5stack" ]] || fail "uninstaller left the 5stack command"
for skill in "${OWNED_SKILLS[@]}"; do
  if [[ "$skill" == "implement" ]]; then
    [[ -f "$TEST_AGENTS_DIR/skills/implement/SKILL.md" ]] || fail "uninstaller did not restore implement"
  else
    [[ ! -e "$TEST_AGENTS_DIR/skills/$skill" && ! -L "$TEST_AGENTS_DIR/skills/$skill" ]] || fail "uninstaller left $skill"
  fi
done
grep -q 'original global instructions' "$TEST_AGENTS_DIR/AGENTS.md" || fail "wrong AGENTS.md restored"
grep -q 'original implement skill' "$TEST_AGENTS_DIR/skills/implement/SKILL.md" || fail "wrong implement skill restored"
grep -q 'original feedback skill' "$TEST_AGENTS_DIR/skills/feedback/SKILL.md" || fail "uninstaller changed restored legacy feedback backup"

echo "5stack static and installer checks passed."
