*************************
Creating Your First Image
*************************

Base Image
##########
Let's start with a simple base image. This image will pull an fedora docker image and update the packages. To setup
your environment do something like this.


.. code-block:: bash
    :caption: Setup

    TUTORIAL_DIR=/tmp/velocity
    mkdir -p $TUTORIAL_DIR/images
    export VELOCITY_IMAGE_PATH=$TUTORIAL_DIR/images
    export VELOCITY_BUILD_DIR=$TUTORIAL_DIR/build
    export VELOCITY_DISTRO=fedora
    # all subsequent commands in this tutorial were run from the TUTORIAL_DIR, but they don't have to be

.. note::

    You will also need Apptainer installed on your system.

Next create a directory in the ``images`` directory called ``fedora``. In this directory create a file called
``specs.yaml`` and a directory called ``templates`` with
a file named ``default.vtmp``. Your image directory and files should now look like this.

.. code-block:: bash
    :caption: /tmp/velocity/images

    fedora
    ├── specs.yaml
    └── templates
        └── default.vtmp


.. code-block:: yaml
    :caption: specs.yaml

    versions:
      - spec: 38
        when: distro=fedora



.. code-block:: text
    :caption: default.vtmp

    @from
        docker.io/fedora:{{ __version__ }}

    @run
        dnf -y upgrade
        dnf clean all

Now if you run `velocity avail` you should get the following.

.. code-block:: bash

    $ velocity avail
    ==> fedora
        38

Now build the image.

.. code-block:: bash

    $ velocity build fedora
    ==> Build Order:
        fedora@38-aa51aa7

    ==> aa51aa7: BUILD fedora@38 ...
    ==> aa51aa7: GENERATING SCRIPT ...
    ==> aa51aa7: BUILDING ...
    ==> aa51aa7: IMAGE /tmp/velocity/build/fedora-38-aa51aa7/aa51aa7.sif (fedora@38) BUILT [0:01:07]

    ==> BUILT: /tmp/velocity/fedora-38__x86_64-fedora.sif

If you wish to see more output you can add the `-v` flag:

