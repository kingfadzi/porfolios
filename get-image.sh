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
ß
# Construct the source and destination paths
SOURCE="${BASE_URL}${IMAGE_TAG}"
DESTINATION="docker-archive:${IMAGE_TAG//[:\/]/-}.tar"

# Run skopeo copy inside the container
docker run --rm \
  -v "$(pwd):/workdir" \
  -w /workdir \
  skopeo:latest copy "$SOURCE" "$DESTINATION"
