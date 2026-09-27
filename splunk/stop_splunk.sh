#!/usr/bin/env bash
# Splunk Container Teardown Script

# Detect running or existing Splunk container
CONTAINER_NAME=$(podman ps -a --format '{{.Names}}' | grep splunk | head -n 1)

if [ -z "$CONTAINER_NAME" ]; then
    echo "===> No Splunk container found."
    exit 0
fi

# Check if running
if podman ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "===> Gracefully stopping container '$CONTAINER_NAME' (allowing 30s for index flush)..."
    podman stop -t 30 "$CONTAINER_NAME"
    echo "===> Container '$CONTAINER_NAME' stopped."
else
    echo "===> Container '$CONTAINER_NAME' is already stopped."
fi

# Remove container instance (persistent volumes splunk_data and splunk_etc remain untouched)
echo "===> Removing container instance '$CONTAINER_NAME'..."
podman rm "$CONTAINER_NAME" 2>/dev/null
echo "===> Teardown complete. Persistent data and configurations are intact."
