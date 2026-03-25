# CDN Support

## gitfs

gitfs does not support CDN distribution. Git repositories require Git protocol support (SSH or smart HTTP), which CDNs do not provide. While a Git hosting service like GitHub may use a CDN for its web interface, the actual `git clone` and `git fetch` operations bypass CDN layers. The Salt master always fetches directly from the configured Git remote. Distributing a gitfs-backed formula at scale requires a properly scaled Git hosting solution, not a CDN.

## spm

spm has partial CDN support. Because `.spm` files are served over plain HTTP/HTTPS and the `SPM-METADATA` index is a static file, a CDN can in principle cache and serve both. However, there is no mechanism in spm for generating CDN-friendly URLs with content-addressed paths (e.g., URLs containing a hash), so cache invalidation relies entirely on HTTP cache headers. In practice, spm repositories are typically served from a single HTTP server rather than a CDN. Authentication and dynamic metadata generation further complicate CDN integration.

## salt-bundle

salt-bundle is designed for CDN-friendly distribution. Repository packages are `.tgz` files with content-addressed cache keys (SHA256 digest) stored in the `index.yaml` under `digest: sha256:<hex>`. The `download_package()` function in `repository.py` constructs absolute download URLs by joining `base_url` with the package filename, making it straightforward to publish packages on any static hosting service (GitHub Pages, S3, Cloudflare R2, etc.) and front it with a CDN. Because the index references packages by URL and every download is verified against a SHA256 digest, CDN caching is safe — even if a CDN serves a stale version of a file, the digest mismatch will be detected and the download rejected. GitHub Releases and GitHub Pages are explicitly supported as first-class hosting targets.
