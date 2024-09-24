
***********
Basic Usage
***********

.. note::

    The output from the commands below may not be the same on your system based on what images you have defined.

`avail`
-------

The `avail` command prints the defined images that can be built.

.. code-block:: bash

    $ velocity avail
    ==> gcc
        12.3.0
        13.2.0
        14.1.0
    ==> llvm
        17.0.0
        17.0.6
    ==> mpich
        3.4.3
    ==> rocm
        5.7.1
        6.0.1
        6.1.3
    ==> ubuntu
        20.04
        22.04
        24.04


Each image is listed and then indented underneath is a list of the available versions.

`spec`
------

The `spec` command shows the dependencies for a given image (or list of images) in a tree like structure.

.. code-block:: bash

    $ velocity spec rocm
      > rocm@6.1.3-fd4d363
         ^ubuntu@22.04-f385880

`build`
-------

The `build` command can be used to build an container image from one or more image definitions.

.. code-block:: bash

    $ velocity build ubuntu
    ==> Build Order:
        ubuntu@24.04-ce71495

    ==> ce71495: BUILD ubuntu@24.04 ...
    ==> ce71495: GENERATING SCRIPT ...
    ==> ce71495: BUILDING ...
    ==> ce71495: IMAGE /tmp/velocity/scratch/ubuntu-24.04-ce71495/ce71495.sif (ubuntu@24.04) BUILT [0:00:25]

    ==> BUILT: /tmp/velocity/images/ubuntu-24.04__x86_64-ubuntu.sif


Both the spec and the build command can also take a list of images.

.. code-block:: bash

    $ velocity build ubuntu mpich
    ==> Build Order:
        ubuntu@24.04-ce71495
        mpich@3.4.3-f5a1d3b

    ==> ce71495: BUILD ubuntu@24.04 ...
    ==> ce71495: GENERATING SCRIPT ...
    ==> ce71495: BUILDING ...
    ==> ce71495: IMAGE /tmp/velocity/scratch/ubuntu-24.04-ce71495/ce71495.sif (ubuntu@24.04) BUILT [0:00:00]

    ==> f5a1d3b: BUILD mpich@3.4.3 ...
    ==> f5a1d3b: GENERATING SCRIPT ...
    ==> f5a1d3b: BUILDING ...
    ==> f5a1d3b: IMAGE /tmp/xjv/velocity/mpich-3.4.3-f5a1d3b/f5a1d3b.sif (mpich@3.4.3) BUILT [0:00:00]

    ==> BUILT: /tmp/velocity/images/mpich-3.4.3_ubuntu-24.04__x86_64-ubuntu.sif
