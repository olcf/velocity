*************************
Creating Your First Image
*************************

Prerequisites
#############
You will need to have the Velocity repo cloned and the following environment variables set. You can do this by
sourcing the `setup-env.sh` script.

.. code-block:: bash

    VELOCITY_IMAGE_DIR=<path to image dir>
    VELOCITY_BACKEND=podman # if you use apptainer you will need to make changes to some of the examples
    VELOCITY_BUILD_DIR=/tmp/velocity/build
    VELOCITY_SYSTEM=x86_64  # if you use a different system name you will need to make changes to some of the examples
    VELOCITY_ROOT=<git repo> # you will also need to add this to PATH
    VELOCITY_DISTRO=fedora

Base Image
##########
Let's start with a simple base image. This image will pull an fedora docker image and update the packages.
Start by creating a directory in the image directory called `fedora` (for this tutorial we are starting with an empty
image directory). Next we need to create a directory in the `fedora` directory for the version of fedora that we want.
Let's use `38`. In this directory create a file called `specifications.yaml` and a directory called `templates` with
a file named `fedora.vtmp`. Your image directory and files should now look like this.

.. code-block:: bash
    :caption: VELOCITY_IMAGE_DIR

    .
    └── fedora
        └── 38
            ├── specifications.yaml
            └── templates
                └── fedora.vtmp

.. code-block:: yaml
    :caption: fedora/38/specifications.yaml

    build_specifications:

      x86_64:
        podman:
          fedora: {}


.. code-block:: text
    :caption: fedora/38/templates/fedora.vtmp

    @from
        docker.io/fedora:38

    @run
        dnf -y upgrade

    @label
        velocity.config.system %(__system__)
        velocity.config.backend %(__backend__)
        velocity.config.distro %(__distro__)
        velocity.image.%(__name__)__%(__tag__) %(__hash__)

Now if you run `velocity avail` you should get the following.

.. code-block:: bash

    user@hostname:~$ velocity avail
    ==> System: x86_64
    ==> Backend: podman
    ==> Distro: fedora

    ==> fedora
            38

Now build the image.

.. code-block:: bash

    user@hostname:~$ velocity build fedora
    ==> System: x86_64
    ==> Backend: podman
    ==> Distro: fedora

    ==> Build Order:
            fedora@=38

    ==> yftozouc: BUILD fedora@=38 ...
    ==> yftozouc: GENERATING SCRIPT ...
    ==> yftozouc: BUILDING ...
    ==> yftozouc: IMAGE localhost/fedora__38__x86_64__fedora:latest (fedora@=38) BUILT [0:07:10]

If you wish to see more output you can add the `-v` flag:

