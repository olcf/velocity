*************************
Creating Your First Image
*************************

Base Image
##########
Let's start with a simple base image. This image will pull an opensuse docker image and update the packages. To setup
your environment do something like this.


.. code-block:: bash
    :caption: Setup

    TUTORIAL_DIR=/tmp/velocity
    mkdir -p $TUTORIAL_DIR/images
    export VELOCITY_IMAGE_PATH=$TUTORIAL_DIR/images
    export VELOCITY_BUILD_DIR=$TUTORIAL_DIR/build
    export VELOCITY_DISTRO=opensuse
    # all subsequent commands in this tutorial were run from the TUTORIAL_DIR, but they don't have to be

.. note::

    You will also need Apptainer installed on your system.

Next create a directory in the ``images`` directory called ``opensuse``. In this directory create a file called
``specs.yaml`` and a directory called ``templates`` with
a file named ``default.vtmp``. Your image directory and files should now look like this.

.. code-block:: bash
    :caption: /tmp/velocity/images

    opensuse
    ├── specs.yaml
    └── templates
        └── default.vtmp


.. code-block:: yaml
    :caption: opensuse/specs.yaml

    versions:
      - spec: 15.4
        when: distro=opensuse



.. code-block:: text
    :caption: opensuse/templates/default.vtmp

    @from
        docker.io/opensuse/leap:{{ __version__ }}

    @run
        zypper --non-interactive refresh
        zypper --non-interactive update
        zypper clean --all

Now if you run `velocity avail` you should get the following.

.. code-block:: bash

    $ velocity avail
    ==> opensuse
        15.4

Now build the image.

.. code-block:: bash

    $ velocity build opensuse
    ==> Build Order:
        opensuse@15.4-a1913cd

    ==> a1913cd: BUILD opensuse@15.4 ...
    ==> a1913cd: GENERATING SCRIPT ...
    ==> a1913cd: BUILDING ...
    ==> a1913cd: IMAGE /tmp/velocity/build/opensuse-15.4-a1913cd/a1913cd.sif (opensuse@15.4) BUILT [0:01:03]

    ==> BUILT: /tmp/velocity/opensuse-15.4__frontier-opensuse.sif

If you wish to see more output you can add the ``-v`` flag to the build command.

Adding Different Versions
#########################
So now we have a base opensuse image. That's great but before we move on let's make some different versions of the image
so that we have more options for building later. Edit the opensuse ``specs.yaml`` and add some versions.

.. code-block:: yaml
    :caption: spec.yaml

    versions:
      - spec:
          - 15.4
          - 15.5
          - 15.6
        when: distro=opensuse

.. code-block:: bash

    $ velocity avail
    ==> opensuse
        15.4
        15.5
        15.6

Specifying Version
##################
When building an image Velocity will default to the latest image. To specify a version use ``<image>@<version>`` e.g.
``opensuse@15.6``. Versions take the form ``<major>.<minor>.<patch>-<suffix>``. You can also specify greater than, less
than, and in-between via ``<image>@<version>:``, ``<image>@:<version>`` and ``<image>@<version>:<version>`` respectively.

Hello World!
############
Now let's get a little more complicated. Let's create an image that runs a python script which prints ``Hello, World!``. You
can give it whatever version you want:

.. code-block:: bash
    :caption: /tmp/velocity/images

    opensuse
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
    :caption: hello-world/files/hello_world.py

    #!/usr/bin/env python3

    print("Hello, World!")

.. code-block:: yaml
    :caption: hello-world/specs.yaml

    versions:
      - spec: 1.0
    dependencies:
      - spec: opensuse
        when: distro=opensuse
    files:
      - name: hello_world.py


.. code-block:: text
    :caption: hello-world/templates/default.vtmp

    @from
        {{ __base__ }}

    @copy
        hello_world.py /hello_world

    @run
        zypper --non-interactive install python3
        chmod +x /hello_world

    @entry
        /hello_world


.. code-block:: bash

    $ velocity avail
    ==> hello-world
        1.0
    ==> opensuse
        15.4
        15.5
        15.6

