# Local formula development

Salt Bundle does not support a `type: path` repository or vendored symlinks.
Every dependency is resolved through an `index.yaml` repository and installed
from a verified archive.

For local development, create a local repository instead:

```bash
mkdir -p /srv/salt-packages
salt-bundle formula pack --output-dir /srv/salt-packages
salt-bundle repo index /srv/salt-packages
```

Point the project's `Saltfile` at the local index:

```yaml
dependencies:
  - name: my-formula
    version: "^1.0.0"
    source: file:///srv/salt-packages
```

Run `salt-bundle project update` after repacking the formula. This keeps the
same integrity and lock-file behaviour as a remote repository.
