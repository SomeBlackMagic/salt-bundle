#!/usr/bin/env bash
set -euo pipefail

project_dir=/tmp/salt-pkg

rm -rf "$project_dir"
mkdir -p "$project_dir"
cp -a /tmp/salt_bundle /tmp/examples /tmp/docs "$project_dir/"
cp /tmp/pyproject.toml "$project_dir/pyproject.toml"
cp -a /tmp/test_functional "$project_dir/test_functional"

# Install salt-bundle into Salt's Python
sudo /opt/saltstack/salt/bin/pip3 install --no-cache-dir -e "$project_dir"

# Install pytest
sudo /opt/saltstack/salt/bin/pip3 install --no-cache-dir pytest

# Prepare vendor with example packages
mkdir -p "$project_dir/vendor"
cp -a "$project_dir/examples/packages/foo" "$project_dir/vendor/foo"
cp -a "$project_dir/examples/packages/bar" "$project_dir/vendor/bar"

cat > "$project_dir/Saltfile" <<'EOF'
vendor_dir: vendor
EOF

# Run functional tests
cd "$project_dir"
/opt/saltstack/salt/bin/python -m pytest test_functional/ -v --tb=short
