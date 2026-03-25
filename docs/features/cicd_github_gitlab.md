# GitHub/GitLab integration

## gitfs

gitfs integrates with GitHub and GitLab only as generic Git remote hosts: it clones or fetches from any `https://` or `git://` URL. There is no use of the GitHub/GitLab API, no release creation, no asset upload, no Pages deployment, and no webhook support. Authentication is handled via SSH keys or HTTPS credentials configured on the Salt master. The integration is passive — gitfs reacts to commits already in the remote, it does not interact with the platform's release or CI infrastructure.

## spm

spm has no native integration with GitHub or GitLab. It can fetch `.spm` files from any HTTP URL, which means a GitHub Pages or GitLab Pages site can technically host an spm repository, but this must be set up and maintained entirely by hand. There is no tooling to create GitHub Releases, upload assets, or update a hosted index from a CI pipeline. GitLab CI and GitHub Actions workflows for spm must be written from scratch using shell scripts.

## salt-bundle

GitHub is fully supported via the `GitHubReleaseProvider` class in `providers/github_provider.py`, which uses the `PyGithub` library (`GitHubReleaser` in `github.py`). For each new formula version, the provider calls `repo.create_git_release()` to create a GitHub Release with tag `{name}-{version}`, then calls `release.upload_asset()` to attach the `.tgz` archive with `content_type='application/gzip'`. If the release already exists (HTTP 422 with `already_exists`), it retrieves the existing release instead of failing. The `index.yaml` is stored on a separate git branch (default: `gh-pages`) via a sequence of `git fetch`, `git checkout --orphan` (if the branch is new), `git add index.yaml`, `git commit`, and `git push origin <branch>` shell commands. Integration with CI requires only two environment variables: `GITHUB_TOKEN` and `GITHUB_REPOSITORY`. GitLab support is partial: the local provider works in any GitLab CI environment, but the GitHub-specific provider class cannot publish to GitLab Releases or GitLab Package Registry without a custom provider implementation.
