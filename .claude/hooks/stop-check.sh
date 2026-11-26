#!/usr/bin/env bash
# Implements: workflow/checked-before-done
# Stop hook: runs `make check` before Claude may finish. A failure blocks the stop once (exit 2, output fed back to
# Claude); if Claude is already continuing because of this hook, it lets it stop so the session can't loop forever.
input=$(cat)
if printf '%s' "$input" | grep -q '"stop_hook_active": *true'; then
  exit 0
fi
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
if out=$(make check 2>&1); then
  exit 0
fi
{
  echo "make check is failing. Fix it before finishing, or say plainly why it can't be fixed now:"
  printf '%s\n' "$out" | tail -n 40
} >&2
exit 2
