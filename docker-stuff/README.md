# Docker stuff

I'm running bazzite for this build not sure if that will be an issue for anyone seeing these files going forward.

Why Bazzine? I don't like windows but I do like video games.  I got a steam deck and I really liked how smooth everything ran and now I'm here.


be sure to change the <vars> in the setup.sh

Note on line 15 & 26 in the podman yaml file :Z suffix: The :Z option on volume mounts tells Podman to automatically relabel persistent storage for SELinux, ensuring rootless container permissions work smoothly alongside label=disable.