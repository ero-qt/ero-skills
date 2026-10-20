#!/usr/bin/env bash
# Prints the live state a task starts from: the fetch, the branch and tree,
# how far the branch is from its base, open PRs and issues from everyone that
# match the given search phrases, the PRs of the signed-in user and the CI
# checks of the current branch's PR.
#
# Exit codes: 0 everything checked, 2 gh signed out or missing, 3 the remote
# isn't on GitHub.
#
# Usage: bash state.sh ["phrase one" "phrase two" ...]
# Each argument is searched on its own. Without arguments, the newest open
# PRs and issues are listed.

set -u

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "not a git repository: $(pwd)" >&2
    exit 1
fi

# Picks the repo that PRs go to: upstream when it exists, else origin.
remote=upstream
git remote get-url upstream > /dev/null 2>&1 || remote=origin
url=$(git remote get-url "$remote" 2>/dev/null || true)
host=$(printf '%s' "$url" | sed -E 's#^(ssh://)?(git@)?(https?://)?([^/:]+).*#\4#')
repo=$(printf '%s' "$url" | sed -E 's#^(ssh://)?(git@)?(https?://)?[^/:]+[:/]##; s#/+$##; s#\.git$##')

echo "## fetch"
git fetch --all --prune 2>&1 | grep -v '^Fetching ' || true

echo
echo "## branch and tree"
git status --short --branch
if ! git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' > /dev/null 2>&1; then
    echo "branch $(git branch --show-current) has no upstream (not pushed)"
fi

base=""
for candidate in "$remote/HEAD" "$remote/main" "$remote/master" origin/main origin/master; do
    if git rev-parse --verify --quiet "$candidate" > /dev/null; then
        base=$(git rev-parse --abbrev-ref "$candidate")
        break
    fi
done
if [ -n "$base" ]; then
    read -r behind ahead <<< "$(git rev-list --left-right --count "$base"...HEAD)"
    echo "base $base: $behind behind, $ahead ahead"
fi

if [ "$host" != "github.com" ]; then
    echo
    echo "$remote is not a GitHub remote ($url), so PRs and issues were not checked"
    exit 3
fi

if ! command -v gh > /dev/null 2>&1 || [ -z "$repo" ]; then
    echo
    echo "gh or a GitHub remote is missing, so PRs and issues were not checked"
    exit 2
fi

# Stops with one clear line instead of an error per query when gh is signed out.
if ! gh auth status --hostname github.com > /dev/null 2>&1; then
    echo
    echo "gh is not signed in (run: gh auth refresh -h github.com), so PRs and issues were not checked"
    exit 2
fi

pr_line='.[] | "#\(.number) \(.title) [\(.author.login)] \(.headRefName) \(.updatedAt[:10])"'
issue_line='.[] | "#\(.number) \(.title) [\(.author.login)] \(.updatedAt[:10])"'

list() {
    local kind=$1 search=$2 jq=$3 fields=$4
    if [ -n "$search" ]; then
        gh "$kind" list --repo "$repo" --state open --search "$search" --limit 20 --json "$fields" --jq "$jq"
    else
        gh "$kind" list --repo "$repo" --state open --limit 15 --json "$fields" --jq "$jq"
    fi
}

if [ $# -eq 0 ]; then
    set -- ""
fi
for phrase in "$@"; do
    label=${phrase:-newest}
    echo
    echo "## open PRs in $repo: $label"
    list pr "$phrase" "$pr_line" number,title,author,headRefName,updatedAt
    echo
    echo "## open issues in $repo: $label"
    list issue "$phrase" "$issue_line" number,title,author,updatedAt
done

echo
echo "## PRs of the signed-in user in $repo"
gh pr list --repo "$repo" --author @me --state open --limit 30 \
    --json number,title,headRefName,reviewDecision,mergeable \
    --jq '.[] | "#\(.number) \(.title) \(.headRefName) review=\(.reviewDecision // "none") mergeable=\(.mergeable)"'

echo
echo "## CI of the current branch's PR"
branch=$(git branch --show-current)
head=$branch
# Uses owner:branch as the head when the PR comes from a fork, because gh only finds fork PRs that way.
fork_owner=$(git remote get-url origin 2>/dev/null | sed -E 's#^(ssh://)?(git@)?(https?://)?[^/:]+[:/]##; s#/.*##')
if [ "$remote" = upstream ] && [ -n "$fork_owner" ]; then
    head="$fork_owner:$branch"
fi
if gh pr view "$head" --repo "$repo" --json number > /dev/null 2>&1; then
    gh pr checks "$head" --repo "$repo" || true
else
    echo "no PR for $branch"
fi
