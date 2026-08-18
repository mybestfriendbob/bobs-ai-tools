#!/usr/bin/env bash

OLLAMA_NAME="ollama-engine"
WEBUI_NAME="open-webui"
OLLAMA_API_URL="http://localhost:11434/api/version"

echo "Checking AI container stack..."

# 0. Ensure custom Podman network exists
if ! podman network exists ai-net 2>/dev/null; then
    podman network create ai-net >/dev/null 2>&1
fi

# 1. Manage Ollama Engine Container
if ! podman container exists "$OLLAMA_NAME" 2>/dev/null; then
    echo "  [!] Container '$OLLAMA_NAME' does not exist. Creating and starting now..."
    podman run -d \
      --name "$OLLAMA_NAME" \
      --network ai-net \
      --device nvidia.com/gpu=all \
      --security-opt=label=disable \
      -v ollama-container_ollama_data:/root/.ollama:Z \
      -p 11434:11434 \
      docker.io/ollama/ollama:latest >/dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "  [✓] Container '$OLLAMA_NAME' created and started with GPU support."
    else
        echo "  [X] Failed to create container '$OLLAMA_NAME'."
    fi
elif [ "$(podman inspect -f '{{.State.Running}}' "$OLLAMA_NAME" 2>/dev/null)" == "true" ]; then
    echo "  [✓] '$OLLAMA_NAME' is already running."
else
    echo "  [...] '$OLLAMA_NAME' is stopped. Starting now..."
    podman start "$OLLAMA_NAME" >/dev/null
    echo "  [✓] Successfully started '$OLLAMA_NAME'."
fi

# 2. Health check for Ollama API
echo "  [...] Waiting for Ollama API to respond on port 11434..."
MAX_RETRIES=15
RETRY=0
until curl -s "$OLLAMA_API_URL" >/dev/null 2>&1 || [ $RETRY -eq $MAX_RETRIES ]; do
    sleep 1
    ((RETRY++))
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo "  [!] Warning: Ollama API did not respond in time."
else
    echo "  [✓] Ollama API is active and healthy."
fi

# 3. Auto-Build Check for siem-copilot
if ! podman exec "$OLLAMA_NAME" ollama list 2>/dev/null | grep -q "siem-copilot"; then
    echo "  [!] 'siem-copilot' model not found. Building from Modelfile..."
    podman exec -i "$OLLAMA_NAME" ollama pull mannix/llama3.1-8b-abliterated
    podman exec -i "$OLLAMA_NAME" ollama create siem-copilot -f - < Modelfile
    echo "  [✓] 'siem-copilot' successfully created!"
else
    echo "  [✓] Model 'siem-copilot' is registered and ready."
fi

echo ""

# 4. Manage Open-WebUI Container
if ! podman container exists "$WEBUI_NAME" 2>/dev/null; then
    echo "  [!] Container '$WEBUI_NAME' does not exist. Creating and starting now..."
    podman run -d \
      --name "$WEBUI_NAME" \
      --network ai-net \
      -p 3000:8080 \
      -e OLLAMA_BASE_URL=http://ollama-engine:11434 \
      -v ollama-container_open-webui_data:/app/backend/data:Z \
      ghcr.io/open-webui/open-webui:main >/dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "  [✓] Container '$WEBUI_NAME' created and started."
    else
        echo "  [X] Failed to create container '$WEBUI_NAME'."
    fi
elif [ "$(podman inspect -f '{{.State.Running}}' "$WEBUI_NAME" 2>/dev/null)" == "true" ]; then
    echo "  [✓] '$WEBUI_NAME' is already running."
else
    echo "  [...] '$WEBUI_NAME' is stopped. Starting now..."
    podman start "$WEBUI_NAME" >/dev/null
    echo "  [✓] Successfully started '$WEBUI_NAME'."
fi