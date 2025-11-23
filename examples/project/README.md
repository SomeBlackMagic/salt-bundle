# SaltBundle Loader Usage Example

After installing `salt-bundle` via pip, Salt will automatically pick up the loader.

## Installation

```bash
pip install salt-bundle
```

## Usage

1. Create `.saltbundle.yaml` in your project root:

```yaml
project: my-infrastructure
vendor_dir: vendor

dependencies:
  nginx: "^1.0.0"
  mysql: "2.3.1"
```

2. Install dependencies:

```bash
salt-bundle vendor
```

3. Run Salt commands from the project directory:

```bash
# Salt will automatically find formulas in vendor/
salt-call state.apply nginx

# Or via salt-ssh
salt-ssh '*' state.apply mysql

# Check that formulas are available
salt-call pillar.get saltbundle
```

## How It Works

1. When executing `salt-call` or `salt-ssh`, Salt loads all installed loaders
2. Our loader (`salt_bundle.loader`) searches for `.saltbundle.yaml` in the current directory
3. Reads `vendor_dir` from the config
4. Automatically adds all formulas from `vendor/` to `file_roots`
5. Formulas become available for use

## Project Structure

```
my-project/
├── .saltbundle.yaml          # Project configuration
├── vendor/                   # Installed formulas
│   ├── nginx/
│   │   ├── init.sls
│   │   └── config.sls
│   └── mysql/
│       ├── init.sls
│       └── install.sls
└── states/                   # Your custom states
    └── webserver.sls
```

## Verification

Make sure the loader is working:

```bash
# Should show formulas from vendor/
salt-call pillar.get saltbundle:formulas

# Check file_roots
salt-call config.get file_roots
```

## No Salt Configuration Required

No changes to `/etc/salt/master` or `/etc/salt/minion` are needed!

The loader is picked up automatically after `pip install salt-bundle`.
