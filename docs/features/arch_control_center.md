# Control Center

## gitfs

The **Salt master** is the exclusive control center for gitfs. All configuration — which repositories to mount, which branch maps to which Salt environment, access credentials — lives in the master configuration file (`/etc/salt/master`). Minions have no direct access to Git; they receive file content from the master's fileserver. Changing the set of formulas available requires modifying the master config and restarting or refreshing the fileserver backend. There is no per-project or per-minion configuration for which formulas are used.

## spm

spm can operate on the **master or directly on a minion**, depending on the use case. Running `spm install` on the master places formulas in the master's file_roots; running it on a minion installs to the minion's local extmods directory. The control is split: the master controls what is served to minions through its `file_roots`, but each minion may also have packages installed locally. There is no central project manifest — the state of installed packages must be tracked externally (e.g., by a Salt state that calls `spm.install`).

## salt-bundle

The **local project directory** is the control center. The `.salt-dependencies.yaml` file in the project root defines all repositories and direct dependencies. The `salt-bundle` CLI tool (run by a developer, CI pipeline, or deployment script) reads this file and writes `.salt-dependencies.lock` with resolved versions. There is no Salt master involvement at this stage — the tool operates independently and produces a vendor tree that can be used on any machine. User-level configuration (`~/.config/salt-bundle/config.yaml`, a `UserConfig` model) can add global repositories and an `allowed_repos` whitelist for security enforcement.
