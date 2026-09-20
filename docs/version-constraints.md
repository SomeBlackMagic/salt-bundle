# Version constraints

Salt Bundle uses semantic-version constraints in `Saltfile` and package
metadata. A `Saltfile` dependency is an object, not a name-to-version map:

```yaml
dependencies:
  - name: nginx
    version: "^2.1.5"
    source: https://packages.example.test/salt
```

The optional `source` must point to a repository containing `index.yaml`. If
it is omitted, Salt Bundle checks global repositories in configured order.

## Formats

| Constraint | Meaning | Example matching versions |
|---|---|---|
| `2.1.5` | Exact version | `2.1.5` |
| `^2.1.5` | Compatible releases, before the next major | `2.1.5`, `2.4.0` |
| `~2.1.5` | Patch releases in the same minor line | `2.1.5`, `2.1.9` |
| `*` | Any version | all versions |
| `>=2.0.0,<3.0.0` | Explicit range | `2.x` versions |

Caret constraints follow the left-most non-zero SemVer component: `^1.2.3`
means `>=1.2.3,<2.0.0`; `^0.2.3` means `>=0.2.3,<0.3.0`.

```yaml
dependencies:
  - name: nginx
    version: "2.1.5"
  - name: mysql
    version: "^8.0.0"
  - name: redis
    version: "~7.2.0"
  - name: common
    version: ">=1.0.0,<2.0.0"
```

## Resolution

`salt-bundle project update` selects the latest available version that matches
each constraint, resolves transitive dependencies, writes `Saltfile.lock`, and
installs the result. `salt-bundle project install` uses the exact locked
versions without resolving again.

When no source is set, repository priority comes from global configuration:

```yaml
# ~/.config/salt-bundle/config.yaml
repositories:
  - name: primary
    url: https://packages.example.test/primary
  - name: fallback
    url: https://packages.example.test/fallback
```

The first source offering a compatible version is selected. To make selection
unambiguous, put the repository URL on the dependency:

```yaml
dependencies:
  - name: nginx
    version: "^2.0.0"
    source: https://packages.example.test/fallback
```

## Recommendations

- Use `^` for normal compatible upgrades.
- Use `~` when only patch upgrades are acceptable.
- Pin an exact version only when required for compatibility or incident
  mitigation.
- Commit `Saltfile.lock`; use `project update` deliberately and deploy with
  `project install`.
- Declare package-to-package requirements in `FORMULA` or `EXTENSION` using
  their package metadata schema; the project manifest remains a list.
