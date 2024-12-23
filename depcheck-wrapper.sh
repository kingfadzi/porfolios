#!/bin/bash

# Script to run OWASP Dependency-Check with proxy and JAVA_HOME configurations

# Configurable variables
JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"  # Path to Java installation
DC_HOME="/opt/dependency-check"                # Path to Dependency-Check installation
DC_PROPERTIES="$DC_HOME/dependency-check.properties" # Path to Dependency-Check properties file
PROXY_SERVER="proxy.example.com"               # Proxy hostname
PROXY_PORT="8080"                              # Proxy port
PROXY_USERNAME="user"                          # Proxy username (optional)
PROXY_PASSWORD="password"                      # Proxy password (optional)
SCAN_PATH="/path/to/project"                   # Path to the project to scan
OUTPUT_DIR="/path/to/output"                   # Directory to save the Dependency-Check report

# Ensure JAVA_HOME is set
export JAVA_HOME="$JAVA_HOME"
export PATH="$JAVA_HOME/bin:$PATH"

# Check if Dependency-Check is installed
if [[ ! -d "$DC_HOME" ]]; then
    echo "Error: Dependency-Check not found at $DC_HOME"
    exit 1
fi

# Ensure the output directory exists
mkdir -p "$OUTPUT_DIR"

# Create Dependency-Check properties file
cat > "$DC_PROPERTIES" <<EOL
# Dependency-Check properties
proxy.server=$PROXY_SERVER
proxy.port=$PROXY_PORT
proxy.username=$PROXY_USERNAME
proxy.password=$PROXY_PASSWORD

# Bypass proxy for local connections
proxy.nonProxyHosts=localhost|127.0.0.1

# Data directory (H2 database)
data.directory=$DC_HOME/data

# Disable online updates for airgapped environments
cve.startyear=2002
cve.validForHours=99999
EOL

echo "Dependency-Check properties file created at $DC_PROPERTIES"

# Run Dependency-Check
echo "Starting Dependency-Check scan on: $SCAN_PATH"
"$DC_HOME/bin/dependency-check.sh" --scan "$SCAN_PATH" \
    --propertyfile "$DC_PROPERTIES" \
    --format JSON \
    --out "$OUTPUT_DIR"

# Check if the scan was successful
if [[ $? -eq 0 ]]; then
    echo "Dependency-Check scan completed successfully."
    echo "Reports saved to: $OUTPUT_DIR"
else
    echo "Error: Dependency-Check scan failed."
    exit 1
fi
