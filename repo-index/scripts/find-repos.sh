#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") <root-dir>" >&2
  exit 1
}

[ $# -eq 1 ] || usage
[ -d "$1" ] || { echo "Error: '$1' is not a directory" >&2; exit 1; }

# Find all .git directories, skipping tool caches that may contain nested repos
# (e.g. .terraform/modules). -prune on .terraform skips it entirely;
# -print -prune on .git prints the match and stops descent into it.
find "$1" \
  -name ".terraform" -prune \
  -o -name ".git" -type d -print -prune \
  | sed 's|/.git$||' \
  | sort
