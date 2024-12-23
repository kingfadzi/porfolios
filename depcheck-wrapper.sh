#!/bin/bash

# Script to run OWASP Dependency-Check in offline mode with a pre-configured properties file

# Configurable variables
JAVA_HOME="/usr/lib/jvm/jdk-21-oracle-x64"      # Path to Java installation
DC_HOME="/opt/dependency-check"                # Path to Dependency-Check installation
DC_PROPERTIES="$DC_HOME/dependency-check.properties" # Path to Dependency-Check properties file
SCAN_PATH="/tmp/sonar-metrics"                 # Path to the project to scan
OUTPUT_DIR="/tmp"                              # Directory to save the Dependency-Check report
LOG_FILE="$OUTPUT_DIR/dependency-check.log"    # Path to the log file

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

# Check if the properties file exists
if [[ ! -f "$DC_PROPERTIES" ]]; then
    echo "Error: Properties file not found at $DC_PROPERTIES"
    exit 1
fi

# Preload the NVD data into the database
echo "Preloading NVD data into the database..."
"$DC_HOME/bin/dependency-check.sh" --updateonly --propertyfile "$DC_PROPERTIES"

if [[ $? -ne 0 ]]; then
    echo "Error: Failed to preload NVD data."
    exit 1
fi

# Run Dependency-Check in offline mode with no updates
echo "Running Dependency-Check in offline mode..."
"$DC_HOME/bin/dependency-check.sh" --scan "$SCAN_PATH" \
    --propertyfile "$DC_PROPERTIES" \
    --noupdate \
    --format JSON \
    --log "$LOG_FILE" \
    --out "$OUTPUT_DIR"

# Check if the scan was successful
if [[ $? -eq 0 ]]; then
    echo "Dependency-Check scan completed successfully."
    echo "Reports saved to: $OUTPUT_DIR"
    echo "Log file: $LOG_FILE"
else
    echo "Error: Dependency-Check scan failed."
    echo "Check log file for details: $LOG_FILE"
    exit 1
fi
