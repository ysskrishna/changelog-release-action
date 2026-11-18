# Release ledger

Updated: 2026-11-19

This file records rollout progress. Consumer documentation describes normal usage rather than the current publication state.

## Initial release: 1.0.0

| Item | Status |
| --- | --- |
| Versioned changelog | Prepared for 1.0.0 on 2026-11-18 |
| Markdown fence and duplicate asset fixes | Implemented with regression coverage |
| Composite entry-point coverage | Tests execute metadata defaults, input/environment mappings, command, and public outputs |
| README review findings 5-11 | Addressed; release notices removed, long explanations collapsed, support matches the reference |
| Local tests and Ubuntu CI | 27 integration tests pass in a fresh environment; hosted Ubuntu passes on runtime commit 80b46b4 |
| Hosted macOS CI | Deferred by maintainer because of transient runner availability; excluded from the CI matrix |
| Merge, v1.0.0 release, and v1 tag | Awaiting the reviewed publication step |
| Marketplace name | Release from Changelog or Tag, selected by the maintainer on 2026-11-19; repository remains ysskrishna/changelog-release-action |
| Marketplace listing and badge | Publish after the version release; add only the verified listing URL |
| gitingest-action pilot | Composite fixture and all four existing integration jobs pass on 43b24d1, pinned to action 80b46b4; named live release remains to be performed |
| Remaining 21 repositories | Migrate after the live pilot passes |

## Follow-up PR after Marketplace publication

- Add Context7 configuration, register/index the documentation, and verify the resulting page.
- Add DeepWiki only after its indexed page is verified.
- Add the verified documentation badges and links together.
- Restore hosted macOS validation when runner availability recovers.

## Release evidence

Record the published version tag, commit SHA, Marketplace URL, consumer version, and successful live workflow links here after publication. Local fixtures do not replace the live pilot.

Pre-publication checks:

- [Action Ubuntu integration](https://github.com/ysskrishna/changelog-release-action/actions/runs/44367684093) passes for runtime commit 80b46b4.
- [Consumer composite fixture](https://github.com/ysskrishna/gitingest-action/actions/runs/44367731768) and [existing consumer tests](https://github.com/ysskrishna/gitingest-action/actions/runs/44367731786) pass for 43b24d1.
