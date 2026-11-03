#!/usr/bin/env bash
set -Eeuo pipefail

readonly EXPECTED_GITHUB_REMOTE="git@github.com:martemme/HomeAssistantAddons.git"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "ERROR: current directory is not a Git worktree." >&2
  exit 2
fi

if ! fetch_url=$(git remote get-url github 2>/dev/null); then
  git remote add github "$EXPECTED_GITHUB_REMOTE"
  exit 0
fi

push_url=$(git remote get-url --push github 2>/dev/null)
if [[ "$fetch_url" != "$EXPECTED_GITHUB_REMOTE" || "$push_url" != "$EXPECTED_GITHUB_REMOTE" ]]; then
  echo "ERROR: existing 'github' remote has an unexpected destination." >&2
  exit 3
fi
