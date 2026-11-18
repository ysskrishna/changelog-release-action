# Usage Examples

Ready-to-copy workflows for [Release from Changelog or Tag](../README.md). Copy the selected file into your repository's `.github/workflows/` directory.

| Workflow | What it does | Before you use it |
| --- | --- | --- |
| [Release from changelog](release-from-changelog.yml) | Publish the matching version section with the default settings | Add a nonempty version section to `CHANGELOG.md` |
| [Release from tag](release-from-tag.yml) | Publish an annotated tag message | Use `git tag -a` and write the release body in its message |
| [Custom changelog and title](custom-changelog-and-title.yml) | Read `docs/CHANGELOG.md` and set the release title | Keep the changelog at that path or change the input |
| [Release with assets](release-with-assets.yml) | Create a source ZIP and checksum, then upload both | Keep the matching version section in `CHANGELOG.md` |

All workflows run on version tags such as `v1.2.3`, fetch the tagged checkout, grant the release job `contents: write`, and prevent overlapping runs for the same tag. Moving a major tag such as `v1` does not trigger them.

The tag must be pushed to GitHub before the action runs. For the changelog examples, `v1.2.3` matches `## [1.2.3]` or `## 1.2.3`. In the tag example, use an annotation such as `git tag -a v1.2.3 -m "Login works on macOS again"`.
