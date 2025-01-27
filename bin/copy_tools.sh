#!/usr/bin/env bash

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <destination-directory>"
  exit 1
fi

DEST=$1
echo "Destination: $DEST"

# 1. cloc
if [ ! -f /usr/local/bin/cloc ]; then
  echo "Error: /usr/local/bin/cloc not found."
  exit 1
fi
mkdir -p "${DEST}/tools/cloc"
echo "Copying cloc..."
cp /usr/local/bin/cloc "${DEST}/tools/cloc/"

# 2. kantra
if [ ! -f /usr/local/bin/kantra ]; then
  echo "Error: /usr/local/bin/kantra not found."
  exit 1
fi
mkdir -p "${DEST}/tools/kantra"
echo "Copying kantra..."
cp /usr/local/bin/kantra "${DEST}/tools/kantra/"

# 2a. .kantra config
if [ ! -d /root/tools/.kantra ]; then
  echo "Error: /root/tools/.kantra directory not found."
  exit 1
fi
echo "Copying .kantra config..."
cp -r /root/tools/.kantra/* "${DEST}/tools/kantra/"

# 3. go-enry
if [ ! -f /usr/local/bin/go-enry ]; then
  echo "Error: /usr/local/bin/go-enry not found."
  exit 1
fi
mkdir -p "${DEST}/tools/go-enry"
echo "Copying go-enry..."
cp /usr/local/bin/go-enry "${DEST}/tools/go-enry/"

# 4. lizard
if [ ! -f /usr/local/bin/lizard ]; then
  echo "Error: /usr/local/bin/lizard not found."
  exit 1
fi
mkdir -p "${DEST}/tools/lizard"
echo "Copying lizard..."
cp /usr/local/bin/lizard "${DEST}/tools/lizard/"

# 5. semgrep (directory)
if [ ! -d /usr/local/bin/semgrep ]; then
  echo "Error: /usr/local/bin/semgrep directory not found."
  exit 1
fi
mkdir -p "${DEST}/tools/semgrep"
echo "Copying semgrep..."
cp -r /usr/local/bin/semgrep/* "${DEST}/tools/semgrep/"

# 6. grype
if [ ! -d /usr/local/bin/grype ]; then
  echo "Error: /usr/local/bin/grype directory not found."
  exit 1
fi
mkdir -p "${DEST}/tools/grype"
echo "Copying grype..."
cp -r /usr/local/bin/grype/* "${DEST}/tools/grype/"

# 6a. grype DB
if [ ! -d /root/.cache/grype/db/5 ]; then
  echo "Error: /root/.cache/grype/db/5 directory not found."
  exit 1
fi
echo "Copying grype DB..."
cp -r /root/.cache/grype/db/5 "${DEST}/tools/grype/"

# 7. syft
if [ ! -d /usr/local/bin/syft ]; then
  echo "Error: /usr/local/bin/syft directory not found."
  exit 1
fi
mkdir -p "${DEST}/tools/syft"
echo "Copying syft..."
cp -r /usr/local/bin/syft/* "${DEST}/tools/syft/"

# 8. trivy
if [ ! -f /usr/local/bin/trivy ]; then
  echo "Error: /usr/local/bin/trivy not found."
  exit 1
fi
mkdir -p "${DEST}/tools/trivy"
echo "Copying trivy..."
cp /usr/local/bin/trivy "${DEST}/tools/trivy/"

# 8a. trivy DB
if [ ! -d /root/.cache/trivy/db ]; then
  echo "Error: /root/.cache/trivy/db directory not found."
  exit 1
fi
echo "Copying trivy DB..."
cp -r /root/.cache/trivy/db "${DEST}/tools/trivy/"

# 9. semgrep-rules
if [ ! -d /root/.semgrep/semgrep-rules ]; then
  echo "Error: /root/.semgrep/semgrep-rules directory not found."
  exit 1
fi
echo "Copying semgrep-rules..."
cp -r /root/.semgrep/semgrep-rules "${DEST}/tools/semgrep/"

echo "Done."