.. code-block:: bash

    user@hostname:~$ velocity build fedora -v
    ==> System: x86_64
    ==> Backend: podman
    ==> Distro: fedora

    ==> Build Order:
            fedora@=38

    ==> xuoykrdt: BUILD fedora@=38 ...
    ==> xuoykrdt: GENERATING SCRIPT ...
            SCRIPT: /tmp/velocity/build/xuoykrdt/script
            FROM docker.io/fedora:38

            RUN dnf -y upgrade

            LABEL velocity.config.system="x86_64" \
                velocity.config.backend="podman" \
                velocity.config.distro="fedora" \
                velocity.image.fedora__38="ff9fa85cf102560cf3fe2014c3c758fbb3809247537abbeab2c4b67c62dda164"

    ==> xuoykrdt: BUILDING ...
            #!/usr/bin/env bash
            podman build -f /tmp/velocity/build/xuoykrdt/script -t localhost/fedora__38__x86_64__fedora:latest .;
            STEP 1/3: FROM docker.io/fedora:38
            STEP 2/3: RUN dnf -y upgrade
            Fedora 38 - x86_64                              131 kB/s |  84 MB     10:53
            Fedora 38 openh264 (From Cisco) - x86_64        2.9 kB/s | 2.6 kB     00:00
            Fedora Modular 38 - x86_64                      1.1 MB/s | 2.8 MB     00:02
            Fedora 38 - x86_64 - Updates                    4.5 MB/s |  40 MB     00:09
            Fedora Modular 38 - x86_64 - Updates            152 kB/s | 2.1 MB     00:14
            Last metadata expiration check: 0:00:01 ago on Wed Mar 27 20:09:54 2024.
            Dependencies resolved.
            ================================================================================
             Package                       Arch     Version                 Repo       Size
            ================================================================================
            Upgrading:
             curl                          x86_64   8.0.1-7.fc38            updates   348 k
             dnf                           noarch   4.19.0-1.fc38           updates   507 k
             dnf-data                      noarch   4.19.0-1.fc38           updates    39 k
             elfutils-default-yama-scope   noarch   0.191-1.fc38            updates    12 k
             elfutils-libelf               x86_64   0.191-1.fc38            updates   208 k
             elfutils-libs                 x86_64   0.191-1.fc38            updates   263 k
             expat                         x86_64   2.6.0-1.fc38            updates   112 k
             keyutils-libs                 x86_64   1.6.3-1.fc38            updates    31 k
             libcurl                       x86_64   8.0.1-7.fc38            updates   315 k
             libdnf                        x86_64   0.73.0-1.fc38           updates   681 k
             libgcc                        x86_64   13.2.1-7.fc38           updates   115 k
             libgomp                       x86_64   13.2.1-7.fc38           updates   324 k
             libsolv                       x86_64   0.7.28-1.fc38           updates   426 k
             libstdc++                     x86_64   13.2.1-7.fc38           updates   870 k
             ncurses-base                  noarch   6.4-7.20230520.fc38.1   updates    88 k
             ncurses-libs                  x86_64   6.4-7.20230520.fc38.1   updates   336 k
             python3                       x86_64   3.11.8-2.fc38           updates    28 k
             python3-dnf                   noarch   4.19.0-1.fc38           updates   606 k
             python3-hawkey                x86_64   0.73.0-1.fc38           updates   107 k
             python3-libdnf                x86_64   0.73.0-1.fc38           updates   859 k
             python3-libs                  x86_64   3.11.8-2.fc38           updates   9.6 M
             systemd-libs                  x86_64   253.17-1.fc38           updates   649 k
             vim-data                      noarch   2:9.1.158-1.fc38        updates    23 k
             vim-minimal                   x86_64   2:9.1.158-1.fc38        updates   808 k
             yum                           noarch   4.19.0-1.fc38           updates    37 k

            Transaction Summary
            ================================================================================
            Upgrade  25 Packages

            Total download size: 17 M
            Downloading Packages:
            (1/25): dnf-data-4.19.0-1.fc38.noarch.rpm       107 kB/s |  39 kB     00:00
            (2/25): elfutils-default-yama-scope-0.191-1.fc3 224 kB/s |  12 kB     00:00
            (3/25): curl-8.0.1-7.fc38.x86_64.rpm            637 kB/s | 348 kB     00:00
            (4/25): dnf-4.19.0-1.fc38.noarch.rpm            807 kB/s | 507 kB     00:00
            (5/25): elfutils-libelf-0.191-1.fc38.x86_64.rpm 901 kB/s | 208 kB     00:00
            (6/25): expat-2.6.0-1.fc38.x86_64.rpm           1.1 MB/s | 112 kB     00:00
            (7/25): keyutils-libs-1.6.3-1.fc38.x86_64.rpm   331 kB/s |  31 kB     00:00
            (8/25): elfutils-libs-0.191-1.fc38.x86_64.rpm   1.1 MB/s | 263 kB     00:00
            (9/25): libgcc-13.2.1-7.fc38.x86_64.rpm         872 kB/s | 115 kB     00:00
            (10/25): libcurl-8.0.1-7.fc38.x86_64.rpm        1.7 MB/s | 315 kB     00:00
            (11/25): libgomp-13.2.1-7.fc38.x86_64.rpm       1.8 MB/s | 324 kB     00:00
            (12/25): libdnf-0.73.0-1.fc38.x86_64.rpm        1.8 MB/s | 681 kB     00:00
            (13/25): libsolv-0.7.28-1.fc38.x86_64.rpm       2.1 MB/s | 426 kB     00:00
            (14/25): ncurses-base-6.4-7.20230520.fc38.1.noa 423 kB/s |  88 kB     00:00
            (15/25): ncurses-libs-6.4-7.20230520.fc38.1.x86 1.3 MB/s | 336 kB     00:00
            (16/25): python3-3.11.8-2.fc38.x86_64.rpm       286 kB/s |  28 kB     00:00
            (17/25): libstdc++-13.2.1-7.fc38.x86_64.rpm     1.8 MB/s | 870 kB     00:00
            (18/25): python3-hawkey-0.73.0-1.fc38.x86_64.rp 834 kB/s | 107 kB     00:00
            (19/25): python3-dnf-4.19.0-1.fc38.noarch.rpm   2.5 MB/s | 606 kB     00:00
            (20/25): python3-libdnf-0.73.0-1.fc38.x86_64.rp 1.6 MB/s | 859 kB     00:00
            (21/25): systemd-libs-253.17-1.fc38.x86_64.rpm  1.4 MB/s | 649 kB     00:00
            (22/25): vim-data-9.1.158-1.fc38.noarch.rpm     196 kB/s |  23 kB     00:00
            (23/25): yum-4.19.0-1.fc38.noarch.rpm           270 kB/s |  37 kB     00:00
            (24/25): vim-minimal-9.1.158-1.fc38.x86_64.rpm  2.5 MB/s | 808 kB     00:00
            (25/25): python3-libs-3.11.8-2.fc38.x86_64.rpm  3.6 MB/s | 9.6 MB     00:02
            --------------------------------------------------------------------------------
            Total                                           3.6 MB/s |  17 MB     00:04
            Running transaction check
            Transaction check succeeded.
            Running transaction test
            Transaction test succeeded.
            Running transaction
              Preparing        :                                                        1/1
              Upgrading        : libgcc-13.2.1-7.fc38.x86_64                           1/50
              Running scriptlet: libgcc-13.2.1-7.fc38.x86_64                           1/50
              Upgrading        : libstdc++-13.2.1-7.fc38.x86_64                        2/50
              Upgrading        : libsolv-0.7.28-1.fc38.x86_64                          3/50
              Upgrading        : libdnf-0.73.0-1.fc38.x86_64                           4/50
              Upgrading        : vim-data-2:9.1.158-1.fc38.noarch                      5/50
              Upgrading        : ncurses-base-6.4-7.20230520.fc38.1.noarch             6/50
              Upgrading        : ncurses-libs-6.4-7.20230520.fc38.1.x86_64             7/50
              Upgrading        : libcurl-8.0.1-7.fc38.x86_64                           8/50
              Upgrading        : expat-2.6.0-1.fc38.x86_64                             9/50
              Upgrading        : python3-3.11.8-2.fc38.x86_64                         10/50
              Upgrading        : python3-libs-3.11.8-2.fc38.x86_64                    11/50
              Upgrading        : python3-libdnf-0.73.0-1.fc38.x86_64                  12/50
              Upgrading        : python3-hawkey-0.73.0-1.fc38.x86_64                  13/50
              Upgrading        : elfutils-libelf-0.191-1.fc38.x86_64                  14/50
              Upgrading        : elfutils-default-yama-scope-0.191-1.fc38.noarch      15/50
              Running scriptlet: elfutils-default-yama-scope-0.191-1.fc38.noarch      15/50
              Upgrading        : dnf-data-4.19.0-1.fc38.noarch                        16/50
              Upgrading        : python3-dnf-4.19.0-1.fc38.noarch                     17/50
              Upgrading        : dnf-4.19.0-1.fc38.noarch                             18/50
              Running scriptlet: dnf-4.19.0-1.fc38.noarch                             18/50
              Upgrading        : yum-4.19.0-1.fc38.noarch                             19/50
              Upgrading        : elfutils-libs-0.191-1.fc38.x86_64                    20/50
              Upgrading        : curl-8.0.1-7.fc38.x86_64                             21/50
              Upgrading        : vim-minimal-2:9.1.158-1.fc38.x86_64                  22/50
              Upgrading        : systemd-libs-253.17-1.fc38.x86_64                    23/50
              Upgrading        : libgomp-13.2.1-7.fc38.x86_64                         24/50
              Upgrading        : keyutils-libs-1.6.3-1.fc38.x86_64                    25/50
              Cleanup          : elfutils-libs-0.190-2.fc38.x86_64                    26/50
              Cleanup          : systemd-libs-253.15-2.fc38.x86_64                    27/50
              Cleanup          : vim-minimal-2:9.1.113-1.fc38.x86_64                  28/50
              Cleanup          : curl-8.0.1-6.fc38.x86_64                             29/50
              Cleanup          : yum-4.18.2-1.fc38.noarch                             30/50
              Running scriptlet: dnf-4.18.2-1.fc38.noarch                             31/50
              Cleanup          : dnf-4.18.2-1.fc38.noarch                             31/50
              Running scriptlet: dnf-4.18.2-1.fc38.noarch                             31/50
              Cleanup          : python3-dnf-4.18.2-1.fc38.noarch                     32/50
              Cleanup          : dnf-data-4.18.2-1.fc38.noarch                        33/50
              Cleanup          : vim-data-2:9.1.113-1.fc38.noarch                     34/50
              Cleanup          : elfutils-default-yama-scope-0.190-2.fc38.noarch      35/50
              Cleanup          : python3-hawkey-0.72.0-1.fc38.x86_64                  36/50
              Cleanup          : python3-libdnf-0.72.0-1.fc38.x86_64                  37/50
              Cleanup          : libdnf-0.72.0-1.fc38.x86_64                          38/50
              Cleanup          : libstdc++-13.2.1-4.fc38.x86_64                       39/50
              Cleanup          : python3-libs-3.11.7-2.fc38.x86_64                    40/50
              Cleanup          : python3-3.11.7-2.fc38.x86_64                         41/50
              Cleanup          : ncurses-libs-6.4-7.20230520.fc38.x86_64              42/50
              Cleanup          : ncurses-base-6.4-7.20230520.fc38.noarch              43/50
              Cleanup          : expat-2.5.0-2.fc38.x86_64                            44/50
              Cleanup          : libgcc-13.2.1-4.fc38.x86_64                          45/50
              Running scriptlet: libgcc-13.2.1-4.fc38.x86_64                          45/50
              Cleanup          : libsolv-0.7.27-1.fc38.x86_64                         46/50
              Cleanup          : libcurl-8.0.1-6.fc38.x86_64                          47/50
              Cleanup          : elfutils-libelf-0.190-2.fc38.x86_64                  48/50
              Cleanup          : libgomp-13.2.1-4.fc38.x86_64                         49/50
              Cleanup          : keyutils-libs-1.6.1-6.fc38.x86_64                    50/50
              Running scriptlet: keyutils-libs-1.6.1-6.fc38.x86_64                    50/50
              Verifying        : curl-8.0.1-7.fc38.x86_64                              1/50
              Verifying        : curl-8.0.1-6.fc38.x86_64                              2/50
              Verifying        : dnf-4.19.0-1.fc38.noarch                              3/50
              Verifying        : dnf-4.18.2-1.fc38.noarch                              4/50
              Verifying        : dnf-data-4.19.0-1.fc38.noarch                         5/50
              Verifying        : dnf-data-4.18.2-1.fc38.noarch                         6/50
              Verifying        : elfutils-default-yama-scope-0.191-1.fc38.noarch       7/50
              Verifying        : elfutils-default-yama-scope-0.190-2.fc38.noarch       8/50
              Verifying        : elfutils-libelf-0.191-1.fc38.x86_64                   9/50
              Verifying        : elfutils-libelf-0.190-2.fc38.x86_64                  10/50
              Verifying        : elfutils-libs-0.191-1.fc38.x86_64                    11/50
              Verifying        : elfutils-libs-0.190-2.fc38.x86_64                    12/50
              Verifying        : expat-2.6.0-1.fc38.x86_64                            13/50
              Verifying        : expat-2.5.0-2.fc38.x86_64                            14/50
              Verifying        : keyutils-libs-1.6.3-1.fc38.x86_64                    15/50
              Verifying        : keyutils-libs-1.6.1-6.fc38.x86_64                    16/50
              Verifying        : libcurl-8.0.1-7.fc38.x86_64                          17/50
              Verifying        : libcurl-8.0.1-6.fc38.x86_64                          18/50
              Verifying        : libdnf-0.73.0-1.fc38.x86_64                          19/50
              Verifying        : libdnf-0.72.0-1.fc38.x86_64                          20/50
              Verifying        : libgcc-13.2.1-7.fc38.x86_64                          21/50
              Verifying        : libgcc-13.2.1-4.fc38.x86_64                          22/50
              Verifying        : libgomp-13.2.1-7.fc38.x86_64                         23/50
              Verifying        : libgomp-13.2.1-4.fc38.x86_64                         24/50
              Verifying        : libsolv-0.7.28-1.fc38.x86_64                         25/50
              Verifying        : libsolv-0.7.27-1.fc38.x86_64                         26/50
              Verifying        : libstdc++-13.2.1-7.fc38.x86_64                       27/50
              Verifying        : libstdc++-13.2.1-4.fc38.x86_64                       28/50
              Verifying        : ncurses-base-6.4-7.20230520.fc38.1.noarch            29/50
              Verifying        : ncurses-base-6.4-7.20230520.fc38.noarch              30/50
              Verifying        : ncurses-libs-6.4-7.20230520.fc38.1.x86_64            31/50
              Verifying        : ncurses-libs-6.4-7.20230520.fc38.x86_64              32/50
              Verifying        : python3-3.11.8-2.fc38.x86_64                         33/50
              Verifying        : python3-3.11.7-2.fc38.x86_64                         34/50
              Verifying        : python3-dnf-4.19.0-1.fc38.noarch                     35/50
              Verifying        : python3-dnf-4.18.2-1.fc38.noarch                     36/50
              Verifying        : python3-hawkey-0.73.0-1.fc38.x86_64                  37/50
              Verifying        : python3-hawkey-0.72.0-1.fc38.x86_64                  38/50
              Verifying        : python3-libdnf-0.73.0-1.fc38.x86_64                  39/50
              Verifying        : python3-libdnf-0.72.0-1.fc38.x86_64                  40/50
              Verifying        : python3-libs-3.11.8-2.fc38.x86_64                    41/50
              Verifying        : python3-libs-3.11.7-2.fc38.x86_64                    42/50
              Verifying        : systemd-libs-253.17-1.fc38.x86_64                    43/50
              Verifying        : systemd-libs-253.15-2.fc38.x86_64                    44/50
              Verifying        : vim-data-2:9.1.158-1.fc38.noarch                     45/50
              Verifying        : vim-data-2:9.1.113-1.fc38.noarch                     46/50
              Verifying        : vim-minimal-2:9.1.158-1.fc38.x86_64                  47/50
              Verifying        : vim-minimal-2:9.1.113-1.fc38.x86_64                  48/50
              Verifying        : yum-4.19.0-1.fc38.noarch                             49/50
              Verifying        : yum-4.18.2-1.fc38.noarch                             50/50

            Upgraded:
              curl-8.0.1-7.fc38.x86_64
              dnf-4.19.0-1.fc38.noarch
              dnf-data-4.19.0-1.fc38.noarch
              elfutils-default-yama-scope-0.191-1.fc38.noarch
              elfutils-libelf-0.191-1.fc38.x86_64
              elfutils-libs-0.191-1.fc38.x86_64
              expat-2.6.0-1.fc38.x86_64
              keyutils-libs-1.6.3-1.fc38.x86_64
              libcurl-8.0.1-7.fc38.x86_64
              libdnf-0.73.0-1.fc38.x86_64
              libgcc-13.2.1-7.fc38.x86_64
              libgomp-13.2.1-7.fc38.x86_64
              libsolv-0.7.28-1.fc38.x86_64
              libstdc++-13.2.1-7.fc38.x86_64
              ncurses-base-6.4-7.20230520.fc38.1.noarch
              ncurses-libs-6.4-7.20230520.fc38.1.x86_64
              python3-3.11.8-2.fc38.x86_64
              python3-dnf-4.19.0-1.fc38.noarch
              python3-hawkey-0.73.0-1.fc38.x86_64
              python3-libdnf-0.73.0-1.fc38.x86_64
              python3-libs-3.11.8-2.fc38.x86_64
              systemd-libs-253.17-1.fc38.x86_64
              vim-data-2:9.1.158-1.fc38.noarch
              vim-minimal-2:9.1.158-1.fc38.x86_64
              yum-4.19.0-1.fc38.noarch

            Complete!
            --> 787eba03a2e
            STEP 3/3: LABEL velocity.config.system="x86_64"     velocity.config.backend="podman"     velocity.config.distro="fedora"     velocity.image.fedora__38="ff9fa85cf102560cf3fe2014c3c758fbb3809247537abbeab2c4b67c62dda164"
            COMMIT localhost/fedora__38__x86_64__fedora:latest
            --> 17c3457c281
            Successfully tagged localhost/fedora__38__x86_64__fedora:latest
            17c3457c281309909691b183b77323eb56390792a787e4a319b494d40868c907
    ==> xuoykrdt: IMAGE localhost/fedora__38__x86_64__fedora:latest (fedora@=38) BUILT [0:13:27]

