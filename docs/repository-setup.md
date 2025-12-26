# Repository Setup Guide

Guide for setting up and maintaining Salt formula repositories.

## Table of Contents

- [Repository Types](#repository-types)
- [Local Repository](#local-repository)
- [HTTP Repository](#http-repository)
- [GitHub Repository](#github-repository)
- [Repository Structure](#repository-structure)
- [Maintenance](#maintenance)

## Repository Types

Salt Bundle supports three repository types:

| Type | URL Format | Use Case |
|------|------------|----------|
| **Local** | `file:///path/to/repo` | Development, testing, private networks |
| **HTTP/HTTPS** | `https://example.com/repo/` | Production, CDN, enterprise |
| **GitHub** | GitHub Releases + Pages | Open source, CI/CD automation |

## Local Repository

### Setup

```bash
# 1. Create repository directory
mkdir -p /srv/salt-repo
cd /srv/salt-repo

# 2. Copy formula packages
cp /path/to/formula-1.0.0.tgz .
cp /path/to/another-formula-2.0.0.tgz .

# 3. Generate index
salt-bundle repo index

# This creates index.yaml
```

### Structure

```
/srv/salt-repo/
├── index.yaml
├── formula-1.0.0.tgz
├── formula-1.0.1.tgz
├── another-formula-2.0.0.tgz
└── another-formula-2.1.0.tgz
```

### Using Local Repository

```bash
# Add repository
salt-bundle repo add --name local --url file:///srv/salt-repo/

# Or in project .saltbundle.yaml
repositories:
  - name: local
    url: file:///srv/salt-repo/
```

### Update Index

```bash
# After adding new packages
cd /srv/salt-repo
cp /path/to/new-formula-3.0.0.tgz .
salt-bundle repo index
```

## HTTP Repository

### Option 1: Simple HTTP Server

**Development/Testing:**

```bash
cd /srv/salt-repo
python3 -m http.server 8080

# Access at: http://localhost:8080/
```

### Option 2: Nginx

**Production:**

```nginx
# /etc/nginx/sites-available/salt-repo
server {
    listen 80;
    server_name salt-formulas.example.com;

    root /srv/salt-repo;
    autoindex on;

    location / {
        try_files $uri $uri/ =404;
    }

    # CORS headers (optional, for browser access)
    add_header Access-Control-Allow-Origin *;
}
```

**Enable:**

```bash
sudo ln -s /etc/nginx/sites-available/salt-repo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 3: Apache

```apache
# /etc/apache2/sites-available/salt-repo.conf
<VirtualHost *:80>
    ServerName salt-formulas.example.com
    DocumentRoot /srv/salt-repo

    <Directory /srv/salt-repo>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
```

**Enable:**

```bash
sudo a2ensite salt-repo
sudo systemctl reload apache2
```

### SSL/HTTPS (Recommended for Production)

```bash
# With Let's Encrypt
sudo certbot --nginx -d salt-formulas.example.com
```

### Using HTTP Repository

```bash
# Add repository
salt-bundle repo add --name prod --url https://salt-formulas.example.com/

# Or in project
repositories:
  - name: prod
    url: https://salt-formulas.example.com/
```

### Base URL in Index

When generating index, specify base URL:

```bash
salt-bundle repo index --base-url https://salt-formulas.example.com/
```

This creates absolute URLs in `index.yaml`:

```yaml
packages:
  nginx:
    - version: 2.0.0
      url: https://salt-formulas.example.com/nginx-2.0.0.tgz
```

Without `--base-url`, URLs are relative (filename only).

## GitHub Repository

### Setup Requirements

- GitHub repository
- GitHub token with `repo` permissions
- GitHub Pages enabled (for index.yaml)

### Configuration

```bash
# Set environment variables
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
export GITHUB_REPOSITORY=yourorg/salt-formulas
```

### Single Formula Release

```bash
cd my-formula
salt-bundle repo release \
  --formulas-dir . \
  --single \
  --provider github
```

**What happens:**
1. Creates GitHub Release tagged `my-formula-1.0.0`
2. Uploads `my-formula-1.0.0.tgz` as release asset
3. Updates `index.yaml` in `gh-pages` branch

### Multiple Formulas Release

```bash
formulas/
  ├── nginx/
  ├── mysql/
  └── redis/

cd formulas
salt-bundle repo release \
  --formulas-dir . \
  --provider github
```

### GitHub Pages Setup

1. **Enable GitHub Pages:**
   - Repository Settings → Pages
   - Source: `gh-pages` branch
   - Save

2. **Access repository:**
```bash
# URL format:
https://yourorg.github.io/salt-formulas/

# Add to project:
salt-bundle repo add \
  --name github \
  --url https://yourorg.github.io/salt-formulas/
```

### CI/CD Automation

See [CI/CD Integration](cicd-integration.md) for automated release workflows.

## Repository Structure

### Flat Structure (Recommended)

```
repo/
├── index.yaml
├── nginx-2.0.0.tgz
├── nginx-2.1.0.tgz
├── mysql-5.7.0.tgz
└── redis-6.2.0.tgz
```

**Pros:** Simple, easy to manage
**Cons:** All files in one directory

### Nested Structure (Alternative)

```
repo/
├── index.yaml
├── nginx/
│   ├── nginx-2.0.0.tgz
│   └── nginx-2.1.0.tgz
├── mysql/
│   └── mysql-5.7.0.tgz
└── redis/
    └── redis-6.2.0.tgz
```

**Pros:** Organized by formula
**Cons:** Requires custom index generation

**Generate nested index:**

```bash
# Generate with subdirectories
cd repo
salt-bundle repo index --base-url https://example.com/repo/

# index.yaml will have correct paths:
# url: nginx/nginx-2.0.0.tgz
```

### index.yaml Format

```yaml
apiVersion: v1
generated: "2025-01-15T10:30:00Z"

packages:
  nginx:
    - version: 2.1.0
      url: nginx-2.1.0.tgz
      digest: sha256:abc123...
      created: "2025-01-15T09:00:00Z"
      keywords: [webserver, nginx]
      maintainers:
        - name: Developer
          email: dev@example.com
      sources:
        - https://github.com/example/nginx-formula

    - version: 2.0.0
      url: nginx-2.0.0.tgz
      digest: sha256:def456...
      created: "2025-01-01T10:00:00Z"

  mysql:
    - version: 5.7.0
      url: mysql-5.7.0.tgz
      digest: sha256:ghi789...
      created: "2025-01-10T11:00:00Z"
```

**Key points:**
- Versions sorted newest first
- Digest is required (sha256)
- URL can be relative or absolute
- Metadata from formula `.saltbundle.yaml` is included

## Maintenance

### Adding New Formula

```bash
# 1. Pack formula
cd /path/to/formula
salt-bundle formula pack --output-dir /srv/salt-repo

# 2. Update index
cd /srv/salt-repo
salt-bundle repo index

# If using base URL:
salt-bundle repo index --base-url https://example.com/repo/
```

### Updating Formula

```bash
# 1. Update version in formula/.saltbundle.yaml
version: 1.1.0

# 2. Pack new version
salt-bundle formula pack --output-dir /srv/salt-repo

# 3. Update index
cd /srv/salt-repo
salt-bundle repo index
```

### Removing Old Versions

```bash
cd /srv/salt-repo

# Remove old package
rm nginx-1.0.0.tgz

# Regenerate index
salt-bundle repo index
```

### Automated Release

**Use `salt-bundle repo release` command:**

```bash
# Local repository
salt-bundle repo release \
  --formulas-dir ./formulas \
  --provider local \
  --pkg-storage-dir /srv/salt-repo

# GitHub repository
export GITHUB_TOKEN=ghp_xxx
export GITHUB_REPOSITORY=org/repo
salt-bundle repo release \
  --formulas-dir ./formulas \
  --provider github
```

**Automated workflow:**
1. Discovers formulas in directory
2. Checks which versions are new
3. Packs new versions
4. Uploads to provider
5. Updates index

See [Publishing Guide](publishing-guide.md) for details.

### Repository Mirroring

**Mirror remote repository locally:**

```bash
#!/bin/bash
REMOTE_REPO="https://salt-formulas.example.com"
LOCAL_REPO="/srv/salt-repo-mirror"

mkdir -p "$LOCAL_REPO"
cd "$LOCAL_REPO"

# Download index
curl -O "$REMOTE_REPO/index.yaml"

# Parse index and download packages
python3 << 'EOF'
import yaml
import requests
import sys

with open('index.yaml') as f:
    index = yaml.safe_load(f)

base_url = sys.argv[1] if len(sys.argv) > 1 else ''

for pkg_name, versions in index.get('packages', {}).items():
    for version in versions:
        url = version['url']
        if not url.startswith('http'):
            url = base_url.rstrip('/') + '/' + url

        filename = url.split('/')[-1]
        print(f"Downloading {filename}...")

        response = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(response.content)
EOF "$REMOTE_REPO"

echo "Mirror complete"
```

### Backup

```bash
# Backup entire repository
tar -czf salt-repo-backup-$(date +%Y%m%d).tar.gz /srv/salt-repo/

# Backup to remote location
rsync -av /srv/salt-repo/ backup-server:/backups/salt-repo/
```

## Security

### Access Control

**Nginx authentication:**

```nginx
server {
    listen 443 ssl;
    server_name salt-formulas.example.com;

    root /srv/salt-repo;

    auth_basic "Salt Repository";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

**Create password file:**

```bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd username
```

**Access with credentials:**

```bash
# In projects, use URL with credentials
salt-bundle repo add \
  --name secure \
  --url https://username:password@salt-formulas.example.com/
```

### Signature Verification (Future Feature)

Currently planned:
- GPG signing of index.yaml
- Verification during install
- Trust chain management

## Performance

### CDN Integration

Use CDN for high-traffic repositories:

```
# Upload to S3/CloudFront, etc.
aws s3 sync /srv/salt-repo/ s3://my-bucket/salt-repo/
aws cloudfront create-invalidation --distribution-id XXX --paths "/*"

# Use CDN URL
salt-bundle repo add \
  --name cdn \
  --url https://cdn.example.com/salt-repo/
```

### Caching Headers

**Nginx:**

```nginx
location ~* \.(tgz|yaml)$ {
    expires 1h;
    add_header Cache-Control "public, immutable";
}
```

### Repository Size

**Monitor size:**

```bash
du -sh /srv/salt-repo/
```

**Cleanup old versions:**

```bash
# Keep only last 3 versions per formula
# (Custom script needed)
```

## Monitoring

### Repository Health Check

```bash
#!/bin/bash
REPO_URL="https://salt-formulas.example.com"

# Check index accessibility
if curl -sf "$REPO_URL/index.yaml" > /dev/null; then
    echo "OK: Index accessible"
else
    echo "ERROR: Index not accessible"
    exit 1
fi

# Validate index format
if curl -s "$REPO_URL/index.yaml" | python3 -m yaml > /dev/null 2>&1; then
    echo "OK: Index valid YAML"
else
    echo "ERROR: Index invalid YAML"
    exit 1
fi

echo "Repository health: OK"
```

### Usage Analytics

**Nginx access log:**

```bash
# Count package downloads
grep -E '\.tgz' /var/log/nginx/access.log | wc -l

# Popular packages
grep -E '\.tgz' /var/log/nginx/access.log | \
  awk '{print $7}' | sort | uniq -c | sort -rn | head -10
```

## Troubleshooting

### Index Not Found

**Problem:** `Error: Index not found`

**Check:**

```bash
# Verify index exists
ls -la /srv/salt-repo/index.yaml

# Verify web server serves it
curl -I https://salt-formulas.example.com/index.yaml

# Regenerate if needed
cd /srv/salt-repo
salt-bundle repo index
```

### Digest Mismatch

**Problem:** `Error: Digest mismatch`

**Solution:**

```bash
# Regenerate index with correct checksums
cd /srv/salt-repo
salt-bundle repo index
```

### Package Not Found

**Problem:** Package in index but not downloadable

**Check:**

```bash
# Verify file exists
ls -la /srv/salt-repo/nginx-2.0.0.tgz

# Verify URL in index.yaml matches file location
cat /srv/salt-repo/index.yaml | grep -A5 nginx
```

## Next Steps

- [Publishing Guide](publishing-guide.md) - Publishing formulas
- [Installation Guide](installation-guide.md) - Using repositories
- [CI/CD Integration](cicd-integration.md) - Automating releases