.. code-block:: bash

    $ velocity build hello-world -v
    ==> Build Order:
        opensuse@15.6-59edd44
        hello-world@1.0-a167014

    ==> 59edd44: BUILD opensuse@15.6 ...
    ==> 59edd44: GENERATING SCRIPT ...
    ==> 59edd44: BUILDING ...
    ==> 59edd44: IMAGE /tmp/velocity/build/opensuse-15.6-59edd44/59edd44.sif (opensuse@15.6) BUILT [0:00:36]

    ==> a167014: BUILD hello-world@1.0 ...
    ==> a167014: COPYING FILES ...
    ==> a167014: GENERATING SCRIPT ...
    ==> a167014: BUILDING ...
    ==> a167014: IMAGE /tmp/velocity/build/hello-world-1.0-a167014/a167014.sif (hello-world@1.0) BUILT [0:00:27]

    ==> BUILT: /tmp/velocity/hello-world-1.0_opensuse-15.6__frontier-opensuse.sif

Our hello-world image has been built!

.. code-block:: bash
    :emphasize-lines: 6

    $ ls -al
    total 207020
    drwxr-xr-x     4 xxx  xxx        120 Sep 25 10:44 .
    drwxrwxrwt 33550 root root    761680 Sep 25 10:45 ..
    drwxr-xr-x     5 xxx  xxx        100 Sep 25 10:44 build
    -rwxr-xr-x     1 xxx  xxx  167243776 Sep 25 10:44 hello-world-1.0_opensuse-15.6__frontier-opensuse.sif
    drwxr-xr-x     4 xxx  xxx         80 Sep 25 10:42 images
    -rwxr-xr-x     1 xxx  xxx   44744704 Sep 25 10:39 opensuse-15.4__frontier-opensuse.sif

Now you can run the image!

.. code-block:: bash

    $ apptainer run hello-world-*-opensuse.sif  # replace * with the specifics of your build
    Hello, World!

OLCF Images
###########

Let's extend what we have done so far and explore some more features of Velocity using a base set of image definitions
provided at https://github.com/olcf/velocity-images. Clone the repository and run:

.. note::

    The ``opensuse`` image in the git repository will override the ``opensuse`` image you just created because velocity
    selects conflicting images by their order in :ref:`velocity_image_path`.

.. code-block:: bash

    export VELOCITY_IMAGE_PATH=<path to the cloned repo>:$VELOCITY_IMAGE_PATH

Let's check what images are available now.

.. note::

    Due to updates to https://github.com/olcf/velocity-images the output shown below may be different for you.

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

If you were to look at the contents of https://github.com/olcf/velocity-images you would notice that there is a
folder in it defining an ``ubuntu`` image. Why does that image not show up? At the beginning of this tutorial
we set ``export VELOCITY_DISTRO=opensuse``. In the ``ubuntu`` ``specs.yaml`` file you would see:

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

    This is important because it keeps us from trying to build a container with two distros, but it may catch you off guard
    by hiding images you thought you had defined.

Now let try building our ``hello-world`` image on an ``ubuntu`` base. In the current state the build will fail but let's
run it anyway and trouble shoot it.

.. code-block:: bash

    $ velocity -d ubuntu build hello-world
    ==> Build Order:
        hello-world@1.0-7562a9e

    ==> 7562a9e: BUILD hello-world@1.0 ...
    ==> 7562a9e: COPYING FILES ...
    ==> 7562a9e: GENERATING SCRIPT ...
    Traceback (most recent call last):
      File "/ccs/home/xxx/.conda/envs/main_x86_64/lib/python3.11/site-packages/velocity/_backends.py", line 131, in generate_script
        if len(sections["@from"]) != 1:
               ~~~~~~~~^^^^^^^^^
    KeyError: '@from'

    During handling of the above exception, another exception occurred:

    Traceback (most recent call last):
      File "<frozen runpy>", line 198, in _run_module_as_main
      File "<frozen runpy>", line 88, in _run_code
      File "/ccs/home/xxx/.conda/envs/main_x86_64/lib/python3.11/site-packages/velocity/__main__.py", line 111, in <module>
        builder.build()
      File "/ccs/home/xxx/.conda/envs/main_x86_64/lib/python3.11/site-packages/velocity/_build.py", line 128, in build
        self._build_image(u, last, name)
      File "/ccs/home/xxx/.conda/envs/main_x86_64/lib/python3.11/site-packages/velocity/_build.py", line 223, in _build_image
        script = self.backend_engine.generate_script(unit, script_variables)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/ccs/home/xxx/.conda/envs/main_x86_64/lib/python3.11/site-packages/velocity/_backends.py", line 140, in generate_script
        raise TemplateSyntaxError("You must have an @from section in your template!")
    velocity._exceptions.TemplateSyntaxError: You must have an @from section in your template!