.. code-block:: bash

    $ velocity build fedora -v
    ==> Build Order:
        fedora@38-aa51aa7

    ==> aa51aa7: BUILD fedora@38 ...
    ==> aa51aa7: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/fedora-38-aa51aa7/script
        Bootstrap: docker
        From: docker.io/fedora:38

        %post
        dnf -y upgrade
        dnf clean all
    ==> aa51aa7: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/velocity/build/fedora-38-aa51aa7/aa51aa7.sif /tmp/velocity/build/fedora-38-aa51aa7/script;
        Fedora 38 - x86_64                              2.3 MB/s |  83 MB     00:35
        Fedora 38 openh264 (From Cisco) - x86_64        2.8 kB/s | 2.6 kB     00:00
        Fedora Modular 38 - x86_64                      1.8 MB/s | 2.8 MB     00:01
        Fedora 38 - x86_64 - Updates                    2.8 MB/s |  42 MB     00:14
        Fedora Modular 38 - x86_64 - Updates            257 kB/s | 2.2 MB     00:08
        Dependencies resolved.
        ================================================================================
         Package                            Arch    Version              Repo      Size
        ================================================================================
        Upgrading:
         fedora-release-common              noarch  38-37                updates   20 k
         fedora-release-container           noarch  38-37                updates   10 k
         fedora-release-identity-container  noarch  38-37                updates   12 k
         glibc                              x86_64  2.37-19.fc38         updates  2.1 M
         glibc-common                       x86_64  2.37-19.fc38         updates  320 k
         glibc-minimal-langpack             x86_64  2.37-19.fc38         updates   42 k
         gnutls                             x86_64  3.8.5-1.fc38         updates  1.1 M
         libnghttp2                         x86_64  1.52.0-3.fc38        updates   75 k
         python-pip-wheel                   noarch  22.3.1-4.fc38        updates  1.4 M
         python3                            x86_64  3.11.9-2.fc38        updates   28 k
         python3-libs                       x86_64  3.11.9-2.fc38        updates  9.6 M
         tpm2-tss                           x86_64  4.0.2-1.fc38         updates  391 k
         vim-data                           noarch  2:9.1.393-1.fc38     updates   23 k
         vim-minimal                        x86_64  2:9.1.393-1.fc38     updates  810 k
        Installing weak dependencies:
         libxcrypt-compat                   x86_64  4.4.36-1.fc38        updates   90 k

        Transaction Summary
        ================================================================================
        Install   1 Package
        Upgrade  14 Packages

        Total download size: 16 M
        Downloading Packages:
        (1/15): fedora-release-container-38-37.noarch.r 160 kB/s |  10 kB     00:00
        (2/15): fedora-release-common-38-37.noarch.rpm  228 kB/s |  20 kB     00:00
        (3/15): fedora-release-identity-container-38-37 385 kB/s |  12 kB     00:00
        (4/15): libxcrypt-compat-4.4.36-1.fc38.x86_64.r 648 kB/s |  90 kB     00:00
        (5/15): glibc-minimal-langpack-2.37-19.fc38.x86 1.1 MB/s |  42 kB     00:00
        (6/15): glibc-common-2.37-19.fc38.x86_64.rpm    2.4 MB/s | 320 kB     00:00
        (7/15): libnghttp2-1.52.0-3.fc38.x86_64.rpm     1.7 MB/s |  75 kB     00:00
        (8/15): glibc-2.37-19.fc38.x86_64.rpm           8.1 MB/s | 2.1 MB     00:00
        (9/15): python3-3.11.9-2.fc38.x86_64.rpm        686 kB/s |  28 kB     00:00
        (10/15): python-pip-wheel-22.3.1-4.fc38.noarch. 8.8 MB/s | 1.4 MB     00:00
        (11/15): tpm2-tss-4.0.2-1.fc38.x86_64.rpm       6.1 MB/s | 391 kB     00:00
        (12/15): gnutls-3.8.5-1.fc38.x86_64.rpm         3.1 MB/s | 1.1 MB     00:00
        (13/15): vim-data-9.1.393-1.fc38.noarch.rpm     503 kB/s |  23 kB     00:00
        (14/15): vim-minimal-9.1.393-1.fc38.x86_64.rpm  4.3 MB/s | 810 kB     00:00
        (15/15): python3-libs-3.11.9-2.fc38.x86_64.rpm   11 MB/s | 9.6 MB     00:00
        --------------------------------------------------------------------------------
        Total                                            11 MB/s |  16 MB     00:01
        Running transaction check
        Transaction check succeeded.
        Running transaction test
        Transaction test succeeded.
        Running transaction
          Preparing        :                                                        1/1
          Upgrading        : glibc-common-2.37-19.fc38.x86_64                      1/29
          Upgrading        : glibc-minimal-langpack-2.37-19.fc38.x86_64            2/29
          Running scriptlet: glibc-2.37-19.fc38.x86_64                             3/29
          Upgrading        : glibc-2.37-19.fc38.x86_64                             3/29
          Running scriptlet: glibc-2.37-19.fc38.x86_64                             3/29
          Upgrading        : fedora-release-identity-container-38-37.noarch        4/29
          Upgrading        : fedora-release-container-38-37.noarch                 5/29
          Upgrading        : fedora-release-common-38-37.noarch                    6/29
          Installing       : libxcrypt-compat-4.4.36-1.fc38.x86_64                 7/29
          Upgrading        : python-pip-wheel-22.3.1-4.fc38.noarch                 8/29
          Upgrading        : python3-3.11.9-2.fc38.x86_64                          9/29
          Upgrading        : python3-libs-3.11.9-2.fc38.x86_64                    10/29
          Upgrading        : vim-data-2:9.1.393-1.fc38.noarch                     11/29
          Upgrading        : vim-minimal-2:9.1.393-1.fc38.x86_64                  12/29
          Upgrading        : gnutls-3.8.5-1.fc38.x86_64                           13/29
          Upgrading        : libnghttp2-1.52.0-3.fc38.x86_64                      14/29
          Running scriptlet: tpm2-tss-4.0.2-1.fc38.x86_64                         15/29
          Upgrading        : tpm2-tss-4.0.2-1.fc38.x86_64                         15/29
          Cleanup          : fedora-release-common-38-36.noarch                   16/29
          Cleanup          : gnutls-3.8.4-1.fc38.x86_64                           17/29
          Cleanup          : tpm2-tss-4.0.1-3.fc38.x86_64                         18/29
          Cleanup          : vim-minimal-2:9.1.309-1.fc38.x86_64                  19/29
          Cleanup          : libnghttp2-1.52.0-2.fc38.x86_64                      20/29
          Cleanup          : python3-3.11.8-2.fc38.x86_64                         21/29
          Cleanup          : fedora-release-container-38-36.noarch                22/29
          Cleanup          : fedora-release-identity-container-38-36.noarch       23/29
          Cleanup          : vim-data-2:9.1.309-1.fc38.noarch                     24/29
          Cleanup          : python3-libs-3.11.8-2.fc38.x86_64                    25/29
          Cleanup          : python-pip-wheel-22.3.1-3.fc38.noarch                26/29
          Cleanup          : glibc-2.37-18.fc38.x86_64                            27/29
          Cleanup          : glibc-minimal-langpack-2.37-18.fc38.x86_64           28/29
          Cleanup          : glibc-common-2.37-18.fc38.x86_64                     29/29
          Running scriptlet: glibc-common-2.37-18.fc38.x86_64                     29/29
          Verifying        : libxcrypt-compat-4.4.36-1.fc38.x86_64                 1/29
          Verifying        : fedora-release-common-38-37.noarch                    2/29
          Verifying        : fedora-release-common-38-36.noarch                    3/29
          Verifying        : fedora-release-container-38-37.noarch                 4/29
          Verifying        : fedora-release-container-38-36.noarch                 5/29
          Verifying        : fedora-release-identity-container-38-37.noarch        6/29
          Verifying        : fedora-release-identity-container-38-36.noarch        7/29
          Verifying        : glibc-2.37-19.fc38.x86_64                             8/29
          Verifying        : glibc-2.37-18.fc38.x86_64                             9/29
          Verifying        : glibc-common-2.37-19.fc38.x86_64                     10/29
          Verifying        : glibc-common-2.37-18.fc38.x86_64                     11/29
          Verifying        : glibc-minimal-langpack-2.37-19.fc38.x86_64           12/29
          Verifying        : glibc-minimal-langpack-2.37-18.fc38.x86_64           13/29
          Verifying        : gnutls-3.8.5-1.fc38.x86_64                           14/29
          Verifying        : gnutls-3.8.4-1.fc38.x86_64                           15/29
          Verifying        : libnghttp2-1.52.0-3.fc38.x86_64                      16/29
          Verifying        : libnghttp2-1.52.0-2.fc38.x86_64                      17/29
          Verifying        : python-pip-wheel-22.3.1-4.fc38.noarch                18/29
          Verifying        : python-pip-wheel-22.3.1-3.fc38.noarch                19/29
          Verifying        : python3-3.11.9-2.fc38.x86_64                         20/29
          Verifying        : python3-3.11.8-2.fc38.x86_64                         21/29
          Verifying        : python3-libs-3.11.9-2.fc38.x86_64                    22/29
          Verifying        : python3-libs-3.11.8-2.fc38.x86_64                    23/29
          Verifying        : tpm2-tss-4.0.2-1.fc38.x86_64                         24/29
          Verifying        : tpm2-tss-4.0.1-3.fc38.x86_64                         25/29
          Verifying        : vim-data-2:9.1.393-1.fc38.noarch                     26/29
          Verifying        : vim-data-2:9.1.309-1.fc38.noarch                     27/29
          Verifying        : vim-minimal-2:9.1.393-1.fc38.x86_64                  28/29
          Verifying        : vim-minimal-2:9.1.309-1.fc38.x86_64                  29/29

        Upgraded:
          fedora-release-common-38-37.noarch
          fedora-release-container-38-37.noarch
          fedora-release-identity-container-38-37.noarch
          glibc-2.37-19.fc38.x86_64
          glibc-common-2.37-19.fc38.x86_64
          glibc-minimal-langpack-2.37-19.fc38.x86_64
          gnutls-3.8.5-1.fc38.x86_64
          libnghttp2-1.52.0-3.fc38.x86_64
          python-pip-wheel-22.3.1-4.fc38.noarch
          python3-3.11.9-2.fc38.x86_64
          python3-libs-3.11.9-2.fc38.x86_64
          tpm2-tss-4.0.2-1.fc38.x86_64
          vim-data-2:9.1.393-1.fc38.noarch
          vim-minimal-2:9.1.393-1.fc38.x86_64
        Installed:
          libxcrypt-compat-4.4.36-1.fc38.x86_64

        Complete!
        42 files removed
    ==> aa51aa7: IMAGE /tmp/velocity/build/fedora-38-aa51aa7/aa51aa7.sif (fedora@38) BUILT [0:01:33]

    ==> BUILT: /tmp/velocity/fedora-38__x86_64-fedora.sif

