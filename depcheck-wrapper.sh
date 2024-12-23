#!/bin/bash

# Script to run OWASP Dependency-Check with hardcoded properties file and JAVA_HOME setup

# Configurable variables
JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"  # Path to Java installation
DC_HOME="/opt/dependency-check"                # Path to Dependency-Check installation
DC_PROPERTIES="$DC_HOME/dependency-check.properties" # Path to Dependency-Check properties file
SCAN_PATH="/path/to/project"                   # Path to the project to scan
OUTPUT_DIR="/path/to/output"                   # Directory to save the Dependency-Check report

# Enable verbose logging
VERBOSE_LOGGING=true

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

# Run Dependency-Check with verbose logging
if [[ "$VERBOSE_LOGGING" == true ]]; then
    echo "Running Dependency-Check with verbose logging..."
    "$DC_HOME/bin/dependency-check.sh" --scan "$SCAN_PATH" \
        --propertyfile "$DC_PROPERTIES" \
        --format JSON \
        --log "$OUTPUT_DIR/dependency-check.log" \
        --out "$OUTPUT_DIR" \
        --verbose
else
    echo "Running Dependency-Check..."
    "$DC_HOME/bin/dependency-check.sh" --scan "$SCAN_PATH" \
        --propertyfile "$DC_PROPERTIES" \
        --format JSON \
        --log "$OUTPUT_DIR/dependency-check.log" \
        --out "$OUTPUT_DIR"
fi

# Check if the scan was successful
if [[ $? -eq 0 ]]; then
    echo "Dependency-Check scan completed successfully."
    echo "Reports saved to: $OUTPUT_DIR"
    echo "Log file: $OUTPUT_DIR/dependency-check.log"
else
    echo "Error: Dependency-Check scan failed."
    echo "Check log file for details: $OUTPUT_DIR/dependency-check.log"
    exit 1
fi
