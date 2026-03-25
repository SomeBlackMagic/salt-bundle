# Pull / Push

## gitfs

gitfs uses a **Pull** model. The Salt master periodically pulls changes from configured Git remotes into its local cache. Minions then pull file content from the master's fileserver on demand. No one pushes formulas to the master — the master autonomously fetches from remotes on its update schedule (controlled by `gitfs_update_interval`, default 60 seconds). The entire flow is inbound: remotes → master cache → minion runtime.

## spm

spm uses a **Push (install)** model. An administrator explicitly pushes packages onto the target system by running `spm install <package>`. The command downloads the `.spm` archive from a configured repository, extracts it to the install path, and updates the state database. This is a one-time imperative action — there is no background polling or automatic re-pull. If the repository contents change, the administrator must run `spm install` again to push the updated version to the system.

## salt-bundle

salt-bundle uses a **Push (artifact)** model. A developer or CI pipeline runs `salt-bundle project update` to resolve, download, and install all formula packages into the `vendor/` directory. The resulting vendor tree (and the `.salt-dependencies.lock` file) is then distributed as an artifact — committed to version control, packaged into a container image, or deployed via a deployment pipeline. Salt consumes the already-installed artifacts through the loader plugin without pulling from any remote at runtime. The push happens at build/deploy time, not at execution time.
