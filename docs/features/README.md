# Full Comparison: gitfs vs spm vs salt-bundle (COMPLETE)

## 1. Architecture and Model

| Criterion                                    | gitfs              | spm             | salt-bundle                         |
|----------------------------------------------|--------------------|-----------------|-------------------------------------|
| [Core model](arch_model.md)                  | Fileserver backend | Package manager | Package manager + dependency system |
| [Delivery type](arch_delivery_type.md)       | runtime pull       | install-time    | install-time (vendor)               |
| [Source](arch_source.md)                     | Git                | .spm packages   | .tgz packages                       |
| [Control center](arch_control_center.md)     | Salt master        | master/minion   | project (local)                     |
| [Pull / Push](arch_pull_push.md)             | Pull               | Push (install)  | Push (artifact)                     |
| [Immutable deploy](arch_immutable_deploy.md) | ❌                  | ⚠️              | ✅                                   |
| [State snapshot](arch_snapshot.md)           | ❌                  | ❌               | ✅                                   |

## 2. Versioning

| Criterion                                     | gitfs            | spm             | salt-bundle |
|-----------------------------------------------|------------------|-----------------|-------------|
| [Version](ver_version.md)                     | branch/tag       | version/release | semver      |
| [Pin version](ver_pin.md)                     | via branch/tag   | yes             | yes         |
| [Semver support](ver_semver.md)               | ❌                | ❌               | ✅           |
| [Version constraints](ver_constraints.md)     | ❌                | ❌               | ✅           |
| [Latest compatible](ver_latest_compatible.md) | ❌                | ❌               | ✅           |
| [Lock file](ver_lockfile.md)                  | ❌                | ❌               | ✅           |
| [Reproducibility](ver_reproducibility.md)     | ❌                | ⚠️              | ✅           |

## 3. Dependency management

| Criterion                                         | gitfs | spm | salt-bundle |
|---------------------------------------------------|-------|-----|-------------|
| [Dependency declaration](dep_declaration.md)      | ❌     | ⚠️  | ✅           |
| [Automatic resolution](dep_auto_resolve.md)       | ❌     | ⚠️  | ✅           |
| [Version constraints](dep_version_constraints.md) | ❌     | ❌   | ✅           |
| [Dependency graph](dep_graph.md)                  | ❌     | ❌   | ⚠️          |
| [Transitive dependencies](dep_transitive.md)      | ❌     | ❌   | ⚠️          |
| [Conflict resolution](dep_conflict.md)            | ❌     | ❌   | ❌           |

## 4. Code and file handling

| Criterion                                 | gitfs | spm | salt-bundle |
|-------------------------------------------|-------|-----|-------------|
| [States (.sls)](files_states.md)          | ✅     | ✅   | ✅           |
| [Modules (_modules)](files_modules.md)    | ✅     | ✅   | ✅           |
| [Pillars](files_pillars.md)               | ⚠️    | ⚠️  | ⚠️          |
| [Templates/files](files_templates.md)     | ✅     | ✅   | ✅           |
| [Runtime access](files_runtime_access.md) | ✅     | ❌   | ❌           |
| [Offline operation](files_offline.md)     | ❌     | ✅   | ✅           |

## 5. Module delivery

| Criterion                                | gitfs               | spm      | salt-bundle |
|------------------------------------------|---------------------|----------|-------------|
| [Sync required](delivery_sync.md)        | ✅                   | ⚠️       | ❌           |
| [Module location](delivery_location.md)  | git cache / extmods | extmods  | vendor/     |
| [Autoload](delivery_autoload.md)         | ❌                   | ❌        | ✅           |
| [Loader integration](delivery_loader.md) | standard            | standard | plugin      |

## 6. Repository model

| Criterion                          | gitfs     | spm          | salt-bundle    |
|------------------------------------|-----------|--------------|----------------|
| [Repo type](repo_type.md)          | Git       | spm repo     | HTTP/file repo |
| [Index](repo_index.md)             | ❌         | SPM-METADATA | index.yaml     |
| [Multiple repos](repo_multiple.md) | ✅         | ✅            | ✅              |
| [Repo priority](repo_priority.md)  | ⚠️        | ❌            | ✅              |
| [CDN support](repo_cdn.md)         | ❌         | ⚠️           | ✅              |
| [Caching](repo_cache.md)           | git cache | spm cache    | package cache  |

## 7. CI/CD integration

| Criterion                                          | gitfs | spm  | salt-bundle |
|----------------------------------------------------|-------|------|-------------|
| [CI-friendly](cicd_friendly.md)                    | ❌     | ⚠️   | ✅           |
| [Build step](cicd_build_step.md)                   | ❌     | ✅    | ✅           |
| [Artifact](cicd_artifact.md)                       | ❌     | .spm | .tgz        |
| [Release pipeline](cicd_release_pipeline.md)       | ❌     | ❌    | ✅           |
| [GitHub/GitLab integration](cicd_github_gitlab.md) | ❌     | ❌    | ⚠️          |
| [Reproducible builds](cicd_reproducible_builds.md) | ❌     | ❌    | ✅           |

## 8. Runtime behavior

