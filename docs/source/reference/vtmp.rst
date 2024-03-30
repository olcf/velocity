***********
VTMP Format
***********

VTMP files are used by Velocity to generate the appropriate script for a particular backend.
While certain features are supported across all backends, others are exclusive to one backend and many are interpreted
quite differently between the different backends. The goal of the VTMP files are to provide a unified API for
container images across multiple backends but they are not feature exhaustive.
VTMP files are split up into a number of sections.

.. code-block:: text
    :caption: Example VTMP

    @from
        # can only take one of these
        docker.io/ubuntu:20.04
        /example.sif # only works for apptainer backend
        %(__base__)

    @pre # same as post but placed right after @from
        # anything here is taken literally
        # denote the start of a line with |
        |echo 'Without tab'
        |    echo 'With tab'

    @arg
        # define arg names
        example_arg # reference this argument throughout the script with @(<arg>)

    @copy
        # list files to copy, format <src> <dest>
        /external/file /internal/file

    @run
        # list of commands to run in container
        echo 'Hello world'
        ?podman echo 'podman'
        ?apptainer echo 'apptainer'
        echo %(template_variable)
        echo @(example_arg) # see @arg

    @env
        # set env variables
        PATH /something:$PATH

    @label
        # set container labels
        velocity.image.%(__name__)__%(__tag__) %(__hash__)


    @entry
        # set entrypoint or %runscript
        # only one line allowed
        /bin/bash

    @post # same as pre but placed after everything else

.. _variables:

Variables
#########
The first thing that is done to a VTMP file is the substitution of any variables found in the script. Variables are indicated
by `%(<variable>)`. In Velocity variables can be defined by the user in the `specifications.yaml` file, but Velocity also
provides a set of build time variables.

.. code-block:: text

    __backend__
    __distro__
    __hash__        # template hash
    __base__        # previous image to build on
    __name__        # current image name e.g. cuda
    __system__
    __tag__         # image "version" e.g. 11.7.1
    __timestamp__

Sections
########

@from
-----
The `@from` section is used to specify the base image to build on top of. Both Podman and Apptainer support pulling
from docker registries. Apptainer also supports building from a sif file. The `@from` section can only have one line in it.

.. _pre_section:

@pre
----
This section and the related `@post` section enable a user to insert a literal section of text into the generated script.
One added feature in this section is the ability to denote the beginning of a line with the | character. This
allows you to add white space to the beginning of a line. The only difference between the `@pre` and `@post` section
are where they are placed in the script the `@pre` section is placed at the beginning of the script
right after the `@from` section.

@arg
----
The `@arg` section specifies build time arguments that are passed to the backend. If these arguments are not passed to
the backend at build time it will fail. Once an arg has been defined in the `@arg` section it can be referenced
throughout the script with `@(<argument>)`.

@copy
-----
The `@copy` section takes a list of files/dir to be copied in the <src> <dest> format.

@run
----
The `@run` section takes a list of commands to be run in the container. These commands should be written as if they all
occur one after the other in the same shell.

@env
----
The `@env` section sets environment variables. These variables will only be available when the container is run or in
the next build so if there is a variable that is needed in the run section you must declare it there as well.

@label
------
A list of labels for the container. The key is separated from the value by the first space. Everything to the right of
the first space is included in the value.

@entry
------
This `@entry` section is converted to `ENTRYPOINT` for podman and `%runscript` for apptainer. You can only have one line
in the `@entry` section.

@post
-----
See :ref:`@pre <pre_section>`. The `@post` section is placed at the end of the script after all other sections.

Conditionals
############
It is handy somtimes to be able to limit certain commands to a backend(s) this can be done by placing a `?<backend>`
at the beginning of the line in question.
