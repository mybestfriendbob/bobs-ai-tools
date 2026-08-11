#!/usr/bin/env bash

# List your container names here
CONTAINERS=("ollama" "open-webui")

echo "Checking AI container status..."

for container in "${CONTAINERS[@]}"; do
    # Check if container exists
    if ! podman container exists "$container" 2>/dev/null; then
        echo "  [!] Container '$container' does not exist."
        continue
    fi

    # Check if container is running
    IS_RUNNING=$(podman inspect -f '{{.State.Running}}' "$container" 2>/dev/null)

    if [ "$IS_RUNNING" == "true" ]; then
        echo "  [✓] '$container' is already running."
    else
        echo "  [...] '$container' is stopped. Starting now..."
        if podman start "$container" >/dev/null 2>&1; then
            echo "  [✓] Successfully started '$container'."
        else
            echo "  [X] Failed to start '$container'."
        fi
    fi
done