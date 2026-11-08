#!/usr/bin/env bash
set -exuo pipefail

mkdir -p /run/sshd /root/.ssh /tmp/salt-pkg/srv/salt /tmp/salt-pkg/etc/salt-ssh
chmod 700 /root/.ssh
ssh-keygen -q -t ed25519 -N '' -f /tmp/salt-pkg/ssh_key
cat /tmp/salt-pkg/ssh_key.pub >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
pgrep -x sshd >/dev/null || /usr/sbin/sshd

cp -a /tmp/salt_bundle /tmp/examples /tmp/salt-pkg/
cp /tmp/pyproject.toml /tmp/salt-pkg/pyproject.toml
cat > /tmp/salt-pkg/kitchen-constraints.txt <<'EOF'
pydantic<2.13
typing-extensions==4.14.1
EOF
/opt/saltstack/salt/bin/pip3 install --no-cache-dir \
  -c /tmp/salt-pkg/kitchen-constraints.txt -e /tmp/salt-pkg

mkdir -p /tmp/salt-pkg/vendor/example
cp -a /tmp/salt-pkg/examples/packages/foo /tmp/salt-pkg/vendor/example/foo-formula
cat > /tmp/salt-pkg/vendor/example/foo-formula/FORMULA <<'EOF'
name: example/foo-formula
version: 1.0.0
top_level_dir: foo
EOF
mkdir /tmp/salt-pkg/vendor/example/foo-formula/foo
mv /tmp/salt-pkg/vendor/example/foo-formula/init.sls /tmp/salt-pkg/vendor/example/foo-formula/foo/init.sls

cat > /tmp/salt-pkg/Saltfile <<'EOF'
vendor_dir: vendor
runtime:
  top_bundle_file: srv/salt/top_bundle.sls
EOF
cat > /tmp/salt-pkg/Saltfile.lock <<'EOF'
dependencies:
  example/foo-formula:
    version: 1.0.0
    repository: local
    url: local
    digest: linked
    type: formula
    source_type: path
    linked: true
EOF
cat > /tmp/salt-pkg/srv/salt/top.sls <<'EOF'
base:
  '*':
    - kitchen_base
EOF
cat > /tmp/salt-pkg/srv/salt/kitchen_base.sls <<'EOF'
kitchen_base:
  test.nop: []
EOF
cat > /tmp/salt-pkg/srv/salt/top_bundle.sls <<'EOF'
base:
  '*':
    - example/foo-formula
EOF
cat > /tmp/salt-pkg/etc/salt-ssh/roster <<'EOF'
kitchen-target:
  host: 127.0.0.1
  user: root
  priv: /tmp/salt-pkg/ssh_key
  ssh_options:
    - StrictHostKeyChecking=no
    - UserKnownHostsFile=/dev/null
EOF
cat > /tmp/salt-pkg/etc/salt-ssh/master <<'EOF'
roster_file: /tmp/salt-pkg/etc/salt-ssh/roster
cachedir: /tmp/salt-pkg/cache
pki_dir: /tmp/salt-pkg/pki
fileserver_backend:
  - roots
  - bundlefs
file_roots:
  base:
    - /tmp/salt-pkg/srv/salt
master_tops:
  salt_bundle: true
EOF