| Criterion                                           | gitfs | spm | salt-bundle |
|-----------------------------------------------------|-------|-----|-------------|
| [Runtime network dependency](runtime_network.md)    | ✅     | ❌   | ❌           |
| [Runtime updates](runtime_updates.md)               | ✅     | ❌   | ❌           |
| [Drift possible](runtime_drift.md)                  | ✅     | ⚠️  | ❌           |
| [Deterministic execution](runtime_deterministic.md) | ❌     | ⚠️  | ✅           |

## 9. Performance

| Criterion                           | gitfs  | spm     | salt-bundle |
|-------------------------------------|--------|---------|-------------|
| [Clone overhead](perf_clone.md)     | high   | none    | none        |
| [Fetch overhead](perf_fetch.md)     | yes    | none    | none        |
| [Install overhead](perf_install.md) | none   | medium  | medium      |
| [Runtime latency](perf_latency.md)  | higher | low     | low         |
| [Scalability](perf_scale.md)        | medium | high    | high        |

## 10. Storage

| Criterion                               | gitfs       | spm     | salt-bundle |
|-----------------------------------------|-------------|---------|-------------|
| [Storage location](storage_location.md) | gitfs cache | extmods | vendor      |
| [History](storage_history.md)           | full git    | none    | none        |
| [Size](storage_size.md)                 | large       | medium  | controlled  |
| [Garbage control](storage_garbage.md)   | ❌           | ⚠️      | ✅           |

## 11. Salt integration

| Criterion                                      | gitfs | spm | salt-bundle  |
|------------------------------------------------|-------|-----|--------------|
| [Fileserver backend](salt_fileserver.md)       | ✅     | ❌   | ✅ (bundlefs) |
| [file_roots](salt_file_roots.md)               | ❌     | ❌   | ✅            |
| [Loader plugin](salt_loader_plugin.md)         | ❌     | ❌   | ✅            |
| [Transparent integration](salt_transparent.md) | ❌     | ❌   | ✅            |

## 12. Security

| Criterion                                   | gitfs | spm | salt-bundle |
|---------------------------------------------|-------|-----|-------------|
| [SHA256 verification](sec_sha256.md)        | ❌     | ❌   | ✅           |
| [Immutable artifact](sec_immutable.md)      | ❌     | ❌   | ✅           |
| [Supply chain control](sec_supply_chain.md) | ❌     | ❌   | ✅           |
| [Repo whitelist](sec_repo_whitelist.md)     | ❌     | ❌   | ✅           |
| [GPG signing](sec_gpg.md)                   | ❌     | ❌   | ❌           |

## 13. UX / DX

| Criterion                              | gitfs | spm  | salt-bundle |
|----------------------------------------|-------|------|-------------|
| [Onboarding ease](ux_onboarding.md)    | ✅     | ❌    | ⚠️          |
| [Predictability](ux_predictability.md) | ❌     | ⚠️   | ✅           |
| [Debug](ux_debug.md)                   | hard  | hard | easier      |
| [Dev workflow](ux_dev_workflow.md)     | fast  | slow | medium      |
| [Learning curve](ux_learning_curve.md) | low   | high | medium      |

## 14. Limitations

| Criterion                                     | gitfs  | spm    | salt-bundle |
|-----------------------------------------------|--------|--------|-------------|
| [No dependency system](limit_no_deps.md)      | ✅      | ✅      | ❌           |
| [No lock](limit_no_lock.md)                   | ✅      | ✅      | ❌           |
| [No transitive deps](limit_transitive.md)     | —      | —      | ⚠️          |
| [No conflict resolve](limit_conflict.md)      | —      | —      | ✅           |
| [salt-ssh compatibility](limit_salt_ssh.md)   | —      | —      | ⚠️          |
| [Runtime coupling](limit_runtime_coupling.md) | high   | low    | low         |

## Summary

- gitfs → runtime config management
- spm → package distribution
- salt-bundle → dependency + artifact system

### Notes on gitfs

- **Pillars** — supported via `gitfs_pillar` (ext_pillar backend), available since Salt 2015.8.0
- **Repo priority** — no explicit priority, but remotes are iterated in order; first match wins
- **Module location** — git objects are cached in `gitfs cache`; after `saltutil.sync`, modules are copied to `/var/cache/salt/*/extmods`

### Notes on spm

- **Semver** — the official version format is `YYYYMM` (date-based), not semver; semver is not supported
- **Automatic dependency resolution** — SPM "attempts" to resolve dependencies automatically, but without version constraints and without a reliable algorithm
- **Pillars** — `pillar.example` is renamed to `<name>.sls.orig` on install and placed in the pillar dir; the user must wire it in manually via top.sls

### Notes on salt-bundle

- **Transitive dependencies** — resolved recursively, but version conflicts are not handled
- **Pillars** — the ext_pillar plugin returns only project metadata (paths, formula list); pillar data from formulas is not wired in automatically
- **GitHub/GitLab** — GitHub is fully supported (Releases + Pages); GitLab has partial support
- **salt-ssh** — integration is unstable (requires duplicating entry points)
- **GPG** — not implemented; verification is SHA256 only
