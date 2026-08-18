# Docker stuff

I'm running bazzite for this build not sure if that will be an issue for anyone seeing these files going forward.

Why Bazzine? I don't like windows but I do like video games.  I got a steam deck and I really liked how smooth everything ran and now I'm here.


be sure to change the <vars> in the setup.sh

Note on line 15 & 26 in the podman yaml file :Z suffix: The :Z option on volume mounts tells Podman to automatically relabel persistent storage for SELinux, ensuring rootless container permissions work smoothly alongside label=disable.


Once the initial image is built and tested we can now use the automatice build scripts.  
 - Start-up.sh will stand the ollama instance up andf the web ui instance up and print the successful ro failure stdout to the screen.
 - agent-built.sh will check for agent updates and rebuild if necessary, modelfile may need edits depending on the changes.
 - teardown.sh will gracefully turn everything off and wipe the graphics memory good if this is a machine you also like to game on.  run teardown and start your game, 


Troubleshooting tips:
is the container running - podman ps -a | grep ollama-engine
get it running - podman start ollama-engine
if Modelfile error remember it may need to go to tem - odman cp Modelfile ollama-engine:/tmp/Modelfile