Adding Different Versions
#########################
So now we have a base Fedora image. That's great but before we move on let's make some different versions of the image
so that we have more options for building later. Edit the fedora ``specs.yaml`` and add some versions.

.. code-block:: yaml
    :caption: spec.yaml

    versions:
      - spec:
          - 38
          - 39
          - 40
          - 41
        when: distro=fedora

.. code-block:: bash

    $ velocity avail
    ==> fedora
        38
        39
        40
        41

Specifying Version
##################
When building an image Velocity will default to the latest image. To specify a version use ``<image>@<version>`` e.g.
``fedora@40``. Versions take the form ``<major>.<minor>.<patch>-<suffix>``. You can also specify greater than, less
than, and in-between via ``<image>@<version>:``, ``<image>@:<version>`` and ``<image>@<version>:<version>`` respectively.

Hello World!
############
Now let's get a little more complicated. Let's create an image that runs a python script which prints ``Hello, World!``. You
can give it whatever version you want:

.. code-block:: bash
    :caption: /tmp/velocity/images

    fedora
    ├── specs.yaml
    └── templates
        └── default.vtmp
    hello-world
    ├── files
    │   └── hello_world.py
    ├── specs.yaml
    └── templates
        └── default.vtmp

Notice that now there is a new folder called ``files`` with a python script in it.

.. code-block:: python
    :caption: hello_world.py

    #!/usr/bin/env python3

    print("Hello, World!")

.. code-block:: yaml
    :caption: specs.yaml

    versions:
      - spec: 1.0
    dependencies:
      - spec: fedora
        when: distro=fedora
    files:
      - name: hello_world.py


.. code-block:: text
    :caption: default.vtmp

    @from
        {{ __base__ }}

    @copy
        hello_world.py /hello_world

    @run
        dnf -y install python3
        chmod +x /hello_world

    @entry
        /hello_world


.. code-block:: bash

    $ velocity avail
    ==> fedora
        38
        39
        40
        41
    ==> hello-world
        1.0

