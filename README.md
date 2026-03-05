# Acknowledgements

We acknowledge the deep learning training school of the Agroecophen PEPR program organized by the ImHorPhen group at IRHS, INRAe Angers, France in the framework of the PHENOME EMPHASIS scientific Infrastructure. 

# Goal: Running DL model inference from ImageJ1

ImageJ1 exec() macro command can run native commands.

Strategy: a shell script activates a conda environment in which we know our model can be used and launches a script that performs the inference. Read back the output mask.

# Prerequisites

You trained a DL model and have a \*.pt weights file.  
Find out key modules versions to recreate a suitable env.

# Install conda env suitable for running your model.



Test run inference like this:  
 

# Shell script that takes proper arguments, and that we will call from ImageJ.

This script parses arguments, discovers conda, activates environment and launches inference out put is saved at given location


# ImageJ macro that launches the script

Save it as Segment\_Unet.ijm in your ImageJ/plugins/ folder.



