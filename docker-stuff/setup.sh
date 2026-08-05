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

