#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

for tool in git gh jq awk; do
  command -v "$tool" >/dev/null || fail "Required tool is missing: $tool."
done
[[ -n "${GH_TOKEN:-}" ]] || fail 'Set GH_TOKEN or run this action with the default GitHub token.'
[[ "${GITHUB_REF:-}" == refs/tags/* ]] || fail 'Run this action from a pushed version tag.'
[[ -n "${GITHUB_REPOSITORY:-}" ]] || fail 'GITHUB_REPOSITORY is missing.'
cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is missing}"

tag="${GITHUB_REF#refs/tags/}"
ref="refs/tags/$tag"
source="${RELEASE_BODY_SOURCE:-changelog}"
changelog="${RELEASE_CHANGELOG_PATH:-CHANGELOG.md}"
title="${RELEASE_TITLE:-Release $tag}"
case "$source" in
  changelog|tag) ;;
  *) fail 'release-body-source must be changelog or tag.' ;;
esac
git show-ref --verify --quiet "$ref" || fail 'The local tag is missing. Use actions/checkout with fetch-depth: 0.'
tag_commit="$(git rev-parse "$ref^{commit}")" || fail 'The tag must point to a commit.'
[[ "$tag_commit" == "$(git rev-parse HEAD)" ]] || fail 'The checkout must point to the triggering tag.'

temp_dir="$(mktemp -d)"
trap 'rm -rf "$temp_dir"' EXIT
encoded_tag="$(printf '%s' "$tag" | jq -sRr @uri)"
export GH_HOST="${GH_HOST:-${GITHUB_SERVER_URL:-https://github.com}}"
GH_HOST="${GH_HOST#https://}"
GH_HOST="${GH_HOST#http://}"

# A failed lookup is only absence when GitHub actually returns HTTP 404.
if gh api --method GET --include "repos/$GITHUB_REPOSITORY/releases/tags/$encoded_tag" \
    >"$temp_dir/response" 2>"$temp_dir/error"; then
  url="$(sed '1,/^[[:space:]]*$/d' "$temp_dir/response" | jq -er '.html_url')"
  [[ "$url" =~ ^https?://[^[:space:]]+$ ]] || fail 'GitHub returned an invalid release URL.'
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    printf 'release-created=false\nrelease-url=%s\n' "$url" >> "$GITHUB_OUTPUT"
  fi
  echo 'The release already exists; skipping.'
  exit 0
elif ! grep -Eq '^HTTP/[0-9.]+ 404([[:space:]]|$)' "$temp_dir/response"; then
  cat "$temp_dir/error" >&2
  fail 'Could not check whether the release exists. Check token permissions and GitHub availability.'
fi

notes="$temp_dir/notes.md"
if [[ "$source" == changelog ]]; then
  [[ -f "$changelog" ]] || fail 'The changelog file is missing. Check release-changelog-path.'
  [[ "$changelog" == /* ]] || changelog="$PWD/$changelog"
  version="${tag#v}"
  awk -v version="$version" '
    {
      sub(/\r$/, "")
      if ($0 ~ /^```/ || $0 ~ /^~~~/) {
        marker = substr($0, 1, 3)
        if (!fence) fence = marker
        else if (fence == marker) fence = ""
        if (emit) print
        next
      }
      if (!fence && /^##[[:space:]]+/) {
        if (emit) exit
        heading = $0
        sub(/^##[[:space:]]+/, "", heading)
        split(heading, parts, /[[:space:]]+/)
        emit = (parts[1] == "[" version "]" || parts[1] == version)
        next
      }
      if (emit && !fence && /^\[[^]]+\]:[[:space:]]+https?:\/\//) exit
      if (emit) print
    }
  ' "$changelog" > "$notes"
else
  [[ "$(git cat-file -t "$ref")" == tag ]] || fail 'release-body-source: tag requires an annotated tag. Create it with git tag -a.'
  git cat-file tag "$ref" | sed '1,/^$/d' |
    sed '/^-----BEGIN PGP SIGNATURE-----$/,$d; /^-----BEGIN SSH SIGNATURE-----$/,$d' > "$notes"
fi
[[ -n "$(tr -d '[:space:]' < "$notes")" ]] || fail 'The selected release body is empty or the changelog version section is missing.'

command_args=(release create "$tag" --repo "$GITHUB_REPOSITORY" --verify-tag
  --title "$title" --notes-file "$notes" --)
while IFS= read -r asset || [[ -n "$asset" ]]; do
  asset="${asset%$'\r'}"
  [[ -n "$asset" ]] || continue
  [[ -f "$asset" ]] || fail 'A release asset file is missing. Use literal file paths, one per line; wildcards are not expanded.'
  [[ "$asset" != *'#'* ]] || fail 'Release asset filenames cannot contain # because GitHub CLI treats it as a label separator.'
  [[ "$asset" == /* ]] || asset="$PWD/$asset"
  command_args+=("$asset")
done <<< "${RELEASE_ASSETS:-}"

url="$(gh "${command_args[@]}")" || fail 'Release creation failed. Inspect the GitHub release before retrying if assets were partially uploaded.'
[[ "$url" =~ ^https?://[^[:space:]]+$ ]] || fail 'GitHub returned an invalid release URL after creation.'
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  printf 'release-created=true\nrelease-url=%s\n' "$url" >> "$GITHUB_OUTPUT"
fi
echo 'GitHub Release created.'
