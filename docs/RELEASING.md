# Publishing Release from Changelog or Tag

## Version tags

- Full version tags such as `v1.0.0` identify a fixed release. Do not move a published version tag.
- The moving major tag `v1` points to the latest compatible version for consumers.
- Breaking changes require a new major version and a new major tag.
- `.github/workflows/publish.yml` runs for `v*.*.*`. Moving `v1` does not create another release.

## Publish a version

1. Review the changes and confirm Ubuntu CI passes.
2. Add a dated version section to `CHANGELOG.md`, retaining an `Unreleased` section for future changes. The chosen tag must match that section after removing its leading `v`.
3. Merge the reviewed changes and tag that exact default-branch commit. For version `1.0.0`:

   ```bash
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   ```

4. Confirm the Publish workflow creates the GitHub Release with the correct title and changelog body. The workflow runs the action checked out from the version tag.
5. Create or update the corresponding major tag after verifying the release. For the `1.x` series, point `v1` at the reviewed version so consumers can use `@v1`.
6. Publish the action through the [GitHub Marketplace release flow](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace). Confirm the metadata name is unique, select the categories, and verify the resulting listing URL before adding its badge, footer link, and repository homepage.

## Validate a consumer release

1. Confirm the shared action's major tag exists, then review and merge the consumer migration.
2. Select the consumer version and commit a matching nonempty changelog section before pushing its tag.
3. Check that the resulting release body matches the changelog section and its title is `Release <tag>`.
4. Rerun the release job and confirm it skips the existing release without changing it.

## Development references

- [GitHub action metadata and inputs](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax)
- [GitHub CLI release creation and asset uploads](https://cli.github.com/manual/gh_release_create)
- [CommonMark fenced code blocks](https://spec.commonmark.org/current/#fenced-code-blocks)