We see that an error occurred in the ``GENERATING SCRIPT`` section. But if we look under ``==> Build Order`` at the top
we will notice the real cause. The ``ubuntu`` image is not being built. This causes the error in script generation
because in our ``default.vtmp`` for ``hello-world`` we have ``{{ __base__ }}`` defined in our ``@from`` section which
looks for a previous image to build on. Let's edit our ``hello-world`` ``specs.yaml``. It should look like this.

.. code-block:: yaml
    :caption: hello-world/specs.yaml
    :emphasize-lines: 6-7

    versions:
      - spec: 1.0
    dependencies:
      - spec: opensuse
        when: distro=opensuse
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
        ubuntu@24.04-043b176
        hello-world@1.0-9dcbb36

    ==> 043b176: BUILD ubuntu@24.04 ...
    ==> 043b176: GENERATING SCRIPT ...
    ==> 043b176: BUILDING ...
    ==> 043b176: IMAGE /tmp/velocity/build/ubuntu-24.04-043b176/043b176.sif (ubuntu@24.04) BUILT [0:00:11]

    ==> 9dcbb36: BUILD hello-world@1.0 ...
    ==> 9dcbb36: COPYING FILES ...
    ==> 9dcbb36: GENERATING SCRIPT ...
    ==> 9dcbb36: BUILDING ...
        INFO:    User not listed in /etc/subuid, trying root-mapped namespace
        INFO:    The %post section will be run under fakeroot
        INFO:    Starting build...
        INFO:    Verifying bootstrap image /tmp/velocity/build/ubuntu-24.04-043b176/043b176.sif
        INFO:    Copying hello_world.py to /hello_world
        INFO:    Running post scriptlet
        + zypper --non-interactive install python3
        /.post.script: 1: zypper: not found
        FATAL:   While performing build: while running engine: exit status 127

Velocity prints out the error from the build ``zypper: not found``. Lets look back at the :doc:`vtmp </reference/vtmp>`
script we wrote for ``hello-world``. Under the ``@run`` section we had:

.. code-block:: text

    @run
        zypper --non-interactive install python3
        chmod +x /hello_world

We used zypper to install python because it is not installed in the opensuse docker image by default. We need to edit this
script to support ``ubuntu``. Change the ``@run`` section to:

.. code-block:: text

    @run
        ?? distro=opensuse |> zypper --non-interactive install python3 ??
        ?? distro=ubuntu |> apt -y install python3 ??
        chmod +x /hello_world

Now we can test by doing a verbose dry-run for ``opensuse`` and ``ubuntu``.

