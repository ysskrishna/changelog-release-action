# Changelog Release

Create a GitHub Release from your changelog section or annotated tag message. Upload your build files in the same step. Works with projects in any language.

This action is under development. The `v1` examples below become usable after the first release is published.

## Quick start

Add `.github/workflows/release.yml` to your repository:

```yaml
name: Release

on:
  push:
    tags: ['v*.*.*']

permissions:
  contents: read

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5.1.0
        with:
          fetch-depth: 0
          persist-credentials: false

      - uses: ysskrishna/changelog-release-action@v1
```

Commit a matching version section to `CHANGELOG.md`, then push that version tag. For `v1.2.3`:

```markdown
## [1.2.3] - 2026-11-18

### Fixed

- Login works on macOS again.
```

The release title is `Release v1.2.3`. Its body contains the section below that version heading, ending before the next version section or trailing reference links. `## 1.2.3` headings also work. One leading `v` is removed from the tag when matching the version; matching is exact.

The example tag pattern excludes moving major tags such as `v1`. Updating an action's major tag should not create another release.

## Inputs

All inputs are optional.

| Input | What it controls | Default |
| --- | --- | --- |
| `release-body-source` | `changelog` reads the matching version section; `tag` reads the annotated tag message | `changelog` |
| `release-changelog-path` | Changelog file path, relative to the checkout | `CHANGELOG.md` |
| `release-title` | Release title | `Release <tag>` |
| `release-assets` | Files to upload, one literal path per line | No assets |

The selected body source must contain text. There are no automatic fallbacks or generated notes: a missing source fails so an incomplete release is not published silently.

### Use the tag message

```yaml
- uses: ysskrishna/changelog-release-action@v1
  with:
    release-body-source: tag
```

Create an annotated tag with the text you want readers to see:

```bash
git tag -a v1.2.3 -m "Login works on macOS again"
git push origin v1.2.3
```

The annotation becomes the release body. The title still defaults to `Release v1.2.3`. A label-only annotation such as `Release 1.2.3` is used as written. Lightweight tags fail in `tag` mode because they have no annotation. PGP and SSH signing blocks are excluded from the body; this action does not verify signatures.

### Customize the changelog, title, and assets

Build your files in earlier workflow steps, then:

```yaml
- uses: ysskrishna/changelog-release-action@v1
  with:
    release-changelog-path: docs/CHANGELOG.md
    release-title: Desktop app release
    release-assets: |
      dist/app.zip
      dist/checksums.txt
```

Asset paths are relative to the checkout unless absolute. Spaces are supported. Wildcards and asset labels are not supported; list each file explicitly. Filenames containing `#` are rejected because GitHub CLI reserves it for labels. Missing files fail before release creation. Building and signing assets remain the caller's responsibility.

Repository or organization variables can supply input values:

```yaml
with:
  release-changelog-path: ${{ vars.RELEASE_CHANGELOG_PATH || 'CHANGELOG.md' }}
```

## Outputs

Give the step an `id` to read its outputs, such as `${{ steps.release.outputs.release-url }}`.

| Output | Meaning |
| --- | --- |
| `release-url` | URL of the created or existing release |
| `release-created` | `true` for a new release; `false` when an existing release was skipped |

## Requirements and reruns

- Run on a tag push and check out that tag with `fetch-depth: 0`.
- Grant the job `contents: write`. The action uses the workflow's GitHub token automatically. Set `GH_TOKEN` in the step's environment to use another token.
- Use a runner with Bash, Git, GitHub CLI (`gh`), `jq`, and standard Unix tools. The action installs nothing. CI exercises Ubuntu and macOS; native Windows shells are not supported.
- The tag must already exist on GitHub. The action never creates Git tags.
- An existing release is left unchanged, including its title, body, and assets. Reruns do not repair or upload additional assets. Authentication, rate-limit, and server failures are reported rather than mistaken for missing releases.
- Release creation and asset upload use multiple GitHub API requests. If a run fails during upload, inspect the release before retrying. Configure workflow concurrency as in the quick start to avoid overlapping runs for the same tag.

For an immutable dependency reference, pin a reviewed commit SHA instead of the moving `@v1` tag.

## Development

The composite entry point is `action.yml`; `scripts/release.sh` contains the release logic. Tests use real temporary Git repositories and a fake `gh`, with no network or real releases:

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/release.sh
```

To test a consumer's current changelog through the same runtime:

```bash
python3 tests/pilot.py /path/to/consumer
```

CI also checks that the composite action rejects invocation from a branch. A real tag-triggered release remains the final publication check.

Maintainers: review the PR and CI, merge the implementation, add the chosen version section to the changelog, and then publish the explicitly approved version tag. The included release workflow runs the local action itself. Maintain the moving `v1` tag separately; it does not trigger that workflow. Marketplace listing is a separate GitHub publication step.

## References

- [GitHub action metadata and inputs](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax)
- [GitHub CLI release creation, tag verification, and asset uploads](https://cli.github.com/manual/gh_release_create)

## License

[MIT](LICENSE)
