#!/bin/bash
# setup.sh — Connect Bruna Land skills to ~/.claude/skills/
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/.claude/skills"
SKILLS_DST="$HOME/.claude/skills"

mkdir -p "$SKILLS_DST"

echo "Syncing skills from $SKILLS_SRC to $SKILLS_DST..."

for skill_dir in "$SKILLS_SRC"/*/; do
  skill_name="$(basename "$skill_dir")"
  target="$SKILLS_DST/$skill_name"

  if [ -L "$target" ]; then
    echo "  ~ $skill_name (already linked)"
  elif [ -d "$target" ]; then
    echo "  ! $skill_name (exists as real directory, skipping — remove it manually to link)"
  else
    ln -s "$skill_dir" "$target"
    echo "  + $skill_name (linked)"
  fi
done

echo "Done."
