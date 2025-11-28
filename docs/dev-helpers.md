```bash
salt-call --local sys.list_functions sys
salt-call --local sys.doc
salt-call --local sys.argspec
salt-call --local sys.state_doc
salt-call --local sys.list_functions
salt-call --local sys.list_returners
salt-call --local sys.list_renderers
salt-call --local sys.list_modules
salt-call --local sys.list_state_modules
salt-call --local sys.list_outputters
salt-call --local sys.list_master_tops
salt-call --local sys.list_runners
salt-call --local sys.list_utils
salt-call --local sys.list_ext_pillar
salt-call --local sys.list_fileserver_backends
salt-call --local state.show_states

# Test bundlefs fileserver
salt-call --local cp.list_master
salt-call --local cp.list_master_dirs

# Enable bundlefs in config (add to /etc/salt/minion or minion config):
# fileserver_backend:
#   - roots
#   - bundlefs
```