.. code-block:: bash
    :emphasize-lines: 33
    :caption: opensuse

    $ velocity build hello-world -dv
    ==> Build Order:
        opensuse@15.6-90ac66d
        hello-world@1.0-5fa2515

    ==> 90ac66d: BUILD opensuse@15.6 --DRY-RUN ...
    ==> 90ac66d: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/opensuse-15.6-90ac66d/script
        Bootstrap: docker
        From: docker.io/opensuse/leap:15.6

        %post
        zypper --non-interactive refresh
        zypper --non-interactive update
        zypper clean --all
    ==> 90ac66d: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/velocity/build/opensuse-15.6-90ac66d/90ac66d.sif /tmp/velocity/build/opensuse-15.6-90ac66d/script;
    ==> 90ac66d: IMAGE /tmp/velocity/build/opensuse-15.6-90ac66d/90ac66d.sif (opensuse@15.6) BUILT [0:00:00]

    ==> 5fa2515: BUILD hello-world@1.0 --DRY-RUN ...
    ==> 5fa2515: COPYING FILES ...
        FILE: /tmp/velocity/images/hello-world/files/hello_world.py -> /tmp/velocity/build/hello-world-1.0-5fa2515/hello_world.py
    ==> 5fa2515: GENERATING SCRIPT ...
        SCRIPT: /tmp/velocity/build/hello-world-1.0-5fa2515/script
        Bootstrap: localimage
        From: /tmp/velocity/build/opensuse-15.6-90ac66d/90ac66d.sif

        %files
        hello_world.py /hello_world

        %post
        zypper --non-interactive install python3
        chmod +x /hello_world

        %runscript
        /hello_world
    ==> 5fa2515: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/velocity/build/hello-world-1.0-5fa2515/5fa2515.sif /tmp/velocity/build/hello-world-1.0-5fa2515/script;
    ==> 5fa2515: IMAGE /tmp/velocity/build/hello-world-1.0-5fa2515/5fa2515.sif (hello-world@1.0) BUILT [0:00:00]

    ==> BUILT: /tmp/velocity/hello-world-1.0_opensuse-15.6__frontier-opensuse.sif

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
on any version of ``opensuse`` or ``ubuntu``, but instead of having a separate script for each combination of version and distro we have
just three. One for ``opensuse``, one for ``ubuntu`` and one for ``hello-world``. This may not seem like a big win for an
example like ``hello-world``; however, this becomes a big win for images like the ``gcc`` image in
https://github.com/olcf/velocity-images. If you look at the ``gcc`` image ``default.vtmp`` script you will see that it can
build practically any version of gcc on ``ubuntu``, ``opensuse`` and ``rockylinux``.

The last thing we need to look at for this tutorial is Velocity's support for multiple container backends. Let's look at
a dry-run example of the ``opensuse`` image that we have been building with ``apptainer``.

.. code-block::
    :emphasize-lines: 8-14,17,20

    $ velocity build opensuse -vd
    ==> Build Order:
        opensuse@15.6-01205e8

    ==> 01205e8: BUILD opensuse@15.6 --DRY-RUN ...
    ==> 01205e8: GENERATING SCRIPT ...
        SCRIPT: /tmp/xxx/velocity/opensuse-15.6-01205e8/script
        Bootstrap: docker
        From: docker.io/opensuse/leap:15.6

        %post
        zypper --non-interactive refresh
        zypper --non-interactive update
        zypper clean --all
    ==> 01205e8: BUILDING ...
        #!/usr/bin/env bash
        apptainer build --disable-cache /tmp/xxx/velocity/opensuse-15.6-01205e8/01205e8.sif /tmp/xxx/velocity/opensuse-15.6-01205e8/script;
    ==> 01205e8: IMAGE /tmp/xxx/velocity/opensuse-15.6-01205e8/01205e8.sif (opensuse@15.6) BUILT [0:00:00]

    ==> BUILT: /tmp/opensuse-15.6__x86_64-opensuse.sif

Next let's look at the same thing but with the backend set to ``podman``.

.. warning::

    If Podman is not installed this will fail. Conversely, if you are on a system that does not have Apptainer
    installed, ``build`` commands using Apptainer will fail.

.. code-block::
    :emphasize-lines: 8-12,15,18

    $ velocity -b podman build opensuse -vd
    ==> Build Order:
        opensuse@15.6-dd91fe3

    ==> dd91fe3: BUILD opensuse@15.6 --DRY-RUN ...
    ==> dd91fe3: GENERATING SCRIPT ...
        SCRIPT: /tmp/xxx/velocity/opensuse-15.6-dd91fe3/script
        FROM docker.io/opensuse/leap:15.6

        RUN zypper --non-interactive refresh && \
            zypper --non-interactive update && \
            zypper clean --all
    ==> dd91fe3: BUILDING ...
        #!/usr/bin/env bash
        podman build -f /tmp/xxx/velocity/opensuse-15.6-dd91fe3/script -t localhost/dd91fe3:latest .;
    ==> dd91fe3: IMAGE localhost/dd91fe3:latest (opensuse@15.6) BUILT [0:00:00]

    ==> BUILT: localhost/opensuse-15.6__x86_64-opensuse:latest

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
    ├── hello-world-1.0-0ff1ff7
    │ ├── 0ff1ff7.sif
    │ ├── build
    │ ├── hello_world.py
    │ ├── log
    │ └── script
    ...
