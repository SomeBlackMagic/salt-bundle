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

PYTHON_VERSION=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
VENDOR_DIR="/opt/saltstack/salt-bundle/vendor/python${PYTHON_VERSION}"
if [ ! -d "$VENDOR_DIR" ]; then
  echo "ERROR: No bundled dependencies for Salt Python ${PYTHON_VERSION}" >&2
  exit 1
fi

export PYTHONPATH="/opt/saltstack/salt-bundle/lib:${VENDOR_DIR}:${PYTHONPATH}"
exec "$PYTHON" -m salt_bundle "$@"
