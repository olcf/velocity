
********
Overview
********

Concept
#######
Velocity is a tool to help with the maintenance of a variety of container builds on multiple systems, backends
(e.g podman or apptainer) and distros.

How it Works
############
Velocity works by building a set of containers in a chain so that the final container has all of the needed components.


Layout
######
The contents of the Velocity repo are fairly simple.

.. code-block::

    .
    ├── docs
    ├── lib
    ├── README.md
    ├── setup-env.sh
    └── velocity

For informational purposes there is a folder `docs` which holds this documentation and a README file.
The `setup-env.sh` script can be used to 'install' velocity. The lib folder holds a python package which the
velocity script needs to run.




Installation
############

First you will need to set up a python virtual environment for Velocity and install the following packages:

.. code-block::

    pyyaml networkx colorama editor loguru

.. important::

    If you wish to build the docs you will also need to install `sphinx` and `sphinx-rtd-theme`.

Next clone the Velocity git repository to the desired location.

.. code-block:: bash

    git clone https://gitlab.ccs.ornl.gov/saue-software/velocity.git

You can then setup Velocity by sourcing the `setup-env.sh` script.

.. code-block:: bash

    . ./velocity/setup-env.sh

The `setup-env.sh` script will help you choose the value of several environment :ref:`variables<configuration>`
that velocity uses.

You should now be able to run the `velocity` command.

.. code-block:: bash

    user@hostname:~$ velocity
    ==> System: x86_64
    ==> Backend: podman
    ==> Distro: fedora

    usage: velocity [-h] [-v] [-b BACKEND] [-s SYSTEM] [-d DISTRO]
                    {build,avail,spec,edit} ...

    Build tool for OLCF containers

    positional arguments:
      {build,avail,spec,edit}
        build               build specified container image
        avail               lookup available images
        spec                lookup image dependencies
        edit                edit image files

    options:
      -h, --help            show this help message and exit
      -v, --version         program version
      -b BACKEND, --backend BACKEND
      -s SYSTEM, --system SYSTEM
      -d DISTRO, --distro DISTRO

    See (https://gitlab.ccs.ornl.gov/saue-software/velocity)


.. _configuration:

Configuration
#############
There are five system variables that need to be set for Velocity to work (these are set in the `setup-env.sh` script).

`VELOCITY_IMAGE_DIR`
--------------------
This variable points to the directory containing the the image definitions.

.. note::

    Image definitions can be created by the user as needed but a base set for usage at OLCF are provided at
    `https://gitlab.ccs.ornl.gov/saue-software/velocity-images.git`

`VELOCITY_SYSTEM`
-----------------
This variable specifies what computer system you are building for (e.g. frontier).

`VELOCITY_BACKEND`
------------------
This variable specifies the container backend that should be used (e.g podman).

`VELOCITY_DISTRO`
-----------------
This variable specifies the distro of the container images that will be built.

`VELOCITY_BUILD_DIR`
--------------------
This variable specifies a scratch space for Velocity to preform builds in.



Basic Usage
###########

`avail`
-------

The `avail` command prints the defined images that can be built.

.. code-block:: bash

    user@hostname:~$ velocity avail
    ==> System: x86_64
    ==> Backend: podman
    ==> Distro: centos

    ==> centos
            stream8
    ==> gcc
            11.2.0
    ==> hmmer
            3.4
    ==> kalign
            3.4.0
    ==> miniforge3
            23.11.0
    ==> python
            3.11.8
    ==> pytorch
            latest

Each image is listed and then indented underneath is a list of the available versions
(in velocity they are called tags).

`spec`
------

The `spec` command shows the dependencies for a given image (or list of images) in a tree like structure.

.. code-block:: bash

    user@hostname:~$ velocity spec pytorch
    ==> System: summit
    ==> Backend: podman
    ==> Distro: centos

      > pytorch@=latest
         ^cuda@=11.7.1
            ^centos@=stream8
         ^cudnn@=8.5.0.96
            ^cuda@=11.7.1
               ^centos@=stream8
         ^spectrum-mpi@=10.4.0.6
            ^centos@=stream8
         ^gcc@=11.2.0
            ^centos@=stream8
         ^miniforge3@=23.11.0
            ^centos@=stream8



`build`
-------

The `build` can be used to build an container image from one or more image definitions.

.. code-block:: bash

    user@hostname:~$ velocity build centos
    ==> System: x86_64
    ==> Backend: podman
    ==> Distro: centos

    ==> Build Order:
            centos@=stream8

    ==> iarfnxer: BUILD centos@=stream8 ...
    ==> iarfnxer: GENERATING SCRIPT ...
    ==> iarfnxer: BUILDING ...
    ==> iarfnxer: IMAGE localhost/centos__stream8__x86_64__centos:latest (centos@=stream8) BUILT (0:01:22)

Both the spec and the build command can also take a list of images.

.. code-block:: bash

    user@hostname:~$ velocity build gcc python
    ==> System: x86_64
    ==> Backend: podman
    ==> Distro: centos

    ==> Build Order:
            centos@=stream8
            gcc@=11.2.0
            python@=3.11.8

    ==> pbxpudvh: BUILD centos@=stream8 ...
    ==> pbxpudvh: GENERATING SCRIPT ...
    ==> pbxpudvh: BUILDING ...
    ==> pbxpudvh: IMAGE localhost/pbxpudvh:latest (centos@=stream8) BUILT [0:01:00]

    ==> lxogjapp: BUILD gcc@=11.2.0 ...
    ==> lxogjapp: GENERATING SCRIPT ...
    ==> lxogjapp: BUILDING ...
    ==> lxogjapp: IMAGE localhost/lxogjapp:latest (gcc@=11.2.0) BUILT [0:40:34]

    ==> sunflyhd: BUILD python@=3.11.8 ...
    ==> sunflyhd: GENERATING SCRIPT ...
    ==> sunflyhd: BUILDING ...
    ==> sunflyhd: IMAGE localhost/python__3.11.8__x86_64__centos:latest (python@=3.11.8) BUILT [0:23:19]

`edit`
------
The edit command can be used to edit the VTMP or specification file for an image. By default
it edits the VTMP file. Add `-s` to edit the `specifications.yaml` file.

.. code-block:: bash

    user@hostname:~$ velocity edit --help
    usage: velocity edit [-h] [-s] target

    positional arguments:
      target               image to edit

    options:
      -h, --help           show this help message and exit
      -s, --specification  edit the specifications file
