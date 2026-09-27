#!/usr/bin/env python3
"""
Splunk Container Manager & Log Source Onboarding Tool
Python 3.14 Strict Syntax Compliant (Rootless Podman Edition)
"""

import os
import re
import subprocess
import sys
import uuid


def get_container(default_name="splunk"):
    """Get running or existing Splunk container name, defaulting to 'splunk'."""
    try:
        cmd = "podman ps -a --format '{{.Names}}' | grep splunk | head -n 1"
        container_name = subprocess.check_output(cmd, shell=True).decode().strip()
        return container_name if container_name else default_name
    except (subprocess.CalledProcessError, FileNotFoundError):
        return default_name


def get_etc_path():
    """Get host filesystem path to splunk_etc volume."""
    vol_cmd = "podman volume inspect splunk_etc --format '{{ .Mountpoint }}'"
    return subprocess.check_output(vol_cmd, shell=True).decode().strip()


def index_exists(index):
    """Check if an index stanza already exists in indexes.conf."""
    etc_path = get_etc_path()
    conf_file = f"{etc_path}/apps/soc_ingest/local/indexes.conf"
    
    # Touch file if it doesn't exist yet
    subprocess.run(f"podman unshare touch '{conf_file}'", shell=True, check=True, stderr=subprocess.DEVNULL)
    
    check_cmd = f"podman unshare grep -F '[{index}]' '{conf_file}'"
    res = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    return res.returncode == 0


def make_index(index):
    """Append new index definition to soc_ingest/local/indexes.conf using podman unshare."""
    etc_path = get_etc_path()
    conf_file = f"{etc_path}/apps/soc_ingest/local/indexes.conf"

    print(f"===> Creating index [{index}]...")
    cmd = f"""podman unshare bash -c "cat <<'EOF' >> '{conf_file}'

[{index}]
homePath = $SPLUNK_DB/{index}/db
coldPath = $SPLUNK_DB/{index}/colddb
thawedPath = $SPLUNK_DB/{index}/thaweddb
maxTotalDataSizeMB = 50000
frozenTimePeriodInSecs = 7776000
EOF" """
    subprocess.run(cmd, shell=True, check=True)


def make_listener(index, port, protocol, sourcetype):
    """Append new TCP/UDP listener to soc_ingest/local/inputs.conf using podman unshare."""
    st = sourcetype if sourcetype else "syslog"
    proto = protocol.lower()
    etc_path = get_etc_path()
    conf_file = f"{etc_path}/apps/soc_ingest/local/inputs.conf"
    
    stanza_header = f"[{proto}://{port}]"
    check_cmd = f"podman unshare grep -F '{stanza_header}' '{conf_file}'"
    res = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"===> Listener {stanza_header} already exists in inputs.conf. Skipping creation.")
        return

    print(f"===> Adding {proto.upper()} listener on port {port} for index '{index}'...")
    cmd = f"""podman unshare bash -c "cat <<'EOF' >> '{conf_file}'

[{proto}://{port}]
index = {index}
sourcetype = {st}
connection_host = ip
EOF" """
    subprocess.run(cmd, shell=True, check=True)


def make_forwarder_listener():
    """Ensure Splunk Universal Forwarder listener [splunktcp://9997] exists in inputs.conf."""
    etc_path = get_etc_path()
    conf_file = f"{etc_path}/apps/soc_ingest/local/inputs.conf"
    
    subprocess.run(f"podman unshare touch '{conf_file}'", shell=True, check=True, stderr=subprocess.DEVNULL)
    
    stanza_header = "[splunktcp://9997]"
    check_cmd = f"podman unshare grep -F '{stanza_header}' '{conf_file}'"
    res = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        print("===> Universal Forwarder listener [splunktcp://9997] already exists in inputs.conf.")
        return

    print("===> Enabling Universal Forwarder receiver on TCP 9997...")
    cmd = f"""podman unshare bash -c "cat <<'EOF' >> '{conf_file}'

[splunktcp://9997]
disabled = 0
EOF" """
    subprocess.run(cmd, shell=True, check=True)


def make_hec_token(index, sourcetype, user_token=None):
    """Generate or register HEC token inside soc_ingest/local/inputs.conf."""
    token = user_token if user_token else str(uuid.uuid4())
    st = sourcetype if sourcetype else "_json"
    etc_path = get_etc_path()
    conf_file = f"{etc_path}/apps/soc_ingest/local/inputs.conf"
    
    stanza_header = f"[http://hec_{index}]"
    check_cmd = f"podman unshare grep -F '{stanza_header}' '{conf_file}'"
    res = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"===> HEC stanza {stanza_header} already exists in inputs.conf. Skipping creation.")
        return token

    print(f"===> Configuring HEC token for index '{index}'...")
    cmd = f"""podman unshare bash -c "cat <<'EOF' >> '{conf_file}'

[http://hec_{index}]
disabled = 0
token = {token}
index = {index}
sourcetype = {st}
EOF" """
    subprocess.run(cmd, shell=True, check=True)
    return token