.. code-block:: bash

    $ velocity build hello-world -v
    ==> Build Order:
        fedora@41-8a9a360
        hello-world@1.0-de9c02b

    ==> 8a9a360: BUILD fedora@41 ...
    ==> 8a9a360: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/fedora-41-8a9a360/script
        Bootstrap: docker
        From: docker.io/fedora:41

        %post
        dnf -y upgrade
        dnf clean all
    ==> 8a9a360: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/velocity/build/fedora-41-8a9a360/8a9a360.sif /tmp/velocity/build/fedora-41-8a9a360/script;
        Updating and loading repositories:
         Fedora 41 openh264 (From Cisco) - x86_ 100% |   6.5 KiB/s |   4.8 KiB |  00m01s
         Fedora 41 - x86_64 - Test Updates      100% |   1.8 MiB/s |   3.4 MiB |  00m02s
         Fedora 41 - x86_64                     100% |  13.9 MiB/s |  35.9 MiB |  00m03s
         Fedora 41 - x86_64 - Updates           100% |  50.3 KiB/s |  31.9 KiB |  00m01s
        Repositories loaded.
        Package                     Arch   Version        Repository                            Size
        Upgrading:
         libgcc                     x86_64 14.2.1-3.fc41  updates-testing                  274.6 KiB
           replacing libgcc         x86_64 14.2.1-1.fc41  34086d2996104518800c8d7dcc6139a1 274.6 KiB
         libgomp                    x86_64 14.2.1-3.fc41  updates-testing                  523.5 KiB
           replacing libgomp        x86_64 14.2.1-1.fc41  34086d2996104518800c8d7dcc6139a1 523.4 KiB
         libstdc++                  x86_64 14.2.1-3.fc41  updates-testing                    2.8 MiB
           replacing libstdc++      x86_64 14.2.1-1.fc41  34086d2996104518800c8d7dcc6139a1   2.8 MiB
         openssl-libs               x86_64 1:3.2.2-7.fc41 updates-testing                    7.8 MiB
           replacing openssl-libs   x86_64 1:3.2.2-5.fc41 34086d2996104518800c8d7dcc6139a1   7.8 MiB
         rpm                        x86_64 4.19.94-1.fc41 updates-testing                    3.1 MiB
           replacing rpm            x86_64 4.19.92-6.fc41 34086d2996104518800c8d7dcc6139a1   3.1 MiB
         rpm-build-libs             x86_64 4.19.94-1.fc41 updates-testing                  206.7 KiB
           replacing rpm-build-libs x86_64 4.19.92-6.fc41 34086d2996104518800c8d7dcc6139a1 206.7 KiB
         rpm-libs                   x86_64 4.19.94-1.fc41 updates-testing                  721.9 KiB
           replacing rpm-libs       x86_64 4.19.92-6.fc41 34086d2996104518800c8d7dcc6139a1 721.9 KiB
         systemd-libs               x86_64 256.6-1.fc41   updates-testing                    2.0 MiB
           replacing systemd-libs   x86_64 256.5-1.fc41   34086d2996104518800c8d7dcc6139a1   2.0 MiB
         zlib-ng-compat             x86_64 2.1.7-3.fc41   updates-testing                  134.0 KiB
           replacing zlib-ng-compat x86_64 2.1.7-2.fc41   34086d2996104518800c8d7dcc6139a1 134.0 KiB

        Transaction Summary:
         Upgrading:         9 packages
         Replacing:         9 packages

        Total size of inbound packages is 5 MiB. Need to download 5 MiB.
        After this operation 2 KiB will be used (install 17 MiB, remove 17 MiB).
        [1/9] libgcc-0:14.2.1-3.fc41.x86_64     100% | 132.2 KiB/s | 133.3 KiB |  00m01s
        [2/9] libstdc++-0:14.2.1-3.fc41.x86_64  100% | 583.3 KiB/s | 887.8 KiB |  00m02s
        [3/9] libgomp-0:14.2.1-3.fc41.x86_64    100% | 208.5 KiB/s | 354.1 KiB |  00m02s
        [4/9] rpm-0:4.19.94-1.fc41.x86_64       100% |   1.6 MiB/s | 547.6 KiB |  00m00s
        [5/9] rpm-build-libs-0:4.19.94-1.fc41.x 100% |   2.1 MiB/s |  99.1 KiB |  00m00s
        [6/9] openssl-libs-1:3.2.2-7.fc41.x86_6 100% |   2.6 MiB/s |   2.3 MiB |  00m01s
        [7/9] rpm-libs-0:4.19.94-1.fc41.x86_64  100% |   1.1 MiB/s | 309.5 KiB |  00m00s
        [8/9] zlib-ng-compat-0:2.1.7-3.fc41.x86 100% |   1.0 MiB/s |  77.7 KiB |  00m00s
        [9/9] systemd-libs-0:256.6-1.fc41.x86_6 100% |   2.6 MiB/s | 730.9 KiB |  00m00s
        --------------------------------------------------------------------------------
        [9/9] Total                             100% |   2.2 MiB/s |   5.4 MiB |  00m02s
        Running transaction
        [ 1/20] Verify package files            100% | 750.0   B/s |   9.0   B |  00m00s
        [ 2/20] Prepare transaction             100% |   1.6 KiB/s |  18.0   B |  00m00s
        [ 3/20] Upgrading libgcc-0:14.2.1-3.fc4 100% |  14.2 MiB/s | 276.3 KiB |  00m00s
        >>> Running post-install scriptlet: libgcc-0:14.2.1-3.fc41.x86_64
        >>> Stop post-install scriptlet: libgcc-0:14.2.1-3.fc41.x86_64
        [ 4/20] Upgrading zlib-ng-compat-0:2.1. 100% |  32.9 MiB/s | 134.8 KiB |  00m00s
        [ 5/20] Upgrading rpm-libs-0:4.19.94-1. 100% | 117.7 MiB/s | 723.4 KiB |  00m00s
        [ 6/20] Upgrading libgomp-0:14.2.1-3.fc 100% | 170.8 MiB/s | 524.8 KiB |  00m00s
        [ 7/20] Upgrading rpm-build-libs-0:4.19 100% |  15.6 MiB/s | 207.5 KiB |  00m00s
        >>> Running pre-install scriptlet: rpm-0:4.19.94-1.fc41.x86_64
        >>> Stop pre-install scriptlet: rpm-0:4.19.94-1.fc41.x86_64
        [ 8/20] Upgrading rpm-0:4.19.94-1.fc41. 100% | 104.3 MiB/s |   2.5 MiB |  00m00s
        [ 9/20] Upgrading openssl-libs-1:3.2.2- 100% | 190.9 MiB/s |   7.8 MiB |  00m00s
        [10/20] Upgrading libstdc++-0:14.2.1-3. 100% | 145.6 MiB/s |   2.8 MiB |  00m00s
        [11/20] Upgrading systemd-libs-0:256.6- 100% | 135.3 MiB/s |   2.0 MiB |  00m00s
        [12/20] Erasing rpm-build-libs-0:4.19.9 100% |   1.0 KiB/s |   5.0   B |  00m00s
        [13/20] Erasing libstdc++-0:14.2.1-1.fc 100% |   6.1 KiB/s |  31.0   B |  00m00s
        [14/20] Erasing systemd-libs-0:256.5-1. 100% |   2.4 KiB/s |  20.0   B |  00m00s
        [15/20] Erasing rpm-0:4.19.92-6.fc41.x8 100% |  26.7 KiB/s | 273.0   B |  00m00s
        [16/20] Erasing rpm-libs-0:4.19.92-6.fc 100% |   2.4 KiB/s |  10.0   B |  00m00s
        [17/20] Erasing openssl-libs-1:3.2.2-5. 100% |   9.5 KiB/s |  39.0   B |  00m00s
        [18/20] Erasing zlib-ng-compat-0:2.1.7- 100% |   1.2 KiB/s |   5.0   B |  00m00s
        [19/20] Erasing libgcc-0:14.2.1-1.fc41. 100% | 647.0   B/s |  11.0   B |  00m00s
        >>> Running post-uninstall scriptlet: libgcc-0:14.2.1-1.fc41.x86_64
        >>> Stop post-uninstall scriptlet: libgcc-0:14.2.1-1.fc41.x86_64
        [20/20] Erasing libgomp-0:14.2.1-1.fc41 100% |  43.0   B/s |   9.0   B |  00m00s
        >>> Running post-transaction scriptlet: rpm-0:4.19.94-1.fc41.x86_64
        >>> Stop post-transaction scriptlet: rpm-0:4.19.94-1.fc41.x86_64
        >>> Running trigger-install scriptlet: glibc-common-0:2.40-3.fc41.x86_64
        >>> Stop trigger-install scriptlet: glibc-common-0:2.40-3.fc41.x86_64
        >>> Running trigger-post-uninstall scriptlet: glibc-common-0:2.40-3.fc41.x86_64
        >>> Stop trigger-post-uninstall scriptlet: glibc-common-0:2.40-3.fc41.x86_64
        Complete!
        Removed 24 files, 13 directories. 0 errors occurred.
    ==> 8a9a360: IMAGE /tmp/velocity/build/fedora-41-8a9a360/8a9a360.sif (fedora@41) BUILT [0:00:21]

    ==> de9c02b: BUILD hello-world@1.0 ...
    ==> de9c02b: COPYING FILES ...
        FILE: /tmp/velocity/images/hello-world/files/hello_world.py -> /tmp/velocity/build/hello-world-1.0-de9c02b/hello_world.py
    ==> de9c02b: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/hello-world-1.0-de9c02b/script
        Bootstrap: localimage
        From: /tmp/velocity/build/fedora-41-8a9a360/8a9a360.sif

        %files
        hello_world.py /hello_world

        %post
        dnf -y install python3
        chmod +x /hello_world

        %runscript
        /hello_world
    ==> de9c02b: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/velocity/build/hello-world-1.0-de9c02b/de9c02b.sif /tmp/velocity/build/hello-world-1.0-de9c02b/script;
        Updating and loading repositories:
         Fedora 41 openh264 (From Cisco) - x86_ 100% |  11.1 KiB/s |   6.0 KiB |  00m01s
         Fedora 41 - x86_64                     100% |  11.7 MiB/s |  35.4 MiB |  00m03s
         Fedora 41 - x86_64 - Updates           100% |  50.1 KiB/s |  31.9 KiB |  00m01s
         Fedora 41 - x86_64 - Test Updates      100% |   1.8 MiB/s |   2.1 MiB |  00m01s
        Repositories loaded.
        Package                     Arch   Version           Repository           Size
        Installing:
         python3                    x86_64 3.13.0~rc2-1.fc41 fedora           31.8 KiB
        Installing dependencies:
         expat                      x86_64 2.6.3-1.fc41      updates-testing 291.5 KiB
         libb2                      x86_64 0.98.1-12.fc41    fedora           42.2 KiB
         mpdecimal                  x86_64 2.5.1-16.fc41     fedora          204.9 KiB
         python-pip-wheel           noarch 24.2-1.fc41       fedora            1.2 MiB
         python3-libs               x86_64 3.13.0~rc2-1.fc41 fedora           40.3 MiB
        Installing weak dependencies:
         python-unversioned-command noarch 3.13.0~rc2-1.fc41 fedora           23.0   B

        Transaction Summary:
         Installing:        7 packages

        Total size of inbound packages is 11 MiB. Need to download 11 MiB.
        After this operation 42 MiB will be used (install 42 MiB, remove 0 B).
        [1/7] libb2-0:0.98.1-12.fc41.x86_64     100% |  94.1 KiB/s |  25.7 KiB |  00m00s
        [2/7] python3-0:3.13.0~rc2-1.fc41.x86_6 100% |  95.9 KiB/s |  27.4 KiB |  00m00s
        [3/7] mpdecimal-0:2.5.1-16.fc41.x86_64  100% | 408.0 KiB/s |  89.0 KiB |  00m00s
        [4/7] expat-0:2.6.3-1.fc41.x86_64       100% | 447.4 KiB/s | 114.1 KiB |  00m00s
        [5/7] python-pip-wheel-0:24.2-1.fc41.no 100% |   2.5 MiB/s |   1.2 MiB |  00m00s
        [6/7] python-unversioned-command-0:3.13 100% | 125.1 KiB/s |  10.5 KiB |  00m00s
        [7/7] python3-libs-0:3.13.0~rc2-1.fc41. 100% |   8.1 MiB/s |   9.1 MiB |  00m01s
        --------------------------------------------------------------------------------
        [7/7] Total                             100% |   6.7 MiB/s |  10.6 MiB |  00m02s
        Running transaction
        [1/9] Verify package files              100% | 269.0   B/s |   7.0   B |  00m00s
        [2/9] Prepare transaction               100% | 280.0   B/s |   7.0   B |  00m00s
        [3/9] Installing expat-0:2.6.3-1.fc41.x 100% |  71.7 MiB/s | 293.6 KiB |  00m00s
        [4/9] Installing python-pip-wheel-0:24. 100% | 310.4 MiB/s |   1.2 MiB |  00m00s
        [5/9] Installing mpdecimal-0:2.5.1-16.f 100% |  50.3 MiB/s | 206.0 KiB |  00m00s
        [6/9] Installing libb2-0:0.98.1-12.fc41 100% |   4.7 MiB/s |  43.3 KiB |  00m00s
        [7/9] Installing python3-libs-0:3.13.0~ 100% | 139.9 MiB/s |  40.7 MiB |  00m00s
        [8/9] Installing python3-0:3.13.0~rc2-1 100% |  10.9 MiB/s |  33.6 KiB |  00m00s
        [9/9] Installing python-unversioned-com 100% |   1.8 KiB/s | 424.0   B |  00m00s
        >>> Running trigger-install scriptlet: glibc-common-0:2.40-3.fc41.x86_64
        >>> Stop trigger-install scriptlet: glibc-common-0:2.40-3.fc41.x86_64
        Complete!
    ==> de9c02b: IMAGE /tmp/velocity/build/hello-world-1.0-de9c02b/de9c02b.sif (hello-world@1.0) BUILT [0:00:14]

    ==> BUILT: /tmp/velocity/hello-world-1.0_fedora-41__x86_64-fedora.sif


