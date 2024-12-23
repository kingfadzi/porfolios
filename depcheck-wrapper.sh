#!/bin/bash

# Script to run OWASP Dependency-Check in offline mode with manually downloaded NVD files

# Configurable variables
JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"  # Path to Java installation
DC_HOME="/opt/dependency-check"                # Path to Dependency-Check installation
DC_PROPERTIES="$DC_HOME/dependency-check.properties" # Path to Dependency-Check properties file
SCAN_PATH="/path/to/project"                   # Path to the project to scan
OUTPUT_DIR="/path/to/output"                   # Directory to save the Dependency-Check report
NVD_PATH="/path/to/nvd"                        # Directory containing manually downloaded NVD files
DB_PATH="/path/to/database"                    # Directory to store the Dependency-Check database
LOG_FILE="$OUTPUT_DIR/dependency-check.log"    # Path to the log file

# Ensure JAVA_HOME is set
export JAVA_HOME="$JAVA_HOME"
export PATH="$JAVA_HOME/bin:$PATH"

# Check if Dependency-Check is installed
if [[ ! -d "$DC_HOME" ]]; then
    echo "Error: Dependency-Check not found at $DC_HOME"
    exit 1
fi

# Ensure the output and database directories exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$DB_PATH"

# Create the properties file for offline mode
cat > "$DC_PROPERTIES" <<EOL
# Dependency-Check properties for offline mode
data.directory=$DB_PATH
cve.startyear=2002
cve.validForHours=99999
cveUrlModified=file:$NVD_PATH/nvdcve-1.1-Modified.json.gz
cveUrlBase=file:$NVD_PATH/nvdcve-1.1-
EOL

echo "Dependency-Check properties file created at $DC_PROPERTIES"

# Preload the NVD data into the database
echo "Preloading NVD data into the database..."
"$DC_HOME/bin/dependency-check.sh" --updateonly --propertyfile "$DC_PROPERTIES"

if [[ $? -ne 0 ]]; then
    echo "Error: Failed to preload NVD data."
    exit 1
fi

# Run Dependency-Check in offline mode
echo "Running Dependency-Check in offline mode..."
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
