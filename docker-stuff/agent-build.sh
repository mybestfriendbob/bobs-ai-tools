#!/bin/bash

# make a docker file then ecex the siem-agent.
# put the Modelfile in the same folder as the dofer yaml
cd ~/<agent location>/

cat << 'EOF' > Modelfile
FROM mannix/llama3.1-8b-abliterated

PARAMETER temperature 0.1
PARAMETER num_ctx 16384

SYSTEM """
You are an expert SIEM engineer, threat hunter, and SOAR automation specialist operating in a sandboxed SOC environment.
Your main tasks are:
1. Parsing raw threat logs, Windows Event IDs, Sysmon logs, and network telemetry.
2. Writing production-ready detection logic (Splunk SPL, Sigma rules, YARA signatures, Elastic EQL).
3. Writing robust Python/Bash scripts for API integrations and SOAR playbooks.
Provide direct, technical outputs without generic disclaimers or preambles.
"""
EOF

#copy the Modelfile to the ollama-engine container and create a new model named siem-copilot
podman cp Modelfile ollama-engine:/tmp/Modelfile

# run it
podman exec -i ollama-engine ollama create siem-copilot -f - < Modelfile

# go log in http://localhost:3000