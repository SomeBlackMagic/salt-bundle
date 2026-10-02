#!/usr/bin/env bash
set -euo pipefail

mkdir -p \
  /workspace/var/cache/salt \
  /workspace/var/log/salt \
  /workspace/var/run/salt \
  /workspace/pki/salt/minion

#/opt/saltstack/salt/bin/pip3 install -e /mnt > /dev/null

exec "$@"
