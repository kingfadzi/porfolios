#!/bin/bash

# Check if an image name and tag are provided
if [ -z "$1" ]; then
  echo "Usage: skopeo image:tag"
  exit 1
fi

# Extract the image name and tag from the input parameter
IMAGE_TAG="$1"

# Define the base URL for the source registry
BASE_URL="docker://registry.example.com/repo/"

# Construct the source and destination paths
SOURCE="${BASE_URL}${IMAGE_TAG}"
DEST_FILENAME="${IMAGE_TAG//[:\/]/-}.tar"
DESTINATION="docker-archive:${DEST_FILENAME}"

# Check if the destination file exists and remove it if necessary
if [ -f "${DEST_FILENAME}" ]; then
  echo "Removing existing file: ${DEST_FILENAME}"
  rm -f "${DEST_FILENAME}"
fi

# Run skopeo copy inside the container
docker run --rm \
  -v "$(pwd):/workdir" \
  -w /workdir \
  skopeo:latest copy "$SOURCE" "$DESTINATION" --src-tls-verify=false
