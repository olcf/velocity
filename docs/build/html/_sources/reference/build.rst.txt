*************
Build Process
*************

This page describes the steps that velocity goes through when building an image.

Setup
#####
After selecting images to build and ordering them Velocity will also create a directory BSD (Build Sub Dir)
named ``<name>-<version>-<hash>`` in build directory.

.. _files:

Files
#####
Next Velocity will copy any files that you specified.

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
At the end of a build the build dir should look somthing like this. With the addition of any other files that
got copied in the :ref:`files<files>` step.

.. code-block:: bash

    .
    ├── fedora-41-8a9a360
    │ ├── 8a9a360.sif
    │ ├── build
    │ ├── log
    │ └── script
    └── hello-world-1.0-de9c02b
        ├── build
        ├── de9c02b.sif
        ├── hello_world.py
        ├── log
        └── script
