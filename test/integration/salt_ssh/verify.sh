#!/usr/bin/env bash
set -euo pipefail
cd /tmp/salt-pkg

salt-ssh -c etc/salt-ssh --out=json kitchen-target cp.list_states > /tmp/salt-ssh-states.json
salt-ssh -c etc/salt-ssh --out=json kitchen-target state.show_top > /tmp/salt-ssh-top.json
salt-ssh -c etc/salt-ssh --out=json kitchen-target test_module.ping > /tmp/salt-ssh-module.json
salt-ssh -c etc/salt-ssh --out=json kitchen-target state.sls foo test=True > /tmp/salt-ssh-state.json

mkdir -p etc/salt-ssh-no-tops
sed '/^master_tops:/,$d' etc/salt-ssh/master > etc/salt-ssh-no-tops/master
salt-ssh -c etc/salt-ssh-no-tops --out=json kitchen-target state.show_top > /tmp/salt-ssh-top-without-provider.json

salt_python=(/opt/saltstack/salt/bin/python3.*)
"${salt_python[0]}" - <<'PY'
import json
from pathlib import Path

states = json.loads(Path('/tmp/salt-ssh-states.json').read_text())['kitchen-target']
assert 'foo' in states, states
assert 'example.foo-formula' not in states, states

top = json.loads(Path('/tmp/salt-ssh-top.json').read_text())['kitchen-target']['base']
assert 'kitchen_base' in top, top
assert 'foo' in top, top
without_provider = json.loads(
    Path('/tmp/salt-ssh-top-without-provider.json').read_text()
)['kitchen-target']['base']
assert without_provider == ['kitchen_base'], without_provider

module = json.loads(Path('/tmp/salt-ssh-module.json').read_text())['kitchen-target']
assert module == 'module loaded', module

applied = json.loads(Path('/tmp/salt-ssh-state.json').read_text())['kitchen-target']
assert any('foo_ready' in key for key in applied), applied
assert all(value['result'] is not False for value in applied.values()), applied
print('With master_tops:', top)
print('Without master_tops:', without_provider)
print('Loaded module:', module)
print('Applied SLS:', list(applied))
PY
