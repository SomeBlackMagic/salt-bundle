# Templates/files

## gitfs

gitfs serves all files from a Git repository through the Salt fileserver, including Jinja2 templates, plain text files, binary files, and any other assets placed in the repository. Files are accessible under the `salt://` URL scheme and can be referenced from state files using `source: salt://path/to/file`. The fileserver fetches file content from the local gitfs cache at `/var/cache/salt/master/gitfs/`, streaming it to minions on demand. Template rendering happens on the minion after the file is transferred.

## spm

spm installs formula packages that may contain any combination of `.sls` files, Jinja2 templates, and static file assets. After installation, these files reside in the directory added to `file_roots` and are served by the standard Salt fileserver. Accessing installed files via `salt://` works identically to files placed manually under `file_roots`. There is no special template handling — Jinja2 processing occurs on the minion at apply time.

## salt-bundle

salt-bundle serves templates and static files from vendored formulas through the `bundlefs` fileserver backend. The `find_file()` function in `bundlefs.py` supports standard formula file lookups in the format `formula_name/path/to/file`, mapping them to `vendor/formula_name/path/to/file` on disk. The `file_list()` function enumerates all files under each formula's directory, exposing them with the `formula_name/` prefix. File content is delivered to minions via the `serve_file()` function, which reads files in chunks using the `file_buffer_size` from Salt opts (defaulting to 262144 bytes). File integrity is provided by `file_hash()`, which computes SHA256 (or the configured `hash_type`) for minion-side cache validation.
