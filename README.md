# Release from Changelog or Tag

[![CI](https://github.com/ysskrishna/changelog-release-action/actions/workflows/test.yml/badge.svg)](https://github.com/ysskrishna/changelog-release-action/actions/workflows/test.yml)
[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Release%20from%20Changelog%20or%20Tag-blue?logo=github)](https://github.com/marketplace/actions/release-from-changelog-or-tag)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/ysskrishna/changelog-release-action?label=release)](https://github.com/ysskrishna/changelog-release-action/releases)
[![Author site](https://img.shields.io/badge/author-ysskrishna.space-informational)](https://ysskrishna.space)

A GitHub Action to create GitHub Releases from your changelog section or annotated tag message, with optional asset uploads.

Changelog conventions follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). A tag such as `v1.2.3` matches the `## [1.2.3]` section in your changelog. Headings without brackets, such as `## 1.2.3`, also work.

## Quick Start

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

Before pushing `v1.2.3`, commit a nonempty `## [1.2.3]` section to `CHANGELOG.md`. Its contents become the release body, and the title defaults to `Release v1.2.3`. No action inputs are required.

The action reads only the matching version section. It excludes the version heading, the next version section, and trailing reference links. If the selected body is missing or empty, the job fails. Existing releases are skipped.

## Inputs

| Input | Description | Required | Default |
| --- | --- | --- | --- |
| `release-body-source` | Where the release body comes from: `changelog` or `tag` | No | `changelog` |
| `release-changelog-path` | Changelog file path, relative to the checkout | No | `CHANGELOG.md` |
| `release-title` | Release title | No | `Release <tag>` |
| `release-assets` | Files to upload, one literal path per line | No | No assets |

To use your annotated tag message as the body:

```yaml
- uses: ysskrishna/changelog-release-action@v1
  with:
    release-body-source: tag
```

Create the annotation with a command such as `git tag -a v1.2.3 -m "Login works on macOS again"`, then push that tag. The message is used as written, excluding PGP or SSH signing blocks. A lightweight tag has no annotation and fails in this mode. There are no automatic fallbacks or generated notes.

## Outputs

| Output | Description |
| --- | --- |
| `release-url` | URL of the created or existing GitHub Release |
| `release-created` | `true` for a new release; `false` when an existing release was skipped |

Give the action step an `id` to reference its outputs, such as `steps.release.outputs.release-url`.

<details>
<summary>Read the release URL in a later step</summary>

```yaml
- uses: ysskrishna/changelog-release-action@v1
  id: release

- name: Show release URL
  env:
    RELEASE_URL: ${{ steps.release.outputs.release-url }}
  run: printf '%s\n' "$RELEASE_URL"
```

</details>

## Usage Examples

For complete, ready-to-copy workflows, see [Usage Examples](examples/README.md).

| Example | Description |
| --- | --- |
| [Release from changelog](examples/release-from-changelog.yml) | Publish the matching version section using the default settings |
| [Release from tag](examples/release-from-tag.yml) | Publish the annotated tag message as the release body |
| [Custom changelog and title](examples/custom-changelog-and-title.yml) | Read a different changelog path and customize the title |
| [Release with assets](examples/release-with-assets.yml) | Build a source ZIP and checksum, then attach both files |

Build and sign assets in earlier workflow steps. List each asset file explicitly, one path per line, and give every file a unique filename. Paths may be relative to the checkout or absolute; spaces are supported. Wildcards and asset labels are not supported.

## Requirements

- Check out the triggering tag with `fetch-depth: 0` and grant the release job `contents: write`, as shown in Quick Start.
- Use a runner with Bash, Git, GitHub CLI (`gh`), `jq`, and standard Unix tools. The action installs nothing; native Windows shells are not supported.
- Push the tag to GitHub before the action runs. The action never creates Git tags.

## Troubleshooting

<details>
<summary>Release failures, token permissions, and reruns</summary>

The job fails when:

- The selected changelog file, version section, or tag annotation is missing or empty.
- The checkout does not match the triggering tag, or the local tag is missing.
- An asset is missing, filenames are duplicated, or a filename contains `#`, which GitHub CLI reserves for labels.
- An input value is invalid, a required tool is missing, or GitHub rejects the request.

The action uses the workflow's GitHub token automatically. Grant `contents: write` to the release job. To use another token, set `GH_TOKEN` in the step's environment.

Only an HTTP 404 response is treated as a missing release. Authentication, rate-limit, and server errors stop the job.

Release creation and asset upload use multiple API requests. If an upload fails, inspect the GitHub Release before retrying. Existing releases keep their title, body, and assets unchanged; reruns do not repair partial uploads or add new assets. Use workflow concurrency to avoid overlapping runs for the same tag.

The action strips signing blocks from annotated tag messages but does not verify signatures.

</details>

## Versioning

Use `@v1` for compatible updates or pin a full version tag or reviewed commit SHA. Full version tags such as `v1.0.0` identify individual releases. The example workflows match `v*.*.*`, so moving the major tag `v1` does not create another release.

## Development

<details>
<summary>Run the integration tests and consumer fixture locally</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
bash -n scripts/release.sh
python3 tests/pilot.py /path/to/consumer
```

Tests execute the single-step `action.yml` metadata in a controlled fixture context, including its defaults, environment mappings, run command, and public outputs. They use real temporary Git repositories and a fake GitHub CLI, without network calls or real releases. The fixture runner is limited to the expressions this action uses; it is not a general GitHub Actions runner. Hosted CI also checks the composite action's non-tag rejection.

The runtime is in `scripts/release.sh`. Python and PyYAML are test dependencies only.

</details>

## Built and maintained by

Release from Changelog or Tag is built and maintained by:

| | Name | GitHub | Role |
| --- | --- | --- | --- |
| <img src="https://github.com/ysskrishna.png?size=120" width="60" height="60" alt="Y. Siva Sai Krishna"> | **Y. Siva Sai Krishna** | [@ysskrishna](https://github.com/ysskrishna) | Creator |

## Changelog

See [CHANGELOG](CHANGELOG.md) for release history.

## Support

If you find this project helpful:

- ⭐ Star the repository
- 🐛 [Report issues](https://github.com/ysskrishna/changelog-release-action/issues)
- 🔀 Submit pull requests
- 💝 [Sponsor on GitHub](https://github.com/sponsors/ysskrishna)

## License

MIT © [Y. Siva Sai Krishna](https://github.com/ysskrishna) - see [LICENSE](LICENSE) for details.

---

<p align="left">
  <a href="https://github.com/ysskrishna">Author's GitHub</a> •
  <a href="https://linkedin.com/in/ysskrishna">Author's LinkedIn</a> •
  <a href="https://ysskrishna.space">Author's site</a> •
  <a href="https://github.com/marketplace/actions/release-from-changelog-or-tag">GitHub Marketplace</a> •
  <a href="examples/README.md">Examples</a> •
  <a href="https://github.com/ysskrishna/changelog-release-action/releases">Releases</a> •
  <a href="https://github.com/ysskrishna/changelog-release-action/issues">Report Issues</a>
</p>
