#!/usr/bin/env bash

#
# Usage:
#   ./copy_tools.sh /path/to/destination
#
# Example:
#   ./copy_tools.sh /mnt/backup
#

# Exit on errors or unset variables
set -euo pipefail

# Check if user provided the destination directory argument
if [ $# -lt 1 ]; then
  echo "Usage: $0 <destination-directory>"
  exit 1
fi

DEST=$1

echo "Copying tools to $DEST ..."

# 1. Copy cloc
mkdir -p "${DEST}/tools/cloc"
cp /usr/local/bin/cloc "${DEST}/tools/cloc/"

# 2. Copy kantra
mkdir -p "${DEST}/tools/kantra"
cp /usr/local/bin/kantra "${DEST}/tools/kantra/"
cp -r /root/tools/.kantra/* "${DEST}/tools/kantra/" 2>/dev/null || true

# 3. Copy go-enry
mkdir -p "${DEST}/tools/go-enry"
cp /usr/local/bin/go-enry "${DEST}/tools/go-enry/"

# 4. Copy lizard
mkdir -p "${DEST}/tools/lizard"
cp /usr/local/bin/lizard "${DEST}/tools/lizard/"

# 5. Copy semgrep
mkdir -p "${DEST}/tools/semgrep"
# If /usr/local/bin/semgrep is a directory, copy recursively
cp -r /usr/local/bin/semgrep/* "${DEST}/tools/semgrep/" 2>/dev/null || true

# 6. Copy grype
mkdir -p "${DEST}/tools/grype"
cp -r /usr/local/bin/grype/* "${DEST}/tools/grype/" 2>/dev/null || true
cp -r /root/.cache/grype/db/5 "${DEST}/tools/grype/" 2>/dev/null || true

# 7. Copy syft
mkdir -p "${DEST}/tools/syft"
cp -r /usr/local/bin/syft/* "${DEST}/tools/syft/" 2>/dev/null || true

# 8. Copy trivy
mkdir -p "${DEST}/tools/trivy"
cp /usr/local/bin/trivy "${DEST}/tools/trivy/" 2>/dev/null || true
cp -r /root/.cache/trivy/db "${DEST}/tools/trivy/" 2>/dev/null || true

# 9. Copy semgrep rules
cp -r /root/.semgrep/semgrep-rules "${DEST}/tools/semgrep/" 2>/dev/null || true

echo "Done copying tools to ${DEST}."
