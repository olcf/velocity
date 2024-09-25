
********
Overview
********

What is Velocity
################
Velocity is a tool to help with the maintenance of container build scripts on multiple systems,
backends (e.g podman or apptainer) and distros.

.. important::

    While Velocity provides a compatibility layer for `Apptainer <https://apptainer.org/documentation/>`_ and
    `Podman <https://docs.podman.io/en/latest>`_, it is still important to have a basic
    knowledge of how they work and the container building process in general.

How it Works
############
Velocity works by building a set of containers in a chain so that the final container has all of the needed components.

.. important::

    Velocity maintains a very hands off approach. It is only as good as the templates/configuration that you write.
    In general it will assume that a particular build will work unless you tell it otherwise.

.. note::

    While Velocity has many features that are similar to those provided by a package manager, it is NOT a
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
    pip install build
    python3 -m build
    # install the built python wheel package the version will depend on what version of velocity you have checked out
    # check the dist directory for the exact version
    pip install dist/olcf_velocity-<version>-py3-none-any.whl

Now you can use Velocity as a python module! We recommend setting a bash alias for convenience.

.. code-block:: bash

    $ alias velocity="python3 -m velocity"
    $ velocity
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
