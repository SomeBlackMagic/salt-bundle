# Pillars

## gitfs

gitfs has **partial pillar support** via a dedicated `gitfs_pillar` ext_pillar backend (rewritten in Salt 2015.8.0). When configured as an `ext_pillar` source, it can serve pillar data from Git repositories — branches and tags map to Salt environments just like the fileserver backend. However, gitfs as a *fileserver* backend alone does not inject pillar data; the `gitfs_pillar` configuration must be set up separately. Example pillar files inside formulas are reachable via `salt://` but are not automatically injected into the pillar namespace — the operator must explicitly configure `ext_pillar` or reference them via `pillar_roots`.

## spm

spm has **partial pillar support**. During package installation, a `pillar.example` file included in the formula is automatically renamed to `<package_name>.sls.orig` and placed in the pillar directory (configured via `spm_pillar_path`, default `/srv/pillar/`). This gives the operator a ready-made pillar template, but it is not activated automatically — the operator must add it to the pillar top file manually. There is no mechanism to automatically expose pillar data to minions, and the `.orig` suffix serves as a reminder that the file is a starting point, not live configuration.

## salt-bundle

salt-bundle includes an `ext_pillar` plugin at `salt_bundle/salt/pillar/saltbundle.py` that injects project metadata into the pillar namespace. It reads `Saltfile`, discovers installed package directories in `vendor/`, and returns a dictionary under `saltbundle` containing the project directory, vendor directory, package names, and paths. This is metadata only: pillar data inside individual packages is not merged automatically. Configure required values in `pillar_roots`.
