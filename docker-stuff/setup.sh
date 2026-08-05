#!/bin/bash

# using podman instead of docker
systemctl --user enable --now podman.socket

# alias podman to docker so scripts don't break
echo "alias docker=podman" >> ~/.bashrc && source ~/.bashrc

# restart service, anytime a script calls for a docker restart we do this
podman restart --all

# this should show the podman details now
echo docker version

# testing GPU visibility to podman
echo podman run --rm --device nvidia.com/gpu=all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi

# Now get docker going

# Test the GPU access if you have AMD google it.
podman run --rm --security-opt=label=disable --device nvidia.com/gpu=all docker.io/nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi

# copy the yaml file ---->> change the <vars>
scp ~/<path to repo>/podman-compose.yml user@<remote server>:/<path to remote location>/podman-compose.yml

mkdir -p <path to container> && cd <path to container>

mkdir -p ~/.docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose

podman compose up -d

# this is the fun part now go run the abliterated version
podman exec -it ollama-engine ollama run mannix/llama3.1-8b-abliterated

# when complete you should see a success message and have a >>> prompt to interract.

# use the /bye command to clean up and close the terminal session.
