#!/bin/sh
set -e

if [ -x /opt/saltstack/salt/bin/python3 ]; then
  PYTHON=/opt/saltstack/salt/bin/python3
elif [ -x /usr/bin/python3 ]; then
  PYTHON=/usr/bin/python3
else
  echo "ERROR: Salt python not found" >&2
  exit 1
fi

export PYTHONPATH="/opt/saltstack/salt-bundle/lib:/opt/saltstack/salt-bundle/vendor:${PYTHONPATH}"
exec "$PYTHON" -m salt_bundle "$@"
