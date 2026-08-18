#!/usr/bin/env bash

# Handles both current and legacy container names
CONTAINERS=("open-webui" "ollama-engine" "ollama")

echo "Tearing down AI container stack..."

for container in "${CONTAINERS[@]}"; do
    if podman container exists "$container" 2>/dev/null; then
        echo "  [...] Stopping and removing container '$container'..."
        # Force stops process and removes container object
        podman rm -f "$container" >/dev/null
        echo "  [✓] '$container' successfully removed."
    else
        echo "  [-] Container '$container' is not present."
    fi
done

echo ""
echo "Stack wiped and GPU VRAM completely freed."
echo "Note: Persistent volumes ('ollama_data' and 'open-webui_data') were NOT deleted."