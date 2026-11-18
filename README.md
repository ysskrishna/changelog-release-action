# Changelog Release

[![CI](https://github.com/ysskrishna/changelog-release-action/actions/workflows/test.yml/badge.svg)](https://github.com/ysskrishna/changelog-release-action/actions/workflows/test.yml)
[![GitHub Marketplace: pending](https://img.shields.io/badge/Marketplace-pending-lightgrey?logo=github)](#version-tags-and-marketplace)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/ysskrishna/changelog-release-action?label=release)](https://github.com/ysskrishna/changelog-release-action/releases)
[![Author site](https://img.shields.io/badge/author-ysskrishna.space-informational)](https://ysskrishna.space)
[![Context7: setup](https://img.shields.io/badge/Context7-setup-18181B)](https://context7.com/add-library)
[![DeepWiki: index](https://img.shields.io/badge/DeepWiki-index-18181B)](https://deepwiki.com/ysskrishna/changelog-release-action)

A GitHub Action to create GitHub Releases from your changelog section or annotated tag message, with optional asset uploads. Powered by [GitHub CLI](https://cli.github.com/).

> The first release and Marketplace listing are pending. The `@v1` examples become usable after publication. Context7 and DeepWiki indexing are also pending.

## Quick Start

After checking out your tagged repository with full history:

```yaml
- uses: ysskrishna/changelog-release-action@v1
  id: release

- name: Show release URL
  env:
    RELEASE_URL: ${{ steps.release.outputs.release-url }}
  run: printf '%s\n' "$RELEASE_URL"
```

The action reads the matching version section from `CHANGELOG.md` and uses `Release <tag>` as the title. No inputs are required. The `id` field is needed only when referencing step outputs.

The calling job needs `contents: write`. For a complete workflow with checkout, permissions, and concurrency, copy [Release from changelog](examples/release-from-changelog.yml).

## Inputs

All inputs are optional.

| Input | Description | Required | Default |
| --- | --- | --- | --- |
| `release-body-source` | Where the release body comes from: `changelog` or `tag` | No | `changelog` |
| `release-changelog-path` | Changelog file path, relative to the checkout | No | `CHANGELOG.md` |
| `release-title` | Release title | No | `Release <tag>` |
| `release-assets` | Files to upload, one literal path per line | No | No assets |

The selected body source must contain text. A missing source fails the job. There are no automatic fallbacks or generated notes.

## Outputs

| Output | Description |
| --- | --- |
| `release-url` | URL of the created or existing GitHub Release |
| `release-created` | `true` for a new release; `false` when an existing release was skipped |

Reference outputs as `steps.<id>.outputs.release-url` in subsequent steps, as shown in Quick Start.

## Release Body

### From your changelog

For a tag named `v1.2.3`, add a matching version section:

```markdown
## [1.2.3] - 2026-11-18

### Fixed

- Login works on macOS again.
```

The body contains the text below that heading, ending before the next version section or trailing reference links. The title defaults to `Release v1.2.3`. Headings such as `## 1.2.3` also work. One leading `v` is removed from the tag when matching the version; matching is exact.

### From your tag message

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

The annotation becomes the body, and the title still defaults to `Release v1.2.3`. A label-only annotation such as `Release 1.2.3` is used as written. Lightweight tags fail in `tag` mode because they have no annotation. PGP and SSH signing blocks are excluded; this action does not verify signatures.

## Usage Examples

For complete, ready-to-copy workflow files, see [Usage Examples](examples/README.md).

| Example | Description |
| --- | --- |
| [Release from changelog](examples/release-from-changelog.yml) | Publish the matching version section using the default settings |
| [Release from tag](examples/release-from-tag.yml) | Publish the annotated tag message as the release body |
| [Custom changelog and title](examples/custom-changelog-and-title.yml) | Read a different changelog path and customize the title |
| [Release with assets](examples/release-with-assets.yml) | Build a source ZIP and checksum, then attach both files |

Repository or organization variables can supply input values:

```yaml
with:
  release-changelog-path: ${{ vars.RELEASE_CHANGELOG_PATH || 'CHANGELOG.md' }}
```

Asset paths are relative to the checkout unless absolute. Spaces are supported. List each file explicitly; wildcards and asset labels are not supported. Filenames containing `#` are rejected because GitHub CLI reserves it for labels. Build and sign assets in earlier workflow steps.

## Error Handling

The action fails with a clear message when:

- The selected changelog file or version section is missing or empty.
- `release-body-source: tag` is selected but the tag is lightweight or its annotation is empty.
- A requested asset file is missing or uses an unsupported filename.
- The checkout does not match the triggering tag, or the local tag is missing.
- The body source is invalid, a required runner tool is missing, or the token lacks permission.
- GitHub rejects the release lookup or creation request.

Only an HTTP 404 response is treated as a missing release. Authentication, rate-limit, and server errors stop the job.

If an upload fails, inspect the GitHub Release before retrying. Release creation and asset upload use multiple API requests. Existing releases are skipped, so a rerun does not repair partial uploads or add new assets.

## Requirements and Reruns

- Run on a tag push and check out that tag with `fetch-depth: 0`.
- Grant the release job `contents: write`. The action uses the workflow's GitHub token automatically. Set `GH_TOKEN` in the step's environment to use another token.
- Use a runner with Bash, Git, GitHub CLI (`gh`), `jq`, and standard Unix tools. The action installs nothing. CI covers Ubuntu and macOS; native Windows shells are not supported.
- Push the tag to GitHub before running the action. The action never creates Git tags.
- Existing releases keep their title, body, and assets unchanged.
- Configure workflow concurrency as shown in the examples to avoid overlapping runs for the same tag.

## Version Tags and Marketplace

Consumers can use the moving `@v1` tag for compatible updates or pin a reviewed commit SHA. Full version tags such as `v1.0.0` identify individual releases.

The example workflows match `v*.*.*`, so updating a moving major tag such as `v1` does not create another release.

The first version tag, moving `v1` tag, and Marketplace listing have not been published. See [Publishing Changelog Release](docs/RELEASING.md) for the publication process, pilot validation, and documentation-service setup. The Marketplace badge links here until a listing URL is verified.

## Development

The composite entry point is `action.yml`; `scripts/release.sh` contains the release logic. Tests use real temporary Git repositories and a fake `gh`, without network calls or real releases:

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/release.sh
```

To test a consumer's current changelog through the same runtime:

```bash
python3 tests/pilot.py /path/to/consumer
```

CI also checks that the composite action rejects a branch invocation. A real tag-triggered release remains the final publication check.

## Credits

Built with [Git](https://git-scm.com/) and [GitHub CLI](https://cli.github.com/). Changelog conventions follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Built and maintained by

Changelog Release is built and maintained by:

| | Name | GitHub | Role |
| --- | --- | --- | --- |
| <img src="https://github.com/ysskrishna.png?size=120" width="60" height="60" alt="Y. Siva Sai Krishna"> | **Y. Siva Sai Krishna** | [@ysskrishna](https://github.com/ysskrishna) | Creator |

## Changelog

See [CHANGELOG](CHANGELOG.md) for release history.

## Support

If you find this project helpful:

- Star the repository.
- [Report issues](https://github.com/ysskrishna/changelog-release-action/issues).
- Submit pull requests.
- [Sponsor on GitHub](https://github.com/sponsors/ysskrishna).

For security problems, use the private reporting process in the [Security Policy](.github/SECURITY.md).

## References

- [GitHub action metadata and inputs](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax)
- [GitHub CLI release creation, tag verification, and asset uploads](https://cli.github.com/manual/gh_release_create)

## License

MIT © [Y. Siva Sai Krishna](https://github.com/ysskrishna) - see [LICENSE](LICENSE) for details.

---

<p align="left">
  <a href="https://github.com/ysskrishna">Author's GitHub</a> •
  <a href="https://linkedin.com/in/ysskrishna">Author's LinkedIn</a> •
  <a href="https://ysskrishna.space">Author's site</a> •
  <a href="#version-tags-and-marketplace">Marketplace status</a> •
  <a href="examples/README.md">Examples</a> •
  <a href="https://github.com/ysskrishna/changelog-release-action/releases">Releases</a> •
  <a href="https://github.com/ysskrishna/changelog-release-action/issues">Report Issues</a>
</p>