Adding Different Versions
#########################
So now we have a base Fedora image. That's great but before we move on let's make some different versions of the image
so that we have more options for building later. Go ahead and copy the `fedora/38` directory several times:

.. code-block:: bash

    cp -rf fedora/38/ fedora/39
    cp -rf fedora/38/ fedora/40
    cp -rf fedora/38/ fedora/41

For each of the versions you will need to go in and change the tag on the source. For example `docker.io/fedora:38`
in `fedora/40/template/fedora.vtmp` should be changed to `docker.io/fedora:40`.

.. code-block:: bash
    :caption: VELOCITY_IMAGE_DIR

    .
    └── fedora
        ├── 38
        │    ├── specifications.yaml
        │    └── templates
        │        └── fedora.vtmp
        ├── 39
        │    ├── specifications.yaml
        │    └── templates
        │        └── fedora.vtmp
        ├── 40
        │    ├── specifications.yaml
        │    └── templates
        │        └── fedora.vtmp
        └── 41
            ├── specifications.yaml
            └── templates
                └── fedora.vtmp

.. code-block:: bash

    user@hostname:~$ velocity avail
    ==> System: x86_64
    ==> Backend: podman
    ==> Distro: fedora

    ==> fedora
            38
            39
            40
            41

Specifying Version
##################
When building an image Velocity will default to the latest image. To specify a version use `<image>@=<version>` e.g.
fedora\@=40. Versions are compared by splitting the version string up based on periods and then comparing the sections
left to right alphanumerically.