def modify_firewall(port, protocol):
    """Open port on Bazzite host firewalld."""
    proto = protocol.lower()
    print(f"===> Updating Bazzite firewalld for port {port}/{proto}...")
    try:
        subprocess.run(f"sudo firewall-cmd --add-port={port}/{proto} --permanent", shell=True, check=True)
        subprocess.run("sudo firewall-cmd --reload", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Firewall update failed: {e}")


def generate_lkgc_script(container, ports_str):
    """Output executable bash script start_splunk_LKGC.sh with active configuration."""
    script_path = "start_splunk_LKGC.sh"
    content = f"""#!/usr/bin/env bash
# Splunk Last Known Good Configuration (LKGC) Startup Script
# Auto-generated by manage_splunk.py

echo "===> Stopping existing Splunk container (if running)..."
podman stop -t 30 {container} 2>/dev/null
podman rm {container} 2>/dev/null

echo "===> Launching Splunk Enterprise container with LKGC parameters..."
podman run -d \\
  --name {container} \\
  --stop-timeout 30 \\
  {ports_str} \\
  -v splunk_data:/opt/splunk/var \\
  -v splunk_etc:/opt/splunk/etc \\
  -e "SPLUNK_START_ARGS=--accept-license" \\
  -e "SPLUNK_GENERAL_TERMS=--accept-sgt-current-at-splunk-com" \\
  -e "SPLUNK_PASSWORD=YourSecurePassword123!" \\
  -e "SPLUNK_LICENSE_URI=Free" \\
  docker.io/splunk/splunk:latest

echo "===> Splunk container '{container}' started successfully!"
"""
    with open(script_path, "w") as f:
        f.write(content)
    
    # Grant execute permissions (chmod +x)
    os.chmod(script_path, 0o755)
    print(f"===> Generated executable startup script: {os.path.abspath(script_path)}")


def config_image(container):
    """Rebuild and restart Podman container with all active port mappings and update LKGC script."""
    print("===> Scanning inputs.conf for active ports...")
    
    # Base web/HEC ports
    port_args = ["-p", "8000:8000", "-p", "8088:8088"]
    
    try:
        etc_path = get_etc_path()
        inputs_file = f"{etc_path}/apps/soc_ingest/local/inputs.conf"
        
        cat_cmd = f"podman unshare cat '{inputs_file}'"
        content = subprocess.check_output(cat_cmd, shell=True).decode()
        
        port_pattern = re.compile(r'\[(tcp|udp|splunktcp)://([0-9]+)\]', re.IGNORECASE)
        for line in content.splitlines():
            match = port_pattern.search(line)
            if match:
                p_proto = match.group(1).lower()
                p_num = match.group(2)
                
                # Map splunktcp to tcp protocol
                if p_proto == "splunktcp":
                    p_proto = "tcp"
                    
                arg = f"{p_num}:{p_num}/{p_proto}"
                if arg not in port_args:
                    port_args.extend(["-p", arg])
    except Exception as e:
        print(f"Warning: Could not dynamically parse inputs.conf: {e}")

    ports_str = " ".join(port_args)
    
    # Generate executable start_splunk_LKGC.sh
    generate_lkgc_script(container, ports_str)
    
    # Execute startup via LKGC script
    print(f"===> Re-launching Podman container '{container}'...")
    subprocess.run("./start_splunk_LKGC.sh", shell=True, check=True)


#######################    MAIN      ##########################

if __name__ == "__main__":
    container = get_container()
    print(f"Detected Splunk container: {container}\n")
    
    print("Select Input Type:")
    print("  1: UDP/TCP Syslog")
    print("  2: HTTP Event Collector (HEC)")
    print("  3: Universal Forwarder (TCP 9997)")
    r = input("Choice [1-3]: ").strip()

    if r == '1':
        index = input("Enter target index name: ").strip()
        sourcetype = input("Enter sourcetype (leave blank for default): ").strip()
        protocol = input("Enter protocol (UDP or TCP): ").strip().lower()
        port = input("Enter port number: ").strip()
        
        if not index_exists(index):
            make_index(index)
        make_listener(index, port, protocol, sourcetype)
        modify_firewall(port, protocol)
        config_image(container)
        
    elif r == '2':
        index = input("Enter target index name: ").strip()
        sourcetype = input("Enter sourcetype (leave blank for default): ").strip()
        user_token = input("Enter HEC Token (leave blank to auto-generate): ").strip()
        
        if not index_exists(index):
            make_index(index)
        assigned_token = make_hec_token(index, sourcetype, user_token)
        modify_firewall("8088", "tcp")
        config_image(container)
        
        print("\n" + "=" * 42)
        print("HEC Endpoint Ready!")
        print("URL: http://127.0.0.1:8088/services/collector/event")
        print(f"Token: {assigned_token}")
        print("=" * 42 + "\n")

    elif r == '3':
        index = input("Enter target index name for Universal Forwarder: ").strip()
        
        if not index_exists(index):
            make_index(index)
        else:
            print(f"===> Index [{index}] already exists in indexes.conf. Skipping creation.")
            
        make_forwarder_listener()
        modify_firewall("9997", "tcp")
        config_image(container)
        
        print("\n" + "=" * 55)
        print(f"Universal Forwarder Ready for Index [{index}] on TCP 9997!")
        print("=" * 55 + "\n")

    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)
