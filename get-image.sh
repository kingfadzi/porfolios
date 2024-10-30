#!/bin/bash

BASE_URL="docker://registry.example.com/repo/"  # Replace with your actual registry URL

if [ -z "$1" ]; then
  echo "Usage: ./get-image.sh <image:tag>"
  exit 1
fi

IMAGE_TAG="$1"

IMAGE_NAME=$(echo "$IMAGE_TAG" | cut -d':' -f1)
TAG=$(echo "$IMAGE_TAG" | cut -d':' -f2)

SANITIZED_TAG="${IMAGE_TAG//[:\/]/-}"
DEST_FILENAME="${SANITIZED_TAG}.tar"
DESTINATION="docker-archive:${DEST_FILENAME}"

if [ -f "${DEST_FILENAME}" ]; then
  echo "Removing existing file: ${DEST_FILENAME}"
  rm -f "${DEST_FILENAME}"
fi

echo "Copying ${IMAGE_TAG} from registry..."
docker run --rm \
  -v "$HOME/.docker:/root/.docker:ro" \
  -v "$(pwd):/workdir" \
  -w /workdir \
  skopeo:latest copy "${BASE_URL}${IMAGE_TAG}" "${DESTINATION}"

if [ $? -ne 0 ]; then
  echo "Error: skopeo copy failed."
  exit 1
fi

echo "Copied to ${DEST_FILENAME}"

echo "Loading ${IMAGE_TAG} into Docker..."
docker load -i "${DEST_FILENAME}"

if [ $? -ne 0 ]; then
  echo "Error: docker load failed."
  exit 1
fi

echo "Loaded ${IMAGE_TAG} into Docker."

# echo "Removing ${DEST_FILENAME}..."
# rm -f "${DEST_FILENAME}"
# echo "Removed ${DEST_FILENAME}"

exit 0