Hello World!
############
Now let's get a little more complicated. Let's create an image that runs a python script which prints hello world. You
can give it whatever version you want:

.. code-block:: bash
    :caption: VELOCITY_IMAGE_DIR

    .
    ├── fedora
    │    ├── 38
    │    │   ├── specifications.yaml
    │    │   └── templates
    │    │       └── fedora.vtmp
    │    ├── 39
    │    │   ├── specifications.yaml
    │    │   └── templates
    │    │       └── fedora.vtmp
    │    ├── 40
    │    │   ├── specifications.yaml
    │    │   └── templates
    │    │       └── fedora.vtmp
    │    └── 41
    │        ├── specifications.yaml
    │        └── templates
    │            └── fedora.vtmp
    └── hello-world
        └── 1.0
            ├── x86_64
            │   └── hello_world.py
            ├── specifications.yaml
            └── templates
                └── fedora.vtmp

Notice that now there is a new folder called `x86_64` with a python file in it.

.. code-block:: bash
    :caption: hello-world/1.0/x86_64/hello_world.py

    #!/usr/bin/env python3

    print("Hello, World!")

.. code-block:: yaml
    :caption: hello-world/1.0/specifications.yaml

    build_specifications:

      x86_64:
        podman:
          fedora:
            dependencies:
              - fedora
            variables:
              fr: fakeroot


.. code-block:: text
    :caption: hello-world/1.0/templates/fedora.vtmp

    @from
        %(__base__)

    @copy
        hello_world.py /hello_world.py

    @entry
        /hello_world.py

    @label
        velocity.image.%(__name__)__%(__tag__) %(__hash__)

.. code-block:: bash

    user@hostname:~$ velocity avail
    ==> System: x86_64
    ==> Backend: podman
    ==> Distro: fedora

    ==> fedora
            38
            39
            40
            41
    ==> hello-world
            1.0

