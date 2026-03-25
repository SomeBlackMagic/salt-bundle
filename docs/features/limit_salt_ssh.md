# salt-ssh compatibility

## gitfs

gitfs is incompatible with salt-ssh by design. gitfs is a fileserver backend that runs on the Salt master process. salt-ssh operates in a masterless mode — it bundles states and modules into a thin client that is pushed to the target host over SSH, without a running master. The gitfs backend is never consulted in this path. To use gitfs-hosted states with salt-ssh, the operator would need to manually clone the repository on each target, which defeats the purpose of gitfs.

## spm

SPM-installed formulas are installed to the master's `extmods/` directory and are available to minions via the standard Salt sync mechanism. salt-ssh's thin client bundling does pick up files from `extmods/` if the thin client is configured to include them, but this is not automatic and requires explicit configuration of `thin_extra_mods`. The level of support is partial and untested in most SPM-based deployments. SPM itself has no special awareness of salt-ssh and provides no tooling to prepare a salt-ssh-compatible bundle.

## salt-bundle

salt-bundle's salt-ssh integration is currently unstable. The loader plugin (`ext/loader.py`) registers Salt extension directories (modules, states, grains, etc.) via Python entry points. These entry points are discovered by Salt's standard loader when the master or minion starts, but salt-ssh uses a separate thin-client bundling path that does not run the same entry point discovery. As a result, the vendor formulas registered through the loader plugin are not automatically included in the salt-ssh thin client. The `ext/pillar/saltbundle.py` notes that the integration requires duplicating entry points for the thin-client context. This is a known architectural issue stemming from salt-ssh's different module loading path, and no clean solution is currently implemented.
