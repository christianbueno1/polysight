#!/usr/bin/env bash
set -euo pipefail

REMOTE_DIR="${1:-/home/christian.bueno__espol.edu.ec/projects/polysight}"
ssh cedia "cd '${REMOTE_DIR}' && git fetch origin dev && git checkout dev && git pull --ff-only origin dev"