.. code-block:: bash

    user@hostname:~$ velocity build hello-world -v
    ==> System: x86_64
    ==> Backend: podman
    ==> Distro: fedora

    ==> Build Order:
            fedora@=41
            hello-world@=1.0

    ==> wmrxxohy: BUILD fedora@=41 ...
    ==> wmrxxohy: GENERATING SCRIPT ...
            SCRIPT: /tmp/velocity/build/wmrxxohy/script
            FROM docker.io/fedora:41

            RUN dnf -y upgrade

            LABEL velocity.config.system="x86_64" \
                velocity.config.backend="podman" \
                velocity.config.distro="fedora" \
                velocity.image.fedora__41="1ad7926d7e542fa521fe4a2eca54aa73caea82958b1f07adf04728b5762063ac"

    ==> wmrxxohy: BUILDING ...
            #!/usr/bin/env bash
            podman build -f /tmp/velocity/build/wmrxxohy/script -t localhost/wmrxxohy:latest .;
            STEP 1/3: FROM docker.io/fedora:41
            STEP 2/3: RUN dnf -y upgrade
            Fedora rawhide openh264 (From Cisco) - x86_64    59  B/s | 123  B     00:02
            Fedora - Rawhide - Developmental packages for t 3.1 MB/s |  20 MB     00:06
            Dependencies resolved.
            ======================================================================================
             Package                             Arch    Version                    Repo      Size
            ======================================================================================
            Upgrading:
             audit-libs                          x86_64  4.0.1-1.fc41               rawhide  126 k
             authselect                          x86_64  1.5.0-5.fc41               rawhide  146 k
             authselect-libs                     x86_64  1.5.0-5.fc41               rawhide  219 k
             crypto-policies                     noarch  20240320-1.git58e3d95.fc41 rawhide   91 k
             curl                                x86_64  8.6.0-7.fc41               rawhide  301 k
             dnf                                 noarch  4.19.2-1.fc41              rawhide  503 k
             dnf-data                            noarch  4.19.2-1.fc41              rawhide   40 k
             elfutils-default-yama-scope         noarch  0.191-5.fc41               rawhide   13 k
             elfutils-libelf                     x86_64  0.191-5.fc41               rawhide  209 k
             elfutils-libs                       x86_64  0.191-5.fc41               rawhide  258 k
             expat                               x86_64  2.6.2-1.fc41               rawhide  113 k
             fedora-release-common               noarch  41-0.6                     rawhide   21 k
             fedora-release-container            noarch  41-0.6                     rawhide   11 k
             fedora-release-identity-container   noarch  41-0.6                     rawhide   12 k
             glib2                               x86_64  2.80.0-1.fc41              rawhide  3.0 M
             glibc                               x86_64  2.39.9000-10.fc41          rawhide  2.2 M
             glibc-common                        x86_64  2.39.9000-10.fc41          rawhide  393 k
             glibc-minimal-langpack              x86_64  2.39.9000-10.fc41          rawhide  106 k
             gmp                                 x86_64  1:6.3.0-1.fc41             rawhide  317 k
             gnupg2                              x86_64  2.4.5-1.fc41               rawhide  2.7 M
             gnutls                              x86_64  3.8.4-1.fc41               rawhide  1.1 M
             libassuan                           x86_64  2.5.7-1.fc41               rawhide   67 k
             libblkid                            x86_64  2.40-0.12.fc41             rawhide  125 k
             libcurl                             x86_64  8.6.0-7.fc41               rawhide  345 k
             libdnf                              x86_64  0.73.1-1.fc41              rawhide  697 k
             libeconf                            x86_64  0.6.2-1.fc41               rawhide   32 k
             libffi                              x86_64  3.4.6-1.fc41               rawhide   40 k
             libgcc                              x86_64  14.0.1-0.13.fc41           rawhide  123 k
             libgcrypt                           x86_64  1.10.3-4.fc41              rawhide  504 k
             libgomp                             x86_64  14.0.1-0.13.fc41           rawhide  344 k
             libgpg-error                        x86_64  1.48-1.fc41                rawhide  232 k
             libksba                             x86_64  1.6.6-1.fc41               rawhide  159 k
             libmodulemd                         x86_64  2.15.0-9.fc41              rawhide  233 k
             libmount                            x86_64  2.40-0.12.fc41             rawhide  155 k
             libnghttp2                          x86_64  1.60.0-2.fc41              rawhide   76 k
             librepo                             x86_64  1.17.1-1.fc41              rawhide   99 k
             libreport-filesystem                noarch  2.17.15-1.fc41             rawhide   14 k
             libsmartcols                        x86_64  2.40-0.12.fc41             rawhide   84 k
             libssh                              x86_64  0.10.6-6.fc41              rawhide  212 k
             libssh-config                       noarch  0.10.6-6.fc41              rawhide  9.1 k
             libstdc++                           x86_64  14.0.1-0.13.fc41           rawhide  881 k
             libtirpc                            x86_64  1.3.4-1.rc3.fc41           rawhide   92 k
             libunistring                        x86_64  1.1-7.fc41                 rawhide  545 k
             libuuid                             x86_64  2.40-0.12.fc41             rawhide   29 k
             libxml2                             x86_64  2.12.6-1.fc41              rawhide  686 k
             libzstd                             x86_64  1.5.6-1.fc41               rawhide  309 k
             npth                                x86_64  1.7-1.fc41                 rawhide   25 k
             openssl-libs                        x86_64  1:3.2.1-3.fc41             rawhide  2.3 M
             pcre2                               x86_64  10.43-1.fc41               rawhide  242 k
             pcre2-syntax                        noarch  10.43-1.fc41               rawhide  149 k
             python-pip-wheel                    noarch  24.0-2.fc41                rawhide  1.5 M
             python3                             x86_64  3.12.2-3.fc41              rawhide   27 k
             python3-dnf                         noarch  4.19.2-1.fc41              rawhide  594 k
             python3-hawkey                      x86_64  0.73.1-1.fc41              rawhide  105 k
             python3-libdnf                      x86_64  0.73.1-1.fc41              rawhide  847 k
             python3-libs                        x86_64  3.12.2-3.fc41              rawhide  9.1 M
             shadow-utils                        x86_64  2:4.15.1-2.fc41            rawhide  1.3 M
             sqlite-libs                         x86_64  3.45.2-1.fc41              rawhide  706 k
             systemd-libs                        x86_64  255.4-1.fc41               rawhide  708 k
             tzdata                              noarch  2024a-4.fc41               rawhide  716 k
             util-linux-core                     x86_64  2.40-0.12.fc41             rawhide  537 k
             vim-data                            noarch  2:9.1.181-1.fc41           rawhide   23 k
             vim-minimal                         x86_64  2:9.1.181-1.fc41           rawhide  807 k
             xz-libs                             x86_64  1:5.4.6-3.fc41             rawhide  110 k
             yum                                 noarch  4.19.2-1.fc41              rawhide   37 k

            Transaction Summary
            ======================================================================================
            Upgrade  65 Packages

            Total download size: 38 M
            Downloading Packages:
            (1/65): audit-libs-4.0.1-1.fc41.x86_64.rpm      136 kB/s | 126 kB     00:00
            (2/65): authselect-1.5.0-5.fc41.x86_64.rpm      153 kB/s | 146 kB     00:00
            (3/65): crypto-policies-20240320-1.git58e3d95.f 623 kB/s |  91 kB     00:00
            (4/65): authselect-libs-1.5.0-5.fc41.x86_64.rpm 199 kB/s | 219 kB     00:01
            [MIRROR] dnf-4.19.2-1.fc41.noarch.rpm: Status code: 404 for http://mirror.math.princeton.edu/pub/fedora/linux/development/rawhide/Everything/x86_64/os/Packages/d/dnf-4.19.2-1.fc41.noarch.rpm (IP: 128.112.18.21)
            [MIRROR] dnf-data-4.19.2-1.fc41.noarch.rpm: Status code: 404 for http://mirror.math.princeton.edu/pub/fedora/linux/development/rawhide/Everything/x86_64/os/Packages/d/dnf-data-4.19.2-1.fc41.noarch.rpm (IP: 128.112.18.21)
            (5/65): curl-8.6.0-7.fc41.x86_64.rpm            919 kB/s | 301 kB     00:00
            (6/65): elfutils-default-yama-scope-0.191-5.fc4 105 kB/s |  13 kB     00:00
            (7/65): elfutils-libelf-0.191-5.fc41.x86_64.rpm 739 kB/s | 209 kB     00:00
            (8/65): dnf-data-4.19.2-1.fc41.noarch.rpm        51 kB/s |  40 kB     00:00
            (9/65): elfutils-libs-0.191-5.fc41.x86_64.rpm   980 kB/s | 258 kB     00:00
            (10/65): expat-2.6.2-1.fc41.x86_64.rpm          787 kB/s | 113 kB     00:00
            (11/65): fedora-release-common-41-0.6.noarch.rp 165 kB/s |  21 kB     00:00
            (12/65): fedora-release-container-41-0.6.noarch  87 kB/s |  11 kB     00:00
            (13/65): fedora-release-identity-container-41-0  77 kB/s |  12 kB     00:00
            (14/65): dnf-4.19.2-1.fc41.noarch.rpm           402 kB/s | 503 kB     00:01
            (15/65): glib2-2.80.0-1.fc41.x86_64.rpm         4.8 MB/s | 3.0 MB     00:00
            (16/65): glibc-minimal-langpack-2.39.9000-10.fc 783 kB/s | 106 kB     00:00
            (17/65): gmp-6.3.0-1.fc41.x86_64.rpm            1.7 MB/s | 317 kB     00:00
            (18/65): glibc-common-2.39.9000-10.fc41.x86_64. 507 kB/s | 393 kB     00:00
            (19/65): gnupg2-2.4.5-1.fc41.x86_64.rpm         8.2 MB/s | 2.7 MB     00:00
            (20/65): libassuan-2.5.7-1.fc41.x86_64.rpm      458 kB/s |  67 kB     00:00
            (21/65): libblkid-2.40-0.12.fc41.x86_64.rpm     687 kB/s | 125 kB     00:00
            (22/65): glibc-2.39.9000-10.fc41.x86_64.rpm     1.0 MB/s | 2.2 MB     00:02
            [MIRROR] libdnf-0.73.1-1.fc41.x86_64.rpm: Status code: 404 for http://mirror.math.princeton.edu/pub/fedora/linux/development/rawhide/Everything/x86_64/os/Packages/l/libdnf-0.73.1-1.fc41.x86_64.rpm (IP: 128.112.18.21)
            (23/65): gnutls-3.8.4-1.fc41.x86_64.rpm         668 kB/s | 1.1 MB     00:01
            (24/65): libeconf-0.6.2-1.fc41.x86_64.rpm       249 kB/s |  32 kB     00:00
            (25/65): libdnf-0.73.1-1.fc41.x86_64.rpm        1.6 MB/s | 697 kB     00:00
            (26/65): libffi-3.4.6-1.fc41.x86_64.rpm         205 kB/s |  40 kB     00:00
            (27/65): libgcc-14.0.1-0.13.fc41.x86_64.rpm     391 kB/s | 123 kB     00:00
            (28/65): libgomp-14.0.1-0.13.fc41.x86_64.rpm    642 kB/s | 344 kB     00:00
            (29/65): libgcrypt-1.10.3-4.fc41.x86_64.rpm     613 kB/s | 504 kB     00:00
            (30/65): libgpg-error-1.48-1.fc41.x86_64.rpm    579 kB/s | 232 kB     00:00
            (31/65): libksba-1.6.6-1.fc41.x86_64.rpm        580 kB/s | 159 kB     00:00
            (32/65): libcurl-8.6.0-7.fc41.x86_64.rpm        140 kB/s | 345 kB     00:02
            (33/65): libmodulemd-2.15.0-9.fc41.x86_64.rpm   406 kB/s | 233 kB     00:00
            (34/65): libmount-2.40-0.12.fc41.x86_64.rpm     271 kB/s | 155 kB     00:00
            (35/65): libreport-filesystem-2.17.15-1.fc41.no  82 kB/s |  14 kB     00:00
            (36/65): librepo-1.17.1-1.fc41.x86_64.rpm       501 kB/s |  99 kB     00:00
            (37/65): libsmartcols-2.40-0.12.fc41.x86_64.rpm 323 kB/s |  84 kB     00:00
            (38/65): libssh-0.10.6-6.fc41.x86_64.rpm        744 kB/s | 212 kB     00:00
            (39/65): libssh-config-0.10.6-6.fc41.noarch.rpm  74 kB/s | 9.1 kB     00:00
            (40/65): libtirpc-1.3.4-1.rc3.fc41.x86_64.rpm   357 kB/s |  92 kB     00:00
            (41/65): libstdc++-14.0.1-0.13.fc41.x86_64.rpm  837 kB/s | 881 kB     00:01
            (42/65): libnghttp2-1.60.0-2.fc41.x86_64.rpm     35 kB/s |  76 kB     00:02
            (43/65): libuuid-2.40-0.12.fc41.x86_64.rpm      208 kB/s |  29 kB     00:00
            (44/65): libunistring-1.1-7.fc41.x86_64.rpm     534 kB/s | 545 kB     00:01
            (45/65): npth-1.7-1.fc41.x86_64.rpm             187 kB/s |  25 kB     00:00
            (46/65): libzstd-1.5.6-1.fc41.x86_64.rpm        767 kB/s | 309 kB     00:00
            (47/65): pcre2-10.43-1.fc41.x86_64.rpm          611 kB/s | 242 kB     00:00
            (48/65): pcre2-syntax-10.43-1.fc41.noarch.rpm   386 kB/s | 149 kB     00:00
            (49/65): python-pip-wheel-24.0-2.fc41.noarch.rp 640 kB/s | 1.5 MB     00:02
            (50/65): python3-3.12.2-3.fc41.x86_64.rpm       203 kB/s |  27 kB     00:00
            [MIRROR] python3-dnf-4.19.2-1.fc41.noarch.rpm: Status code: 404 for http://mirror.math.princeton.edu/pub/fedora/linux/development/rawhide/Everything/x86_64/os/Packages/p/python3-dnf-4.19.2-1.fc41.noarch.rpm (IP: 128.112.18.21)
            (51/65): libxml2-2.12.6-1.fc41.x86_64.rpm       168 kB/s | 686 kB     00:04
            (52/65): openssl-libs-3.2.1-3.fc41.x86_64.rpm   554 kB/s | 2.3 MB     00:04
            (53/65): python3-hawkey-0.73.1-1.fc41.x86_64.rp 130 kB/s | 105 kB     00:00
            (54/65): python3-dnf-4.19.2-1.fc41.noarch.rpm   425 kB/s | 594 kB     00:01
            (55/65): shadow-utils-4.15.1-2.fc41.x86_64.rpm  3.5 MB/s | 1.3 MB     00:00
            (56/65): sqlite-libs-3.45.2-1.fc41.x86_64.rpm   2.8 MB/s | 706 kB     00:00
            (57/65): python3-libdnf-0.73.1-1.fc41.x86_64.rp 678 kB/s | 847 kB     00:01
            (58/65): systemd-libs-255.4-1.fc41.x86_64.rpm   2.9 MB/s | 708 kB     00:00
            (59/65): util-linux-core-2.40-0.12.fc41.x86_64. 3.0 MB/s | 537 kB     00:00
            (60/65): tzdata-2024a-4.fc41.noarch.rpm         1.5 MB/s | 716 kB     00:00
            (61/65): vim-data-9.1.181-1.fc41.noarch.rpm     125 kB/s |  23 kB     00:00
            (62/65): xz-libs-5.4.6-3.fc41.x86_64.rpm        530 kB/s | 110 kB     00:00
            (63/65): yum-4.19.2-1.fc41.noarch.rpm           215 kB/s |  37 kB     00:00
            (64/65): python3-libs-3.12.2-3.fc41.x86_64.rpm  3.5 MB/s | 9.1 MB     00:02
            (65/65): vim-minimal-9.1.181-1.fc41.x86_64.rpm  218 kB/s | 807 kB     00:03
            --------------------------------------------------------------------------------
            Total                                           2.0 MB/s |  38 MB     00:19
            Running transaction check
            Transaction check succeeded.
            Running transaction test
            Transaction test succeeded.
            Running transaction
              Preparing        :                                                        1/1
              Upgrading        : libgcc-14.0.1-0.13.fc41.x86_64                       1/130
              Running scriptlet: libgcc-14.0.1-0.13.fc41.x86_64                       1/130
              Upgrading        : tzdata-2024a-4.fc41.noarch                           2/130
              Upgrading        : crypto-policies-20240320-1.git58e3d95.fc41.noarc     3/130
              Running scriptlet: crypto-policies-20240320-1.git58e3d95.fc41.noarc     3/130
              Upgrading        : glibc-common-2.39.9000-10.fc41.x86_64                4/130
              Upgrading        : glibc-minimal-langpack-2.39.9000-10.fc41.x86_64      5/130
              Running scriptlet: glibc-2.39.9000-10.fc41.x86_64                       6/130
              Upgrading        : glibc-2.39.9000-10.fc41.x86_64                       6/130
              Running scriptlet: glibc-2.39.9000-10.fc41.x86_64                       6/130
              Upgrading        : libgpg-error-1.48-1.fc41.x86_64                      7/130
              Upgrading        : libuuid-2.40-0.12.fc41.x86_64                        8/130
              Upgrading        : openssl-libs-1:3.2.1-3.fc41.x86_64                   9/130
              Upgrading        : xz-libs-1:5.4.6-3.fc41.x86_64                       10/130
              Upgrading        : libsmartcols-2.40-0.12.fc41.x86_64                  11/130
              Upgrading        : libstdc++-14.0.1-0.13.fc41.x86_64                   12/130
              Upgrading        : libzstd-1.5.6-1.fc41.x86_64                         13/130
              Upgrading        : sqlite-libs-3.45.2-1.fc41.x86_64                    14/130
              Upgrading        : libblkid-2.40-0.12.fc41.x86_64                      15/130
              Upgrading        : libmount-2.40-0.12.fc41.x86_64                      16/130
              Upgrading        : libffi-3.4.6-1.fc41.x86_64                          17/130
              Upgrading        : fedora-release-identity-container-41-0.6.noarch     18/130
              Upgrading        : fedora-release-container-41-0.6.noarch              19/130
              Upgrading        : fedora-release-common-41-0.6.noarch                 20/130
              Upgrading        : elfutils-libelf-0.191-5.fc41.x86_64                 21/130
              Upgrading        : systemd-libs-255.4-1.fc41.x86_64                    22/130
              Upgrading        : libxml2-2.12.6-1.fc41.x86_64                        23/130
              Upgrading        : libassuan-2.5.7-1.fc41.x86_64                       24/130
              Upgrading        : libgcrypt-1.10.3-4.fc41.x86_64                      25/130
              Upgrading        : libksba-1.6.6-1.fc41.x86_64                         26/130
              Upgrading        : audit-libs-4.0.1-1.fc41.x86_64                      27/130
              Upgrading        : authselect-libs-1.5.0-5.fc41.x86_64                 28/130
              Upgrading        : expat-2.6.2-1.fc41.x86_64                           29/130
              Upgrading        : gmp-1:6.3.0-1.fc41.x86_64                           30/130
              Upgrading        : libeconf-0.6.2-1.fc41.x86_64                        31/130
              Upgrading        : libnghttp2-1.60.0-2.fc41.x86_64                     32/130
              Upgrading        : libtirpc-1.3.4-1.rc3.fc41.x86_64                    33/130
              Upgrading        : libunistring-1.1-7.fc41.x86_64                      34/130
              Upgrading        : gnutls-3.8.4-1.fc41.x86_64                          35/130
              Upgrading        : npth-1.7-1.fc41.x86_64                              36/130
              Upgrading        : vim-data-2:9.1.181-1.fc41.noarch                    37/130
              Upgrading        : python-pip-wheel-24.0-2.fc41.noarch                 38/130
              Upgrading        : python3-3.12.2-3.fc41.x86_64                        39/130
              Upgrading        : python3-libs-3.12.2-3.fc41.x86_64                   40/130
              Upgrading        : pcre2-syntax-10.43-1.fc41.noarch                    41/130
              Upgrading        : pcre2-10.43-1.fc41.x86_64                           42/130
              Upgrading        : glib2-2.80.0-1.fc41.x86_64                          43/130
              Upgrading        : libmodulemd-2.15.0-9.fc41.x86_64                    44/130
              Upgrading        : libssh-config-0.10.6-6.fc41.noarch                  45/130
              Upgrading        : libssh-0.10.6-6.fc41.x86_64                         46/130
              Upgrading        : libcurl-8.6.0-7.fc41.x86_64                         47/130
              Upgrading        : librepo-1.17.1-1.fc41.x86_64                        48/130
              Upgrading        : libdnf-0.73.1-1.fc41.x86_64                         49/130
              Upgrading        : python3-libdnf-0.73.1-1.fc41.x86_64                 50/130
              Upgrading        : python3-hawkey-0.73.1-1.fc41.x86_64                 51/130
              Upgrading        : libreport-filesystem-2.17.15-1.fc41.noarch          52/130
              Upgrading        : dnf-data-4.19.2-1.fc41.noarch                       53/130
              Upgrading        : python3-dnf-4.19.2-1.fc41.noarch                    54/130
              Upgrading        : dnf-4.19.2-1.fc41.noarch                            55/130
              Running scriptlet: dnf-4.19.2-1.fc41.noarch                            55/130
              Upgrading        : elfutils-default-yama-scope-0.191-5.fc41.noarch     56/130
              Running scriptlet: elfutils-default-yama-scope-0.191-5.fc41.noarch     56/130
              Upgrading        : elfutils-libs-0.191-5.fc41.x86_64                   57/130
              Upgrading        : yum-4.19.2-1.fc41.noarch                            58/130
              Upgrading        : curl-8.6.0-7.fc41.x86_64                            59/130
              Upgrading        : vim-minimal-2:9.1.181-1.fc41.x86_64                 60/130
              Upgrading        : gnupg2-2.4.5-1.fc41.x86_64                          61/130
              Upgrading        : shadow-utils-2:4.15.1-2.fc41.x86_64                 62/130
              Upgrading        : authselect-1.5.0-5.fc41.x86_64                      63/130
              Upgrading        : util-linux-core-2.40-0.12.fc41.x86_64               64/130
              Upgrading        : libgomp-14.0.1-0.13.fc41.x86_64                     65/130
              Cleanup          : util-linux-core-2.40-0.9.rc1.fc41.x86_64            66/130
              Cleanup          : systemd-libs-255.3-1.fc40.x86_64                    67/130
              Cleanup          : gnupg2-2.4.4-1.fc40.x86_64                          68/130
              Cleanup          : elfutils-libs-0.190-6.fc40.x86_64                   69/130
              Cleanup          : shadow-utils-2:4.14.0-6.fc40.x86_64                 70/130
              Cleanup          : vim-minimal-2:9.1.113-1.fc41.x86_64                 71/130
              Running scriptlet: authselect-1.5.0-3.fc40.x86_64                      72/130
              Cleanup          : authselect-1.5.0-3.fc40.x86_64                      72/130
              Cleanup          : curl-8.6.0-6.fc40.x86_64                            73/130
              Cleanup          : fedora-release-common-41-0.1.noarch                 74/130
              Cleanup          : libgcrypt-1.10.3-3.fc40.x86_64                      75/130
              Cleanup          : elfutils-libelf-0.190-6.fc40.x86_64                 76/130
              Cleanup          : libassuan-2.5.6-4.fc40.x86_64                       77/130
              Cleanup          : authselect-libs-1.5.0-3.fc40.x86_64                 78/130
              Cleanup          : audit-libs-4.0-8.fc40.x86_64                        79/130
              Cleanup          : libksba-1.6.5-3.fc40.x86_64                         80/130
              Cleanup          : libgpg-error-1.47-4.fc40.x86_64                     81/130
              Cleanup          : libeconf-0.5.2-3.fc40.x86_64                        82/130
              Cleanup          : libgomp-14.0.1-0.6.fc40.x86_64                      83/130
              Cleanup          : fedora-release-container-41-0.1.noarch              84/130
              Cleanup          : yum-4.19.0-1.fc40.noarch                            85/130
              Cleanup          : libzstd-1.5.5-5.fc40.x86_64                         86/130
              Cleanup          : npth-1.6-18.fc40.x86_64                             87/130
              Running scriptlet: dnf-4.19.0-1.fc40.noarch                            88/130
              Cleanup          : dnf-4.19.0-1.fc40.noarch                            88/130
              Running scriptlet: dnf-4.19.0-1.fc40.noarch                            88/130
              Cleanup          : python3-dnf-4.19.0-1.fc40.noarch                    89/130
              Cleanup          : dnf-data-4.19.0-1.fc40.noarch                       90/130
              Cleanup          : libreport-filesystem-2.17.14-1.fc40.noarch          91/130
              Cleanup          : fedora-release-identity-container-41-0.1.noarch     92/130
              Cleanup          : vim-data-2:9.1.113-1.fc41.noarch                    93/130
              Cleanup          : elfutils-default-yama-scope-0.190-6.fc40.noarch     94/130
              Cleanup          : python3-hawkey-0.73.0-1.fc40.x86_64                 95/130
              Cleanup          : python3-libdnf-0.73.0-1.fc40.x86_64                 96/130
              Cleanup          : python3-libs-3.12.2-1.fc40.x86_64                   97/130
              Cleanup          : python3-3.12.2-1.fc40.x86_64                        98/130
              Cleanup          : libdnf-0.73.0-1.fc40.x86_64                         99/130
              Cleanup          : python-pip-wheel-23.3.2-1.fc40.noarch              100/130
              Cleanup          : libstdc++-14.0.1-0.6.fc40.x86_64                   101/130
              Cleanup          : librepo-1.17.0-3.fc40.x86_64                       102/130
              Cleanup          : libcurl-8.6.0-6.fc40.x86_64                        103/130
              Cleanup          : libxml2-2.12.5-1.fc40.x86_64                       104/130
              Cleanup          : libssh-0.10.6-4.fc40.x86_64                        105/130
              Cleanup          : openssl-libs-1:3.2.1-2.fc40.x86_64                 106/130
              Cleanup          : sqlite-libs-3.45.1-2.fc40.x86_64                   107/130
              Cleanup          : libtirpc-1.3.4-1.rc2.fc40.2.x86_64                 108/130
              Cleanup          : libmodulemd-2.15.0-8.fc40.x86_64                   109/130
              Cleanup          : glib2-2.79.1-1.fc40.x86_64                         110/130
              Cleanup          : libmount-2.40-0.9.rc1.fc41.x86_64                  111/130
              Cleanup          : gnutls-3.8.3-2.fc40.x86_64                         112/130
              Cleanup          : libblkid-2.40-0.9.rc1.fc41.x86_64                  113/130
              Cleanup          : libuuid-2.40-0.9.rc1.fc41.x86_64                   114/130
              Cleanup          : xz-libs-5.4.6-1.fc40.x86_64                        115/130
              Cleanup          : libsmartcols-2.40-0.9.rc1.fc41.x86_64              116/130
              Cleanup          : expat-2.6.0-1.fc41.x86_64                          117/130
              Cleanup          : gmp-1:6.2.1-8.fc40.x86_64                          118/130
              Cleanup          : libunistring-1.1-7.fc40.x86_64                     119/130
              Cleanup          : libffi-3.4.4-7.fc40.x86_64                         120/130
              Cleanup          : pcre2-10.42-2.fc40.2.x86_64                        121/130
              Cleanup          : libnghttp2-1.59.0-2.fc40.x86_64                    122/130
              Cleanup          : pcre2-syntax-10.42-2.fc40.2.noarch                 123/130
              Cleanup          : crypto-policies-20240201-1.git9f501f3.fc40.noarc   124/130
              Cleanup          : libssh-config-0.10.6-4.fc40.noarch                 125/130
              Cleanup          : glibc-2.39.9000-1.fc41.x86_64                      126/130
              Cleanup          : glibc-minimal-langpack-2.39.9000-1.fc41.x86_64     127/130
              Cleanup          : glibc-common-2.39.9000-1.fc41.x86_64               128/130
              Cleanup          : tzdata-2024a-2.fc40.noarch                         129/130
              Cleanup          : libgcc-14.0.1-0.6.fc40.x86_64                      130/130
              Running scriptlet: libgcc-14.0.1-0.6.fc40.x86_64                      130/130
              Running scriptlet: authselect-libs-1.5.0-5.fc41.x86_64                130/130
              Running scriptlet: libgcc-14.0.1-0.6.fc40.x86_64                      130/130

            Upgraded:
              audit-libs-4.0.1-1.fc41.x86_64
              authselect-1.5.0-5.fc41.x86_64
              authselect-libs-1.5.0-5.fc41.x86_64
              crypto-policies-20240320-1.git58e3d95.fc41.noarch
              curl-8.6.0-7.fc41.x86_64
              dnf-4.19.2-1.fc41.noarch
              dnf-data-4.19.2-1.fc41.noarch
              elfutils-default-yama-scope-0.191-5.fc41.noarch
              elfutils-libelf-0.191-5.fc41.x86_64
              elfutils-libs-0.191-5.fc41.x86_64
              expat-2.6.2-1.fc41.x86_64
              fedora-release-common-41-0.6.noarch
              fedora-release-container-41-0.6.noarch
              fedora-release-identity-container-41-0.6.noarch
              glib2-2.80.0-1.fc41.x86_64
              glibc-2.39.9000-10.fc41.x86_64
              glibc-common-2.39.9000-10.fc41.x86_64
              glibc-minimal-langpack-2.39.9000-10.fc41.x86_64
              gmp-1:6.3.0-1.fc41.x86_64
              gnupg2-2.4.5-1.fc41.x86_64
              gnutls-3.8.4-1.fc41.x86_64
              libassuan-2.5.7-1.fc41.x86_64
              libblkid-2.40-0.12.fc41.x86_64
              libcurl-8.6.0-7.fc41.x86_64
              libdnf-0.73.1-1.fc41.x86_64
              libeconf-0.6.2-1.fc41.x86_64
              libffi-3.4.6-1.fc41.x86_64
              libgcc-14.0.1-0.13.fc41.x86_64
              libgcrypt-1.10.3-4.fc41.x86_64
              libgomp-14.0.1-0.13.fc41.x86_64
              libgpg-error-1.48-1.fc41.x86_64
              libksba-1.6.6-1.fc41.x86_64
              libmodulemd-2.15.0-9.fc41.x86_64
              libmount-2.40-0.12.fc41.x86_64
              libnghttp2-1.60.0-2.fc41.x86_64
              librepo-1.17.1-1.fc41.x86_64
              libreport-filesystem-2.17.15-1.fc41.noarch
              libsmartcols-2.40-0.12.fc41.x86_64
              libssh-0.10.6-6.fc41.x86_64
              libssh-config-0.10.6-6.fc41.noarch
              libstdc++-14.0.1-0.13.fc41.x86_64
              libtirpc-1.3.4-1.rc3.fc41.x86_64
              libunistring-1.1-7.fc41.x86_64
              libuuid-2.40-0.12.fc41.x86_64
              libxml2-2.12.6-1.fc41.x86_64
              libzstd-1.5.6-1.fc41.x86_64
              npth-1.7-1.fc41.x86_64
              openssl-libs-1:3.2.1-3.fc41.x86_64
              pcre2-10.43-1.fc41.x86_64
              pcre2-syntax-10.43-1.fc41.noarch
              python-pip-wheel-24.0-2.fc41.noarch
              python3-3.12.2-3.fc41.x86_64
              python3-dnf-4.19.2-1.fc41.noarch
              python3-hawkey-0.73.1-1.fc41.x86_64
              python3-libdnf-0.73.1-1.fc41.x86_64
              python3-libs-3.12.2-3.fc41.x86_64
              shadow-utils-2:4.15.1-2.fc41.x86_64
              sqlite-libs-3.45.2-1.fc41.x86_64
              systemd-libs-255.4-1.fc41.x86_64
              tzdata-2024a-4.fc41.noarch
              util-linux-core-2.40-0.12.fc41.x86_64
              vim-data-2:9.1.181-1.fc41.noarch
              vim-minimal-2:9.1.181-1.fc41.x86_64
              xz-libs-1:5.4.6-3.fc41.x86_64
              yum-4.19.2-1.fc41.noarch

            Complete!
            --> 43089713ea9
            STEP 3/3: LABEL velocity.config.system="x86_64"     velocity.config.backend="podman"     velocity.config.distro="fedora"     velocity.image.fedora__41="1ad7926d7e542fa521fe4a2eca54aa73caea82958b1f07adf04728b5762063ac"
            COMMIT localhost/wmrxxohy:latest
            --> 49321c240b5
            Successfully tagged localhost/wmrxxohy:latest
            49321c240b522a0d66cd30b62addc99e87b5861e2e6c27f6d0136968c73be5aa
    ==> wmrxxohy: IMAGE localhost/wmrxxohy:latest (fedora@=41) BUILT [0:01:02]

    ==> bdvdbcor: BUILD hello-world@=1.0 ...
    ==> bdvdbcor: COPYING FILES ...
            FILE: /home/xjv/tmp/hello-world/1.0/x86_64/hello_world.py -> /tmp/velocity/build/bdvdbcor/hello_world.py
    ==> bdvdbcor: GENERATING SCRIPT ...
            SCRIPT: /tmp/velocity/build/bdvdbcor/script
            FROM localhost/wmrxxohy:latest

            COPY hello_world.py /hello_world.py

            LABEL velocity.image.hello-world__1.0="1b080f458c34ae2759d1eb3e8464d3d508e3bcb981a476f70709b0f20b6218bb"

            ENTRYPOINT ['/hello_world.py']

    ==> bdvdbcor: BUILDING ...
            #!/usr/bin/env bash
            podman build -f /tmp/velocity/build/bdvdbcor/script -t localhost/hello-world__1.0__x86_64__fedora:latest .;
            STEP 1/4: FROM localhost/wmrxxohy:latest
            STEP 2/4: COPY hello_world.py /hello_world.py
            --> fa1896e8689
            STEP 3/4: LABEL velocity.image.hello-world__1.0="1b080f458c34ae2759d1eb3e8464d3d508e3bcb981a476f70709b0f20b6218bb"
            --> d58637575df
            STEP 4/4: ENTRYPOINT ['/hello_world.py']
            COMMIT localhost/hello-world__1.0__x86_64__fedora:latest
            --> 21211d9de40
            Successfully tagged localhost/hello-world__1.0__x86_64__fedora:latest
            21211d9de40aa6c0cb6b625e6f4fed265c88f9a4be09c4edcd93a78360580ecf
    ==> bdvdbcor: IMAGE localhost/hello-world__1.0__x86_64__fedora:latest (hello-world@=1.0) BUILT [0:00:03]

Our hello-world image has been built!

.. code-block:: bash
    :emphasize-lines: 3

    user@hostname:~$ podman image ls
    REPOSITORY                                 TAG         IMAGE ID      CREATED        SIZE
    localhost/hello-world__1.0__x86_64__fedora latest      db958bad4f40  4 minutes ago  337 MB
    docker.io/library/fedora                   41          54d1373b70a2  5 weeks ago    180 MB

