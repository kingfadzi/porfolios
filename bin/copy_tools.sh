#!/usr/bin/env bash

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <destination-directory>"
  exit 1
fi

DEST=$1
echo "Destination: $DEST"

mkdir -p "${DEST}/tools/cloc"
if [ -f /usr/local/bin/cloc ]; then
  echo "Copying cloc"
  cp -v /usr/local/bin/cloc "${DEST}/tools/cloc/" || echo "Failed to copy cloc"
fi

mkdir -p "${DEST}/tools/kantra"
if [ -f /usr/local/bin/kantra ]; then
  echo "Copying kantra"
  cp -v /usr/local/bin/kantra "${DEST}/tools/kantra/" || echo "Failed to copy kantra"
fi
if [ -d /root/tools/.kantra ]; then
  echo "Copying .kantra config"
  cp -rv /root/tools/.kantra/* "${DEST}/tools/kantra/" || echo "Failed to copy .kantra"
fi

mkdir -p "${DEST}/tools/go-enry"
if [ -f /usr/local/bin/go-enry ]; then
  echo "Copying go-enry"
  cp -v /usr/local/bin/go-enry "${DEST}/tools/go-enry/" || echo "Failed to copy go-enry"
fi

mkdir -p "${DEST}/tools/lizard"
if [ -f /usr/local/bin/lizard ]; then
  echo "Copying lizard"
  cp -v /usr/local/bin/lizard "${DEST}/tools/lizard/" || echo "Failed to copy lizard"
fi

mkdir -p "${DEST}/tools/semgrep"
if [ -d /usr/local/bin/semgrep ]; then
  echo "Copying semgrep"
  cp -rv /usr/local/bin/semgrep/* "${DEST}/tools/semgrep/" || echo "Failed to copy semgrep"
fi

mkdir -p "${DEST}/tools/grype"
if [ -d /usr/local/bin/grype ]; then
  echo "Copying grype"
  cp -rv /usr/local/bin/grype/* "${DEST}/tools/grype/" || echo "Failed to copy grype"
fi
if [ -d /root/.cache/grype/db/5 ]; then
  echo "Copying grype DB"
  cp -rv /root/.cache/grype/db/5 "${DEST}/tools/grype/" || echo "Failed to copy grype DB"
fi

mkdir -p "${DEST}/tools/syft"
if [ -d /usr/local/bin/syft ]; then
  echo "Copying syft"
  cp -rv /usr/local/bin/syft/* "${DEST}/tools/syft/" || echo "Failed to copy syft"
fi

mkdir -p "${DEST}/tools/trivy"
if [ -f /usr/local/bin/trivy ]; then
  echo "Copying trivy"
  cp -v /usr/local/bin/trivy "${DEST}/tools/trivy/" || echo "Failed to copy trivy"
fi
if [ -d /root/.cache/trivy/db ]; then
  echo "Copying trivy DB"
  cp -rv /root/.cache/trivy/db "${DEST}/tools/trivy/" || echo "Failed to copy trivy DB"
fi

if [ -d /root/tools/semgrep/semgrep-rules ]; then
  echo "Copying semgrep-rules"
  cp -rv /root/tools/semgrep/semgrep-rules "${DEST}/tools/semgrep/" || echo "Failed to copy semgrep-rules"
fi

echo "Done."
