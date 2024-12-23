#!/bin/bash

# Script to run OWASP Dependency-Check with detailed logging and JAVA_HOME setup

# Configurable variables
JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"  # Path to Java installation
DC_HOME="/opt/dependency-check"                # Path to Dependency-Check installation
DC_PROPERTIES="$DC_HOME/dependency-check.properties" # Path to Dependency-Check properties file
SCAN_PATH="/path/to/project"                   # Path to the project to scan
OUTPUT_DIR="/path/to/output"                   # Directory to save the Dependency-Check report
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

# Check if properties file exists
if [[ ! -f "$DC_PROPERTIES" ]]; then
    echo "Error: Properties file not found at $DC_PROPERTIES"
    exit 1
fi

# Add debug-level logging to the properties file
if ! grep -q "logging.level.org.owasp.dependencycheck=DEBUG" "$DC_PROPERTIES"; then
    echo "Enabling debug logging in the properties file..."
    echo "logging.level.org.owasp.dependencycheck=DEBUG" >> "$DC_PROPERTIES"
fi

# Run Dependency-Check with logging
echo "Running Dependency-Check..."
"$DC_HOME/bin/dependency-check.sh" --scan "$SCAN_PATH" \
    --propertyfile "$DC_PROPERTIES" \
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
