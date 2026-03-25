# Runtime Updates

## gitfs

gitfs supports live runtime updates: as soon as a new commit is pushed to the configured branch, the Salt master's gitfs poller fetches it on the next update cycle. No manual intervention is required on the master. A `salt-run fileserver.update` call can force an immediate fetch. This means that a formula change becomes effective within seconds to minutes without any deployment action — which is convenient for rapid iteration but also means that an unreviewed commit to a live branch immediately affects all managed nodes on their next highstate.

## spm

spm does not support runtime updates. Updating a formula requires an operator to run `spm remove <formula>` followed by `spm install <formula>` (or `spm update` if the repository index has been refreshed). These are explicit, synchronous administrative commands. There is no background poller, no automatic refresh, and no mechanism for the Salt master to detect that a newer version of an installed package is available. Nodes continue to use the previously installed version until a human intervenes.

## salt-bundle

salt-bundle does not support runtime updates. The `vendor/` directory is populated by `salt-bundle project install`, which is a deliberate, explicit operation. No background process watches the repository for new releases. To update a dependency, an operator runs `salt-bundle project update` (which resolves the latest compatible version against the configured constraint, updates `.salt-dependencies.lock`, and re-downloads the package into `vendor/`), followed by re-running highstate. This separation between the install phase and the execution phase is intentional: it prevents unreviewed upstream changes from silently affecting production runs.