Our hello-world image has been built!

.. code-block:: bash
    :emphasize-lines: 7

    $ ls
    total 190972
    drwxr-xr-x  4 xxx  users      4096 Sep 18 10:01 .
    drwxrwxrwt 31 root root     131072 Sep 18 10:01 ..
    drwxr-xr-x  4 xxx  users      4096 Sep 18 10:01 build
    -rwxr-xr-x  1 xxx  users  66007040 Sep 18 09:42 fedora-38__x86_64-fedora.sif
    -rwxr-xr-x  1 xxx  users 129392640 Sep 18 10:01 hello-world-1.0_fedora-41__x86_64-fedora.sif
    drwxr-xr-x  4 xxx  users      4096 Sep 18 09:44 images


Now you can run the image!

.. code-block:: bash

    $ apptainer run hello-world-1.0_fedora-41__x86_64-fedora.sif
    Hello, World!

OLCF Images
###########

Let's extend what we have done so far and explore some more features of Velocity using a base set of image definitions
provided at https://github.com/olcf/velocity-images. Clone the repository and run:

.. code-block:: bash

    export VELOCITY_IMAGE_PATH=<path to the cloned repo>:$VELOCITY_IMAGE_PATH

Let's check what images are available now.

.. note::

    Due to updates to https://github.com/olcf/velocity-images the output shown below may be different for you.

