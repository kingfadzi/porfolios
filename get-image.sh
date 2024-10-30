#!/bin/bash

# Base registry URL
BASE_URL="docker://registry.example.com/repo/"

# Check for image:tag argument
if [ -z "$1" ]; then
  echo "Usage: ./get-image.sh <image:tag>"
  exit 1
fi

IMAGE_TAG="$1"
SANITIZED_TAG="${IMAGE_TAG//[:\/]/-}"
DEST_FILENAME="${SANITIZED_TAG}.tar"
DESTINATION="docker-archive:${DEST_FILENAME}"

# Remove existing tar file if it exists
if [ -f "${DEST_FILENAME}" ]; then
  echo "Removing existing file: ${DEST_FILENAME}"
  rm -f "${DEST_FILENAME}"
fi

# Copy the image using skopeo
echo "Copying ${IMAGE_TAG} from registry..."
docker run --rm \
  -v "$HOME/.docker:/root/.docker:ro" \
  -v "$(pwd):/workdir" \
  -w /workdir \
  skopeo:latest copy "${BASE_URL}${IMAGE_TAG}" "${DESTINATION}"

# Check if copy was successful
if [ $? -ne 0 ]; then
  echo "Error: skopeo copy failed."
  exit 1
fi

echo "Copied to ${DEST_FILENAME}"

# Load the image into Docker
echo "Loading ${IMAGE_TAG} into Docker..."
docker load -i "${DEST_FILENAME}"

# Check if load was successful
if [ $? -ne 0 ]; then
  echo "Error: docker load failed."
  exit 1
fi

echo "Loaded ${IMAGE_TAG} into Docker."

# Optional: Remove the tar file
# Uncomment the lines below to enable cleanup
# echo "Removing ${DEST_FILENAME}..."
# rm -f "${DEST_FILENAME}"
# echo "Removed ${DEST_FILENAME}"

exit 0
