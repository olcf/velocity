*************
Build Process
*************

This page describes the steps that velocity goes through when building an image.

Setup
#####
After selecting images to build and ordering them. Velocity will start by assigning a random
id to each image to be built. It will also create a directory BSD (Build Sub Dir) named with that random id in
`VELOCITY_BUILD_DIR`.

.. _files:

Files
#####
Next Velocity will look for a folder in the image definition directory with the same name as `VELOCITY_SYSTEM`. All
of the files in this directory will be copied to the BSD.

Parse Template
##############
Velocity will then parse the correct template and generate a file called `script` in the BSD.

Create Build Script
###################
At this point Velocity will piece together the build command and append it to the end of the prolog (if a prolog was
specified). It will place the resulting script in the BSD with the name `build`.

Build
#####
Finally velocity will run the `build` script and log the output to a file called `log` in the BSD.

Build Directory Layout
######################
At the end of a build `VELOCITY_BUILD_DIR` should look somthing like this. With the addition of any other files that
got copied in the :ref:`files<files>` step.

.. code-block:: bash

    .
    ├── jknqsnkc
    │   ├── build
    │   ├── log
    │   └── script
    └── nfhmhmsh
        ├── build
        ├── log
        └── script

