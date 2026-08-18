# Check if siem-copilot model exists in Ollama, build if missing
if ! podman exec "$OLLAMA_NAME" ollama list 2>/dev/null | grep -q "siem-copilot"; then
    echo "  [!] 'siem-copilot' model not found. Initializing build..."
    podman exec -i "$OLLAMA_NAME" ollama pull mannix/llama3.1-8b-abliterated
    podman exec -i "$OLLAMA_NAME" ollama create siem-copilot -f - < Modelfile
    echo "  [✓] 'siem-copilot' successfully created!"
else
    echo "  [✓] Model 'siem-copilot' is ready."
fi