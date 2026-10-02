#!/usr/bin/env bash
set -euo pipefail

docker build --tag salt-bundle-kitchen:3006 test/docker
