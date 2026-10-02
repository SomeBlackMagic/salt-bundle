#!/usr/bin/env bash
set -euo pipefail

project_dir=/tmp/salt-pkg

rm -rf "$project_dir"
mkdir -p "$project_dir"
cp -a /tmp/salt_bundle /tmp/examples /tmp/docs "$project_dir/"
cp /tmp/pyproject.toml "$project_dir/pyproject.toml"
cp /tmp/test_loader.sh "$project_dir/test_loader.sh"
cp /tmp/Saltfile "$project_dir/Saltfile"

sudo /opt/saltstack/salt/bin/pip3 install --no-cache-dir -e "$project_dir"
mkdir -p "$project_dir/vendor"
cp -a "$project_dir/examples/packages/foo" "$project_dir/vendor/foo"
