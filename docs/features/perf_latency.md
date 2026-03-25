# Runtime latency

## gitfs

gitfs introduces higher runtime latency compared to local-filesystem backends. When a minion requests a file, the Salt master must look up the file in its gitfs cache. If the cache is stale (the background update has not completed yet), the master may serve an older version or wait for the fetch to finish. The file lookup involves walking the git object tree, which is slower than a direct filesystem `stat` call. With many formula repositories configured, the gitfs backend must search through all of them for each file request. This overhead is small per file (typically single-digit milliseconds) but accumulates over a large highstate that references many formula files.

## spm

spm has low runtime latency. Installed formula files reside in local directories that Salt reads via its standard file_roots mechanism — a simple filesystem lookup with no intermediary layer. There is no git object store traversal, no network call, and no archive extraction during state rendering. The performance characteristics of spm-installed formulas at runtime are identical to hand-placed formula files in `/srv/salt/`.

## salt-bundle

salt-bundle has low runtime latency comparable to spm. The `bundlefs` fileserver backend's `find_file()` function performs a direct `os.path.isfile()` check on the absolute path constructed from the `vendor/` directory. The `_get_vendor_roots()` function caches the list of vendor subdirectory paths in the process-local `_CACHE['vendor_roots']` list, so repeated file lookups within the same Salt master process avoid redundant filesystem scans. File content is served via `serve_file()` using Python's standard `open()` and `fp.seek()`/`fp.read()` with the configurable `file_buffer_size` (default 256 KB), which is the same chunked serving mechanism used by Salt's built-in fileserver backends.
