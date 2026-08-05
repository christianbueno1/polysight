#!/usr/bin/env bash
set -euo pipefail

: "${1:?Uso: $0 git@github.com:usuario/polysight.git [directorio-remoto]}"
REPOSITORY_URL="$1"
REMOTE_DIR="${2:-/home/christian.bueno__espol.edu.ec/polysight}"

ssh cedia "git clone '${REPOSITORY_URL}' '${REMOTE_DIR}' && cd '${REMOTE_DIR}' && git checkout dev"
