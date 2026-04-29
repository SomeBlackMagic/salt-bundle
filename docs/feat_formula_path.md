# Feature Spec: `formula_path` parameter in `.saltbundle.yaml`

## Goal

Add an optional `formula_path` parameter to `.saltbundle.yaml` that specifies the subdirectory
containing the actual formula files to be packed into the tar archive. When the parameter is
absent, behaviour is identical to the current implementation (the directory containing
`.saltbundle.yaml` is used as the source).

---

## Motivation

A repository may co-locate the formula with other content (CI configs, documentation, tests,
wrapper scripts, etc.) in a subdirectory:

```
my-formula/
├── .saltbundle.yaml      ← project root
├── .saltbundleignore
├── README.md
├── ci/
└── formula/              ← actual Salt formula lives here
    ├── init.sls
    └── _modules/
        └── mymod.py
```

Without `formula_path` the user must either pollute `.saltbundleignore` with every non-formula
path or restructure the repository.

---

## Terminology

| Term | Meaning |
|------|---------|
| `formula_dir` | Directory that contains `.saltbundle.yaml`. Unchanged by this feature. |
| `source_dir` | Directory whose files are packed into the archive. Equals `formula_dir` when `formula_path` is absent, `formula_dir / formula_path` otherwise. |

---

## Changes

### 1. `salt_bundle/models/package_models.py` — `PackageMeta`

Add one optional field:

```python
formula_path: Optional[str] = None
```

**Validation rules (via Pydantic validator):**

- Must be a relative path (must not start with `/`)
- Must not contain `..` components (path traversal protection)
- Normalised with `Path(formula_path).as_posix()` before storage

### 2. `salt_bundle/utils/fs.py` — `load_ignore_patterns`

No signature change. The function already accepts an arbitrary `base_dir`; callers are
responsible for passing the correct directory (see §3 below).

### 3. `salt_bundle/package.py` — `pack_formula`

**New logic:**

```python
formula_dir = Path(formula_dir)

meta = load_package_meta(formula_dir)

# Resolve source directory
if meta.formula_path:
    source_dir = (formula_dir / meta.formula_path).resolve()
    # Safety: source_dir must remain inside formula_dir
    if not source_dir.is_relative_to(formula_dir.resolve()):
        raise ValueError(f"formula_path escapes formula_dir: {meta.formula_path}")
    if not source_dir.is_dir():
        raise FileNotFoundError(f"formula_path does not exist: {source_dir}")
else:
    source_dir = formula_dir
```

**`.saltbundleignore` handling:**

The ignore file is **always** read from `formula_dir` (next to `.saltbundle.yaml`), but the
patterns are matched **relative to `source_dir`** (the directory being packed):

```python
# Load patterns from project root, not from source_dir
patterns = load_ignore_patterns(formula_dir)

# Collect files relative to source_dir using the pre-loaded patterns
files = collect_files(source_dir, patterns)
```

This works because `collect_files` accepts an explicit `patterns` argument and passes it
straight to `should_ignore(path, source_dir, patterns)`, which computes all relative paths
against `source_dir`. When patterns are explicit, `collect_files` does **not** call
`load_ignore_patterns` internally (current behaviour — the `if patterns is None` guard already
handles this).

**Why this is correct:**

| Scenario | `.saltbundleignore` location | Pattern base |
|----------|------------------------------|--------------|
| No `formula_path` | `formula_dir` (= `source_dir`) | `formula_dir` |
| With `formula_path` | `formula_dir` | `source_dir` |

A user writing `.saltbundleignore` patterns like `tests/**` or `*.pyc` is describing paths
**inside the formula** — they should match against whatever directory is being packed, not
against the project root. Keeping the file in `formula_dir` is consistent with where all other
project-level config files live.

**`.saltbundle.yaml` in archive:**

`.saltbundle.yaml` is always added at the **archive root**, regardless of `formula_path`. The
file is read from `formula_dir` and archived as `.saltbundle.yaml` (not as
`<formula_path>/.saltbundle.yaml`):

```python
saltbundle_yaml = formula_dir / '.saltbundle.yaml'
if saltbundle_yaml not in files:
    # Add with explicit arcname so it lands at archive root
    tar.add(saltbundle_yaml, arcname='.saltbundle.yaml')
```

**`.sls` file check:**

The check for at least one `.sls` file must use `source_dir`:

```python
sls_files = list(source_dir.glob('*.sls'))
if not sls_files:
    raise ValueError(f"No .sls files found in source directory: {source_dir}")
```

**Archive entry paths:**

All files from `source_dir` are archived with paths relative to `source_dir` (current
behaviour, path base changes from `formula_dir` to `source_dir`):

```python
with tarfile.open(archive_path, 'w:gz') as tar:
    for file_path in files:
        arcname = file_path.relative_to(source_dir)
        tar.add(file_path, arcname=str(arcname))
```

---

## What does NOT change

- Archive filename: `{name}-{version}.tgz`
- `unpack_formula()` — no changes needed; it already expects `.saltbundle.yaml` at archive root
- `get_package_info()` — reads `.saltbundle.yaml` from archive root; no changes needed
- CLI interface `salt-bundle formula pack` — no new flags required
- Default ignore patterns in `DEFAULT_IGNORE_PATTERNS`

---

## Example

**Directory layout:**

```
my-formula/
├── .saltbundle.yaml     (formula_path: formula)
├── .saltbundleignore    (contains: ci/**)
├── ci/
│   └── pipeline.yml
└── formula/
    ├── init.sls
    ├── config.sls
    └── _modules/
        └── mymod.py
```

**`.saltbundle.yaml`:**

```yaml
name: my-formula
version: 1.0.0
description: Example formula in a subdirectory
formula_path: formula
dependencies: []
```

**`.saltbundleignore`:**

```
ci/**
```

**Resulting archive `my-formula-1.0.0.tgz`:**

```
.saltbundle.yaml        ← from formula_dir (project root)
init.sls                ← from formula/
config.sls              ← from formula/
_modules/mymod.py       ← from formula/
```

`ci/**` in `.saltbundleignore` is not matched against `formula/` contents (no `ci/` there), so
it has no effect here — but if `formula/ci/` existed it would be excluded correctly.

---

## Edge cases

| Case | Expected behaviour |
|------|--------------------|
| `formula_path` is `.` or empty string | Treat as absent; use `formula_dir` |
| `formula_path` points outside `formula_dir` (e.g. `../other`) | Raise `ValueError` |
| `formula_path` directory does not exist | Raise `FileNotFoundError` |
| `.saltbundleignore` absent from `formula_dir` | Only default patterns apply (current behaviour) |
| `.saltbundleignore` present in `source_dir` but not in `formula_dir` | Ignored — file is always loaded from `formula_dir` |
| `formula_path` set, `.saltbundle.yaml` already inside `source_dir` | Must not be double-added to archive |
