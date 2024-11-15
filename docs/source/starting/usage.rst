
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
    ==> opensuse
        15.4
        15.5
        15.6
    ==> rocm
        5.7.1
        6.0.1
        6.1.3

    $ velocity avail gcc
    ==> gcc
        12.3.0
        13.2.0
        14.1.0

Each image is listed and then indented underneath is a list of the available versions.

`spec`
------

The `spec` command shows the dependencies for a given image (or list of images) in a tree like structure.

.. code-block:: text

    $ velocity spec rocm
      > rocm@6.1.3-2a35af4
         ^opensuse@15.5-b386640

`build`
-------

The `build` command can be used to build an container image from one or more image definitions.

.. code-block:: text

    $ velocity build opensuse
    ==> Build Order:
        opensuse@15.6-01205e8

    ==> 01205e8: BUILD opensuse@15.6 ...
    ==> 01205e8: GENERATING SCRIPT ...
    ==> 01205e8: BUILDING ...
    ==> 01205e8: IMAGE /tmp/xxx/velocity/opensuse-15.6-01205e8/01205e8.sif (opensuse@15.6) BUILT [0:02:12]

    ==> BUILT: /tmp/opensuse-15.6__x86_64-opensuse.sif

Both the spec and the build command can also take a list of images.

.. code-block:: text

    $ velocity build opensuse mpich
    ==> Build Order:
        opensuse@15.6-01205e8
        mpich@3.4.3-5a22b26

    ==> 01205e8: BUILD opensuse@15.6 ...
    ==> 01205e8: GENERATING SCRIPT ...
    ==> 01205e8: BUILDING ...
    ==> 01205e8: IMAGE /tmp/xxx/velocity/opensuse-15.6-01205e8/01205e8.sif (opensuse@15.6) BUILT [0:00:00]

    ==> 5a22b26: BUILD mpich@3.4.3 ...
    ==> 5a22b26: GENERATING SCRIPT ...
    ==> 5a22b26: BUILDING ...
    ==> 5a22b26: IMAGE /tmp/xxx/velocity/mpich-3.4.3-5a22b26/5a22b26.sif (mpich@3.4.3) BUILT [0:09:32]

    ==> BUILT: /tmp/mpich-3.4.3_opensuse-15.6__x86_64-opensuse.sif
