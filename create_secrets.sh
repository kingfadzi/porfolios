#!/bin/bash

# Set paths to secrets
SSH_KEY_PATH="./secrets/ssh_key"
SSH_KEY_PUB_PATH="./secrets/ssh_key_pub"
CERT_PATH="./secrets/self_signed_cert"

# Function to create a secret
create_secret() {
    local secret_name=$1
    local file_path=$2

    if [ ! -f "$file_path" ]; then
        echo "Error: File $file_path does not exist. Skipping $secret_name."
        return 1
    fi

    # Check if the secret already exists
    if docker secret ls | grep -q "$secret_name"; then
        echo "Secret $secret_name already exists. Skipping creation."
    else
        docker secret create "$secret_name" "$file_path"
        if [ $? -eq 0 ]; then
            echo "Secret $secret_name created successfully."
        else
            echo "Failed to create secret $secret_name."
        fi
    fi
}

# Ensure Swarm mode is enabled
if ! docker info | grep -q "Swarm: active"; then
    echo "Swarm mode is not active. Initializing Docker Swarm..."
    docker swarm init
fi

# Create secrets
create_secret "ssh_key" "$SSH_KEY_PATH"
create_secret "ssh_key_pub" "$SSH_KEY_PUB_PATH"
create_secret "self_signed_cert" "$CERT_PATH"

echo "All secrets processed."