.. code-block:: bash

    $ velocity avail
    ==> fedora
        38
        39
        40
        41
    ==> gcc
        12.3.0
        13.2.0
        14.1.0
    ==> hello-world
        1.0
    ==> llvm
        17.0.0
        17.0.6
    ==> mpich
        3.4.3
    ==> rocm
        5.7.1
        6.0.1
        6.1.3

If you were to look at the contents of https://github.com/olcf/velocity-images you would notice that there is a
folder in it defining an ``ubuntu`` image. Why does that image not show up? At the beginning of this tutorial
we set ``export VELOCITY_DISTRO=fedora``. In the ``ubuntu`` ``specs.yaml`` file you would see:

.. code-block:: yaml

    versions:
      - spec:
          - 20.04
          - 22.04
          - 24.04
        when: distro=ubuntu

The ``when: distro=ubuntu`` means that the defined versions will not show up unless the distro is set to ``ubuntu``.
Run the following command and compare the difference.

.. code-block:: bash

    $ velocity -d ubuntu avail
    ==> gcc
        12.3.0
        13.2.0
        14.1.0
    ==> hello-world
        1.0
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

.. important::

    This is important because it keeps us from trying to build a container with two distros, but it may catch you off gaurd
    by hiding images you thought you had defined.

Now let try building our ``hello-world`` image on an ``ubuntu`` base. In the current state the build will fail but let's
run it anyway and trouble shoot it.

