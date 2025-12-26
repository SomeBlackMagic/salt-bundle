# CI/CD Integration Guide

Guide for integrating Salt Bundle with CI/CD pipelines.

## Table of Contents

- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Jenkins](#jenkins)
- [Best Practices](#best-practices)

## GitHub Actions

### Single Formula Repository

Automatically release formula when changed.

**`.github/workflows/release.yml`:**

```yaml
name: Release Formula

on:
  push:
    branches: [main, master]
    paths:
      - '.saltbundle.yaml'
      - '**.sls'
      - '**.jinja'
      - 'files/**'
      - 'templates/**'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Salt Bundle
        run: pip install salt-bundle

      - name: Release Formula
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: |
          salt-bundle repo release \
            --formulas-dir . \
            --single \
            --provider github
```

### Multiple Formulas Repository

Release all changed formulas in monorepo.

**`.github/workflows/release.yml`:**

```yaml
name: Release Formulas

on:
  push:
    branches: [main]
    paths:
      - 'formulas/**'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Salt Bundle
        run: pip install salt-bundle

      - name: Configure Git
        run: |
          git config user.name "$GITHUB_ACTOR"
          git config user.email "$GITHUB_ACTOR@users.noreply.github.com"

      - name: Release Formulas
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: |
          salt-bundle repo release \
            --formulas-dir ./formulas \
            --provider github

      - name: Summary
        run: echo "Released formulas to GitHub Releases"
```

### Selective Formula Release

Release only changed formulas.

**`.github/workflows/release.yml`:**

```yaml
name: Release Changed Formulas

on:
  push:
    branches: [main]
    paths:
      - 'formulas/**'

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      formulas: ${{ steps.detect.outputs.formulas }}
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          fetch-depth: 2

      - name: Detect Changed Formulas
        id: detect
        run: |
          CHANGED=$(git diff --name-only HEAD~1 HEAD | \
            grep '^formulas/' | \
            cut -d/ -f2 | \
            sort -u | \
            jq -R -s -c 'split("\n")[:-1]')
          echo "formulas=$CHANGED" >> $GITHUB_OUTPUT

  release:
    needs: detect-changes
    if: needs.detect-changes.outputs.formulas != '[]'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        formula: ${{ fromJson(needs.detect-changes.outputs.formulas) }}
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Salt Bundle
        run: pip install salt-bundle

      - name: Release ${{ matrix.formula }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: |
          salt-bundle repo release \
            --formulas-dir formulas/${{ matrix.formula }} \
            --single \
            --provider github
```

### Testing Before Release

Add tests before releasing.

**`.github/workflows/test-and-release.yml`:**

```yaml
name: Test and Release

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: |
          pip install salt-bundle
          pip install salt

      - name: Validate Metadata
        run: |
          python3 << 'EOF'
          import yaml
          from salt_bundle.models.package_models import PackageMeta

          with open('.saltbundle.yaml') as f:
              data = yaml.safe_load(f)
              meta = PackageMeta(**data)
              print(f"✓ Valid: {meta.name} {meta.version}")
          EOF

      - name: Test Pack
        run: salt-bundle formula pack --output-dir /tmp

      - name: Test Salt Syntax
        run: |
          salt-call --local --file-root=. state.show_sls $(basename $(pwd))

  release:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Salt Bundle
        run: pip install salt-bundle

      - name: Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: |
          salt-bundle repo release \
            --formulas-dir . \
            --single \
            --provider github
```

### Project Dependency Installation

Install dependencies in CI/CD for testing.

**`.github/workflows/test.yml`:**

```yaml
name: Test Project

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Salt Bundle
        run: pip install salt-bundle

      - name: Add Repository
        run: |
          salt-bundle repo add \
            --name main \
            --url https://yourorg.github.io/salt-formulas/

      - name: Install Dependencies
        run: salt-bundle project install

      - name: Verify Installation
        run: salt-bundle formula verify

      - name: Test States
        run: |
          pip install salt
          salt-call --local \
            --file-root=salt:vendor \
            state.show_top
```

## GitLab CI

### Single Formula Repository

**`.gitlab-ci.yml`:**

```yaml
stages:
  - test
  - release

variables:
  PYTHON_VERSION: "3.10"

test:
  stage: test
  image: python:${PYTHON_VERSION}
  script:
    - pip install salt-bundle salt
    - salt-bundle formula pack --output-dir /tmp
    - salt-call --local --file-root=. state.show_sls $(basename $(pwd))
  only:
    changes:
      - .saltbundle.yaml
      - "*.sls"

release:
  stage: release
  image: python:${PYTHON_VERSION}
  script:
    - pip install salt-bundle
    - |
      salt-bundle repo release \
        --formulas-dir . \
        --single \
        --provider local \
        --pkg-storage-dir ./repo
  artifacts:
    paths:
      - repo/
  only:
    refs:
      - main
    changes:
      - .saltbundle.yaml
      - "*.sls"

pages:
  stage: release
  needs: [release]
  script:
    - mkdir -p public
    - cp -r repo/* public/
  artifacts:
    paths:
      - public
  only:
    refs:
      - main
```

### Multiple Formulas Repository

**`.gitlab-ci.yml`:**

```yaml
stages:
  - release

.release_template:
  stage: release
  image: python:3.10
  script:
    - pip install salt-bundle
    - |
      salt-bundle repo release \
        --formulas-dir formulas/${FORMULA_NAME} \
        --single \
        --provider local \
        --pkg-storage-dir ./repo
  artifacts:
    paths:
      - repo/
  only:
    changes:
      - formulas/${FORMULA_NAME}/**/*

release_nginx:
  extends: .release_template
  variables:
    FORMULA_NAME: nginx

release_mysql:
  extends: .release_template
  variables:
    FORMULA_NAME: mysql

release_redis:
  extends: .release_template
  variables:
    FORMULA_NAME: redis

# Combine all releases
pages:
  stage: release
  needs:
    - release_nginx
    - release_mysql
    - release_redis
  script:
    - mkdir -p public
    - cp -r repo/* public/ 2>/dev/null || true
  artifacts:
    paths:
      - public
  only:
    refs:
      - main
```

### Project Testing

**`.gitlab-ci.yml`:**

```yaml
stages:
  - test

test:
  stage: test
  image: python:3.10
  before_script:
    - pip install salt-bundle salt
    - |
      salt-bundle repo add \
        --name main \
        --url https://formulas.example.com/
  script:
    - salt-bundle project install
    - salt-bundle formula verify
    - |
      salt-call --local \
        --file-root=salt:vendor \
        state.show_top
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - vendor/
```

## Jenkins

### Jenkinsfile for Formula Release

```groovy
pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.10'
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install salt-bundle
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    . venv/bin/activate
                    salt-bundle formula pack --output-dir /tmp
                '''
            }
        }

        stage('Release') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    . venv/bin/activate
                    salt-bundle repo release \
                        --formulas-dir . \
                        --single \
                        --provider local \
                        --pkg-storage-dir /srv/salt-repo
                '''
            }
        }
    }

    post {
        success {
            echo 'Formula released successfully'
        }
        failure {
            echo 'Release failed'
        }
    }
}
```

### Jenkinsfile for Project Testing

```groovy
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install salt-bundle salt
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    . venv/bin/activate
                    salt-bundle repo add \
                        --name main \
                        --url https://formulas.example.com/
                    salt-bundle project install
                '''
            }
        }

        stage('Verify') {
            steps {
                sh '''
                    . venv/bin/activate
                    salt-bundle formula verify
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    . venv/bin/activate
                    salt-call --local \
                        --file-root=salt:vendor \
                        state.show_top
                '''
            }
        }
    }
}
```

## Best Practices

### Caching

**GitHub Actions:**

```yaml
- name: Cache Salt Bundle
  uses: actions/cache@v3
  with:
    path: |
      ~/.cache/salt-bundle
      vendor/
    key: ${{ runner.os }}-salt-bundle-${{ hashFiles('.salt-dependencies.lock') }}
    restore-keys: |
      ${{ runner.os }}-salt-bundle-
```

**GitLab CI:**

```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - .cache/salt-bundle/
    - vendor/
```

### Security

**Use secrets for tokens:**

```yaml
# GitHub Actions
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# GitLab CI
env:
  GITHUB_TOKEN: $CI_JOB_TOKEN
```

**Don't commit tokens:**

```bash
# .gitignore
.env
*.token
secrets/
```

### Version Bumping

**Automatic version bump:**

```yaml
- name: Bump Version
  run: |
    VERSION=$(git describe --tags --abbrev=0 | awk -F. '{$NF+=1; print $0}' OFS=.)
    sed -i "s/version: .*/version: $VERSION/" .saltbundle.yaml
    git add .saltbundle.yaml
    git commit -m "Bump version to $VERSION"
    git tag "$VERSION"
    git push --tags
```

### Notifications

**Slack notification (GitHub Actions):**

```yaml
- name: Notify Slack
  if: success()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Formula ${{ github.event.repository.name }} released successfully"
      }
```

### Dry Run in PR

Test releases in pull requests:

```yaml
on:
  pull_request:
    branches: [main]

jobs:
  dry-run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install Salt Bundle
        run: pip install salt-bundle
      - name: Dry Run Release
        run: |
          salt-bundle repo release \
            --formulas-dir . \
            --single \
            --provider local \
            --pkg-storage-dir /tmp/test \
            --dry-run
```

### Matrix Testing

Test multiple Salt versions:

```yaml
strategy:
  matrix:
    salt-version: ['3006', '3007', '3008', '3009']

steps:
  - name: Test with Salt ${{ matrix.salt-version }}
    run: |
      pip install salt==${{ matrix.salt-version }}
      salt-call --version
      salt-call --local state.show_sls myformula
```

### Parallel Releases

Release multiple formulas in parallel:

```yaml
strategy:
  matrix:
    formula: [nginx, mysql, redis, postgresql]
  max-parallel: 4

steps:
  - name: Release ${{ matrix.formula }}
    run: |
      salt-bundle repo release \
        --formulas-dir formulas/${{ matrix.formula }} \
        --single \
        --provider github
```

## Troubleshooting

### Permission Denied

**Problem:** `Error: Permission denied when pushing to gh-pages`

**Solution:** Ensure `GITHUB_TOKEN` has write permissions:

```yaml
permissions:
  contents: write  # For pushing to gh-pages
```

### Rate Limiting

**Problem:** `Error: API rate limit exceeded`

**Solution:** Use authenticated requests and cache:

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

- name: Cache
  uses: actions/cache@v3
  with:
    path: ~/.cache/salt-bundle
    key: ${{ runner.os }}-salt-bundle
```

### Network Timeouts

**Problem:** `Error: Connection timeout`

**Solution:** Increase timeout and add retries:

```bash
salt-bundle project install --timeout 300 || \
salt-bundle project install --timeout 300 || \
salt-bundle project install --timeout 300
```

## Next Steps

- [Publishing Guide](publishing-guide.md) - Manual publishing
- [Repository Setup](repository-setup.md) - Setting up repositories
- [CLI Reference](cli-reference.md) - All commands
