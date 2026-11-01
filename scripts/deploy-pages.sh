#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Commit the already tracked public tree without moving the working checkout.
if git ls-remote --exit-code --heads origin gh-pages >/dev/null; then
  git fetch origin gh-pages
  pages_parent=$(git rev-parse FETCH_HEAD)
  pages_commit=$(git commit-tree HEAD:public -p "$pages_parent" -m 'Update Pattern Instrument site')
else
  remote_status=$?
  if [ "$remote_status" -ne 2 ]; then exit "$remote_status"; fi
  pages_commit=$(git commit-tree HEAD:public -m 'Publish Pattern Instrument site')
fi
git push origin "$pages_commit:refs/heads/gh-pages"
