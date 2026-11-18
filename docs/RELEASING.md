# Publishing Changelog Release

## Version tags

- Full version tags such as `v1.0.0` identify a fixed release. Do not move a published version tag.
- The moving major tag `v1` points to the latest compatible version for consumers.
- Breaking changes require a new major version and a new major tag.
- `.github/workflows/publish.yml` runs for `v*.*.*`. Moving `v1` does not create another release.

Creating tags, publishing releases, merging PRs, and submitting Marketplace listings require an explicit maintainer decision. The examples below document the process; the first version has not been published.

## First release

1. Review the implementation and confirm its CI checks pass. Select the version to publish.
2. Move the completed entries from `CHANGELOG.md` into a matching version section, for example `## [1.0.0]`, retaining an `Unreleased` section for future changes. Add the release and comparison links.
3. Merge the reviewed changes and tag that exact default-branch commit. For a selected version of `1.0.0`, the commands are:

   ```bash
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   ```

4. Confirm the Publish workflow creates the GitHub Release from the matching changelog section. Check its title, body, and URL. The self-release workflow uses the action checked out from that tag.
5. Create the moving `v1` tag at the reviewed version and push it. Consumers can then use `@v1`. On later compatible releases, update the major tag after verifying the new release.
6. Publish the action to GitHub Marketplace from the release publication flow. Use the name **Changelog Release**, icon **tag**, and color **blue** from `action.yml`. Verify the assigned Marketplace URL before adding it to the README badge, footer, and repository homepage.
7. Change the README Marketplace badge from pending to the verified listing, and remove the first-release notices in the README, example index, and security policy.

## Consumer pilot

1. After `v1` exists, review and merge the draft `gitingest-action` migration.
2. Select its pilot version and commit a nonempty matching changelog section before creating the tag.
3. Publish the explicitly selected consumer version. Check that its release body matches that changelog section and its title is `Release <tag>`.
4. Rerun the release job and confirm it skips the existing release without changing it.
5. Migrate the remaining repositories after this live pilot passes. Keep asset building in each caller and use the shared action for release creation.

## Documentation services

`context7.json` follows the PyPI Package Stats Action configuration and uses the same owner's public team verification key. Its project URL and description identify this action. This file prepares indexing; it does not register or index the project by itself.

After the documentation is merged, [add the repository to Context7](https://context7.com/add-library) and confirm its project page works before changing the Context7 badge from setup to docs. Request indexing through [DeepWiki](https://deepwiki.com/ysskrishna/changelog-release-action) and confirm the generated page before changing that badge from index to ask.

## Repository presentation

Keep the README badge row, input/output reference tables, usage-example links, error handling, maintainer section, support links, and footer aligned with the PyPI Package Stats Action pattern. Repository topics should describe GitHub Actions, changelogs, releases, and automation. Until the Marketplace listing exists, the repository homepage links to the README.
