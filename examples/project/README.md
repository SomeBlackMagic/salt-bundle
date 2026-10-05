# Salt Bundle Project Example

Minimal project showing how salt-bundle integrates with Salt.

## Project Structure

```
my-project/
├── Saltfile                # Project config: dependencies and vendor path
├── Saltfile.lock           # Generated lock file with pinned versions
├── salt/                   # Your custom states and target activation
│   ├── top.sls             # Standard Salt top file (state → target mapping)
│   ├── top_bundle.sls      # Optional: target-specific formula activation
│   └── webserver/
│       └── init.sls
└── vendor/                 # Installed formulas (managed by salt-bundle)
    ├── foo/
    │   ├── _modules/
    │   ├── _states/
    │   ├── _grains/
    │   └── defaults.sls
    └── bar/
        └── init.sls
```

## Quick Start

```bash
# 1. Install salt-bundle into Salt's Python environment
pip install salt-bundle

# 2. Initialize a new project (creates Saltfile)
salt-bundle project init

# 3. Edit Saltfile to declare dependencies
cat Saltfile
# vendor_dir: vendor
# dependencies:
#   - name: foo
#     version: "^0.1.0"
#     source: https://formulas.example.com/

# 4. Resolve and install dependencies into vendor/
salt-bundle project update

# 5. Run Salt — formulas are discovered automatically
salt-call --local state.apply foo
salt-call --local grains.get test_grain
```

## How It Works

After `pip install salt-bundle`, Salt automatically loads the `salt.loader` entry
points registered by the package. No changes to `/etc/salt/master` or
`/etc/salt/minion` are needed.

On every `salt-call` / `salt-ssh` invocation:

1. The loader plugin finds `Saltfile` in the current directory (or parents)
2. Reads `vendor_dir` to locate installed formulas
3. Registers formula directories with Salt's loader (`_modules`, `_states`,
   `_grains`, `_renderers`, etc.)
4. The bundlefs fileserver backend serves formula state files

## Saltfile Format

```yaml
vendor_dir: vendor

dependencies:
  - name: foo
    version: "^0.1.0"
    source: https://formulas.example.com/

runtime:
  top_bundle_file: salt/top_bundle.sls  # target-aware activation rules (default)
  cache_dir: .salt-bundle/runtime
  max_workers: 4
```

## Target-Aware Activation (Optional)

`top_bundle.sls` controls which formulas are active for which minions:

```yaml
base:
  '*web*':
    - nginx
  '*db*':
    - mysql
```

Inspect activation with CLI:

```bash
salt-bundle runtime resolve web01
salt-bundle runtime explain web01
salt-bundle runtime validate
salt-bundle runtime matrix 'web01' 'db01'
```

## Verification

```bash
# Check that the loader discovers formulas
salt-call --local pillar.get saltbundle:formulas

# List loaded modules from vendor formulas
salt-call --local sys.list_modules | grep test_module

# List loaded states
salt-call --local sys.list_state_modules | grep test_state
```

## Reproducible Deployment

```bash
# On another machine / in CI — install exact pinned versions from lock file
salt-bundle project install
```

## Local Formula Development

For a local development loop, point a dependency directly at a package source
directory. The path is resolved relative to this `Saltfile`; no archive or
`index.yaml` is required.

```yaml
dependencies:
  - name: foo
    source: path://../packages/foo
```

`salt-bundle project update` copies a snapshot into `vendor/`. Re-run it after
changing the local package.

To make source changes visible immediately, opt into link mode:

```yaml
dependencies:
  - name: foo
    source: path://../packages/foo
    link: true
```

Link mode creates `vendor/foo` as a symlink and records `digest: linked` in
`Saltfile.lock`; use it for local development, not portable CI deployments.

For a directory containing several packages, configure a global source
repository and omit `source` from the dependency:

```yaml
# ~/.config/salt-bundle/config.yaml
repositories:
  - name: local-formulas
    url: /home/user/workspace/formulas
    type: path-source
```