.. code-block:: bash

    $ velocity -d ubuntu build hello-world
    ==> Build Order:
        hello-world@1.0-8fe7227

    ==> 8fe7227: BUILD hello-world@1.0 ...
    ==> 8fe7227: COPYING FILES ...
    ==> 8fe7227: GENERATING SCRIPT ...
    Traceback (most recent call last):
      File "/tmp/velocity_env/lib/python3.10/site-packages/velocity/_backends.py", line 131, in generate_script
        if len(sections["@from"]) != 1:
    KeyError: '@from'

    During handling of the above exception, another exception occurred:

    Traceback (most recent call last):
      File "/usr/lib/python3.10/runpy.py", line 196, in _run_module_as_main
        return _run_code(code, main_globals, None,
      File "/usr/lib/python3.10/runpy.py", line 86, in _run_code
        exec(code, run_globals)
      File "/tmp/velocity_env/lib/python3.10/site-packages/velocity/__main__.py", line 111, in <module>
        builder.build()
      File "/tmp/velocity_env/lib/python3.10/site-packages/velocity/_build.py", line 128, in build
        self._build_image(u, last, name)
      File "/tmp/velocity_env/lib/python3.10/site-packages/velocity/_build.py", line 223, in _build_image
        script = self.backend_engine.generate_script(unit, script_variables)
      File "/tmp/velocity_env/lib/python3.10/site-packages/velocity/_backends.py", line 140, in generate_script
        raise TemplateSyntaxError("You must have an @from section in your template!")
    velocity._exceptions.TemplateSyntaxError: You must have an @from section in your template!

We see that an error occurred in the ``GENERATING SCRIPT`` section. But if we look under ``==> Build Order`` at the top
we will notice the real cause. The ``ubuntu`` image is not being built. This causes the error in script generation
because in our ``default.vtmp`` for ``hello-world`` we have ``{{ __base__ }}`` defined in our ``@from`` section which
looks for a previously built image to build on. Let's edit our ``hello-world`` ``specs.yaml``. It should look like this.

.. code-block:: yaml
    :caption: specs.yaml
    :emphasize-lines: 6-7

    versions:
      - spec: 1.0
    dependencies:
      - spec: fedora
        when: distro=fedora
      - spec: ubuntu
        when: distro=ubuntu
    files:
      - name: hello_world.py

Under the ``dependencies`` section we added the ``ubuntu`` image, but we specified it should only be a dependency when
our distro is set to ubuntu. You can test that Velocity is now adding ``ubuntu`` as a dependency by running:

.. code-block:: bash

    $ velocity -d ubuntu spec hello-world
      > hello-world@1.0-f6bfef8
         ^ubuntu@24.04-ce71495

Now we can try to build again, but it will fail with a new error.

.. code-block:: bash

    $ velocity -d ubuntu build hello-world
    ==> Build Order:
        ubuntu@24.04-ce71495
        hello-world@1.0-f6bfef8

    ==> ce71495: BUILD ubuntu@24.04 ...
    ==> ce71495: GENERATING SCRIPT ...
    ==> ce71495: BUILDING ...
    ==> ce71495: IMAGE /tmp/velocity/build/ubuntu-24.04-ce71495/ce71495.sif (ubuntu@24.04) BUILT [0:00:00]

    ==> f6bfef8: BUILD hello-world@1.0 ...
    ==> f6bfef8: COPYING FILES ...
    ==> f6bfef8: GENERATING SCRIPT ...
    ==> f6bfef8: BUILDING ...
        INFO:    Starting build...
        INFO:    Verifying bootstrap image /tmp/velocity/build/ubuntu-24.04-ce71495/ce71495.sif
        INFO:    Copying hello_world.py to /hello_world
        INFO:    Running post scriptlet
        + dnf -y install python3
        /.post.script: 1: dnf: not found
        FATAL:   While performing build: while running engine: exit status 127

Velocity prints out the error from the build ``dnf: not found``. Lets look back at the :doc:`vtmp </reference/vtmp>`
script we wrote for ``hello-world``. Under the ``@run`` section we had:

.. code-block:: text

    @run
        dnf -y install python3
        chmod +x /hello_world

We used dnf to install python because it is not installed in the fedora docker image by default. We need to edit this
script to support ``ubuntu``. Change the ``@run`` section to:

.. code-block:: text

    @run
        ?? distro=fedora |> dnf -y install python3 ??
        ?? distro=ubuntu |> apt -y install python3 ??
        chmod +x /hello_world

Now we can test by doing a verbose dry-run for ``fedora`` and ``ubuntu``.

.. code-block:: bash
    :emphasize-lines: 32
    :caption: fedora

    $ velocity build hello-world -dv
    ==> Build Order:
        fedora@41-8a9a360
        hello-world@1.0-3de9f9b

    ==> 8a9a360: BUILD fedora@41 --DRY-RUN ...
    ==> 8a9a360: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/fedora-41-8a9a360/script
        Bootstrap: docker
        From: docker.io/fedora:41

        %post
        dnf -y upgrade
        dnf clean all
    ==> 8a9a360: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/velocity/build/fedora-41-8a9a360/8a9a360.sif /tmp/velocity/build/fedora-41-8a9a360/script;
    ==> 8a9a360: IMAGE /tmp/velocity/build/fedora-41-8a9a360/8a9a360.sif (fedora@41) BUILT [0:00:00]

    ==> 3de9f9b: BUILD hello-world@1.0 --DRY-RUN ...
    ==> 3de9f9b: COPYING FILES ...
        FILE: /tmp/velocity/images/hello-world/files/hello_world.py -> /tmp/velocity/build/hello-world-1.0-3de9f9b/hello_world.py
    ==> 3de9f9b: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/hello-world-1.0-3de9f9b/script
        Bootstrap: localimage
        From: /tmp/velocity/build/fedora-41-8a9a360/8a9a360.sif

        %files
        hello_world.py /hello_world

        %post
        dnf -y install python3
        chmod +x /hello_world

        %runscript
        /hello_world
    ==> 3de9f9b: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/velocity/build/hello-world-1.0-3de9f9b/3de9f9b.sif /tmp/velocity/build/hello-world-1.0-3de9f9b/script;
    ==> 3de9f9b: IMAGE /tmp/velocity/build/hello-world-1.0-3de9f9b/3de9f9b.sif (hello-world@1.0) BUILT [0:00:00]

    ==> BUILT: /tmp/velocity/hello-world-1.0_fedora-41__x86_64-fedora.sif

.. code-block:: bash
    :emphasize-lines: 37
    :caption: ubuntu

    $ velocity -d ubuntu build hello-world -dv
    ==> Build Order:
        ubuntu@24.04-ce71495
        hello-world@1.0-b03891d

    ==> ce71495: BUILD ubuntu@24.04 --DRY-RUN ...
    ==> ce71495: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/ubuntu-24.04-ce71495/script
        Bootstrap: docker
        From: docker.io/ubuntu:24.04

        %post
        export DEBIAN_FRONTEND="noninteractive"
        apt -y update
        apt -y upgrade
        apt clean

        %environment
        export DEBIAN_FRONTEND="noninteractive"
    ==> ce71495: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/velocity/build/ubuntu-24.04-ce71495/ce71495.sif /tmp/velocity/build/ubuntu-24.04-ce71495/script;
    ==> ce71495: IMAGE /tmp/velocity/build/ubuntu-24.04-ce71495/ce71495.sif (ubuntu@24.04) BUILT [0:00:00]

    ==> b03891d: BUILD hello-world@1.0 --DRY-RUN ...
    ==> b03891d: COPYING FILES ...
        FILE: /tmp/velocity/images/hello-world/files/hello_world.py -> /tmp/velocity/build/hello-world-1.0-b03891d/hello_world.py
    ==> b03891d: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/hello-world-1.0-b03891d/script
        Bootstrap: localimage
        From: /tmp/velocity/build/ubuntu-24.04-ce71495/ce71495.sif

        %files
        hello_world.py /hello_world

        %post
        apt -y install python3
        chmod +x /hello_world

        %runscript
        /hello_world
    ==> b03891d: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/velocity/build/hello-world-1.0-b03891d/b03891d.sif /tmp/velocity/build/hello-world-1.0-b03891d/script;
    ==> b03891d: IMAGE /tmp/velocity/build/hello-world-1.0-b03891d/b03891d.sif (hello-world@1.0) BUILT [0:00:00]

    ==> BUILT: /tmp/velocity/hello-world-1.0_ubuntu-24.04__x86_64-ubuntu.sif

We can see that each build uses the correct command to install python. Now we can actually build the image.

.. code-block:: bash

    $ velocity -d ubuntu build hello-world
    ==> Build Order:
        ubuntu@24.04-ce71495
        hello-world@1.0-b03891d

    ==> ce71495: BUILD ubuntu@24.04 ...
    ==> ce71495: GENERATING SCRIPT ...
    ==> ce71495: BUILDING ...
    ==> ce71495: IMAGE /tmp/velocity/build/ubuntu-24.04-ce71495/ce71495.sif (ubuntu@24.04) BUILT [0:00:00]

    ==> b03891d: BUILD hello-world@1.0 ...
    ==> b03891d: COPYING FILES ...
    ==> b03891d: GENERATING SCRIPT ...
    ==> b03891d: BUILDING ...
    ==> b03891d: IMAGE /tmp/velocity/build/hello-world-1.0-b03891d/b03891d.sif (hello-world@1.0) BUILT [0:00:09]

    ==> BUILT: /tmp/velocity/hello-world-1.0_ubuntu-24.04__x86_64-ubuntu.sif

This example is a demonstration of one of the major strengths of Velocity. The ``hello-world`` image can now be built
on any version of ``fedora`` or ``ubuntu``, but instead of having a separate script for each version and distro we have
just three. One for ``fedora``, one for ``ubuntu`` and one for ``hello-world``. This may not seem like a big win for an
example like ``hello-world``; however, this becomes a big win for images like the ``gcc`` image in
https://github.com/olcf/velocity-images. If you look at the ``gcc`` image ``default.vtmp`` script you will see that it can
build practically any version of gcc on ``ubuntu``, ``opensuse`` and ``rockylinux``. And all of that with only 24 lines
of code (in the gcc script).

The last thing we need to look at for this tutorial is Velocity's support for multiple container backends. Let's look at
a dry-run example of the ``fedora`` image that we have been building with ``apptainer``.

.. code-block::
    :emphasize-lines: 8-13,16,19

    $ velocity build fedora -vd
    ==> Build Order:
        fedora@41-8a9a360

    ==> 8a9a360: BUILD fedora@41 --DRY-RUN ...
    ==> 8a9a360: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/fedora-41-8a9a360/script
        Bootstrap: docker
        From: docker.io/fedora:41

        %post
        dnf -y upgrade
        dnf clean all
    ==> 8a9a360: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/velocity/build/fedora-41-8a9a360/8a9a360.sif /tmp/velocity/build/fedora-41-8a9a360/script;
    ==> 8a9a360: IMAGE /tmp/velocity/build/fedora-41-8a9a360/8a9a360.sif (fedora@41) BUILT [0:00:00]

    ==> BUILT: /tmp/velocity/fedora-41__x86_64-fedora.sif

Next let's look at the same thing but with the backend set to ``podman``.

.. warning::

    If Podman is not installed this will fail. Conversely, if you are on a system that does not have Apptainer
    installed, ``build`` commands using it will fail.

.. code-block::
    :emphasize-lines: 8-11,14,17

    $ velocity -b podman build fedora -vd
    ==> Build Order:
        fedora@41-bd4bd64

    ==> bd4bd64: BUILD fedora@41 --DRY-RUN ...
    ==> bd4bd64: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/fedora-41-bd4bd64/script
        FROM docker.io/fedora:41

        RUN dnf -y upgrade && \
            dnf clean all
    ==> bd4bd64: BUILDING ...
        #!/usr/bin/env bash
        podman build -f /tmp/velocity/build/fedora-41-bd4bd64/script -t localhost/bd4bd64:latest .;
    ==> bd4bd64: IMAGE localhost/bd4bd64:latest (fedora@41) BUILT [0:00:00]

    ==> BUILT: localhost/fedora-41__x86_64-fedora:latest

As you can see Velocity automatically renders the scripts to the correct format and changes the build commands
to use Podman. Amazing!!!

One last note about debugging builds with Velocity. We set ``VELOCITY_BUILD_DIR`` at the beginning of this tutorial.
If you look in the directory that it points to you will find a folder for each image that was built. Each folder
contains the rendered script, build log, files generated by the build (e.g SIF files), build commands, and any files
that were needed for the build (e.g. ``hello_world.py``). All of these can be very useful for debugging a build.
One very helpful feature is that the build of an image can be run manually by running the ``build`` script in a folder.

.. code-block:: bash
    :caption: Build Directory Contents

    .
    ├── fedora-38-aa51aa7
    │ ├── aa51aa7.sif
    │ ├── build
    │ ├── log
    │ └── script
    ├── fedora-41-8a9a360
    │ ├── 8a9a360.sif
    │ ├── build
    │ ├── log
    │ └── script
    ├── fedora-41-bd4bd64
    │ ├── build
    │ └── script
    ├── hello-world-1.0-12e1055
    │ ├── 12e1055.sif
    │ ├── build
    │ ├── hello_world.py
    │ ├── log
    │ └── script
    ├── hello-world-1.0-3de9f9b
    │ ├── build
    │ ├── hello_world.py
    │ └── script
    ├── hello-world-1.0-8fe7227 # here is one of the failed builds
    │ └── hello_world.py
    ├── hello-world-1.0-b03891d
    │ ├── b03891d.sif
    │ ├── build
    │ ├── hello_world.py
    │ ├── log
    │ └── script
    ├── hello-world-1.0-f6bfef8
    │ ├── build
    │ ├── hello_world.py
    │ ├── log
    │ └── script
    └── ubuntu-24.04-ce71495
        ├── build
        ├── ce71495.sif
        ├── log
        └── script
