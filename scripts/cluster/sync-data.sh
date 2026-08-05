#!/usr/bin/env bash
set -euo pipefail

LOCAL_ARCHIVE="${1:-/home/chris/Downloads/hyper-kvasir-labeled-images.zip}"
REMOTE_ARCHIVE="${2:-/home/christian.bueno__espol.edu.ec/datasets/hyper-kvasir-labeled-images.zip}"
EXPECTED_SHA256="c603449b1bc0be86948b11d9aea8b2002058a11e6f5499e2a384b9ae9c8dbd3f"

LOCAL_SHA256="$(sha256sum "${LOCAL_ARCHIVE}" | awk '{print $1}')"
if [[ "${LOCAL_SHA256}" != "${EXPECTED_SHA256}" ]]; then
  echo "SHA-256 local inválido: ${LOCAL_SHA256}" >&2
  exit 2
fi

rsync --archive --partial --info=progress2 "${LOCAL_ARCHIVE}" "cedia:${REMOTE_ARCHIVE}"
ssh cedia "sha256sum '${REMOTE_ARCHIVE}'"
