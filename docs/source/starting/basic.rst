
********
Overview
********

How it Works
############
Velocity works by building a set of containers in a chain so that the final container has all of the needed components.
Velocity maintains a very hands off approach. It is only as good as the templates/configuration that you write.
In general it will assume that a particular build will work unless you tell it otherwise. It is important to note
that while Velocity has many features that are similar to those provided by a package manager, it is NOT a
package manager. Rather it should be viewed as a templating and build orchestration tool.

Installation
############

The easiest way to install velocity is to install prebuilt python packages using pip.

.. code-block:: bash

    pip install olcf-velocity

You can also clone the velocity repository and build/install velocity from source.

.. code-block:: bash

    git clone https://github.com/olcf/velocity.git
    cd velocity
    python3 -m build
    # install the built python wheel package
    pip install dist/olcf-velocity-<version>*.whl

Now you can use Velocity as a python module! We recommend setting a bash alias for convenience.

.. code-block:: bash

    user@hostname:~$ alias velocity="python3 -m velocity"
    user@hostname:~$ velocity
    usage: velocity [-h] [-v] [-D {TRACE,DEBUG,INFO,SUCCESS,WARNING,ERROR,CRITICAL}] [-b BACKEND] [-s SYSTEM] [-d DISTRO] {build,avail,spec} ...

    build tool for OLCF containers

    positional arguments:
      {build,avail,spec}
        build               build specified container image
        avail               lookup available images
        spec                lookup image dependencies

    options:
      -h, --help            show this help message and exit
      -v, --version         program version
      -D {TRACE,DEBUG,INFO,SUCCESS,WARNING,ERROR,CRITICAL}, --debug {TRACE,DEBUG,INFO,SUCCESS,WARNING,ERROR,CRITICAL}
                            set debug output level
      -b BACKEND, --backend BACKEND
      -s SYSTEM, --system SYSTEM
      -d DISTRO, --distro DISTRO

    See https://github.com/olcf/velocity

.. _configuration:

Configuration
#############
Velocity has a number of configuration options. The basic ones are setting the system name, container backend,
container distro, the path(s) to your image definitions and the build scratch directory.
To see more configuration options go to the :doc:`configuration </reference/config>` page. The easiest way to configure velocity is to
edit ``~/.velocity/config.yaml``.

.. code-block::

    velocity:
      system: frontier
      backend: apptainer
      distro: ubuntu
      image_path: # a list of : seperated paths
      build_dir: # path to a scratch space

.. note::

    Image definitions can be created by the user as needed but a base set for usage at OLCF are provided at
    https://github.com/olcf/velocity-images

Basic Usage
###########

`avail`
-------

The `avail` command prints the defined images that can be built.

.. code-block:: bash

    user@hostname:~$ velocity avail
    ==> gcc
        12.3.0
        13.2.0
        14.1.0
    ==> mpich
        3.4.3
    ==> rocm
        5.7.1
    ==> ubuntu
        20.04
        22.04
        24.04

Each image is listed and then indented underneath is a list of the available versions.

`spec`
------

The `spec` command shows the dependencies for a given image (or list of images) in a tree like structure.

.. code-block:: bash

    user@hostname:~$ velocity spec pytorch
      > pytorch@latest
         ^cuda@11.7.1
            ^centos@stream8
         ^cudnn@8.5.0.96
            ^cuda@11.7.1
               ^centos@stream8
         ^spectrum-mpi@10.4.0.6
            ^centos@stream8
         ^gcc@11.2.0
            ^centos@stream8
         ^miniforge3@23.11.0
            ^centos@stream8


`build`
-------

The `build` command can be used to build an container image from one or more image definitions.

.. code-block:: bash

    user@hostname:~$ velocity build centos
    ==> Build Order:
            centos@=stream8

    ==> iarfnxer: BUILD centos@=stream8 ...
    ==> iarfnxer: GENERATING SCRIPT ...
    ==> iarfnxer: BUILDING ...
    ==> iarfnxer: IMAGE localhost/centos__stream8__x86_64__centos:latest (centos@=stream8) BUILT (0:01:22)

Both the spec and the build command can also take a list of images.

.. code-block:: bash

    user@hostname:~$ velocity build gcc python
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
