***********
VTMP Format
***********

VTMP files are used by Velocity to generate the appropriate script for a particular backend.
The goal of the VTMP files are to provide a unified API for
container images across multiple backends but they are not feature exhaustive.
VTMP files are split up into a number of sections.

.. code-block:: text
    :caption: Example VTMP

    >>> this is a comment
    @from
        >>> can only take one of these examples
        docker.io/ubuntu:20.04
        /example.sif    >>> only works for apptainer backend
        {{ __base__ }}  >>> build on the previous image

    @pre
        >>> anything here is taken literally
        >>> optionally denote the start of a line with | (helpful for white space)
        echo 'Without tab'
        |    echo 'With tab'

    @copy
        >>> list files to copy, format <src> <dest>
        /external/file /internal/file

    @run
        >>> list of commands to run in container
        echo 'Hello world'
        ?? distro=podman |> echo 'podman' ??    >>> conditional
        ?? distro=apptainer |> echo 'apptainer' ??
        echo {{ template_variable }}
        echo @@ example_arg @@  >>> define an argument
        !envar TEST_VAR I want this here and in the @env section    >>> the !envar directive

    @env
        >>> set env variables
        PATH /something:$PATH

    @label
        >>> set container labels
        IMAGE_NAME {{ __name__ }}

    @entry
        >>> set  ENTRYPOINT or %runscript
        >>> only one line allowed

        /bin/bash

    @post >>> same as pre but placed after everything else

.. _variables:

Variables
#########
The first thing that is done to a VTMP file is the substitution of any variables found in the script. Variables are indicated
by ``{{ <variable> }}``. In Velocity variables can be defined by the user in the `specs.yaml` file, but Velocity also
provides a set of build time variables.

.. code-block:: text

    __backend__
    __distro__
    __base__        >>> previous image to build on
    __name__        >>> current image name e.g. cuda
    __system__
    __version__     >>> image "version" e.g. 11.7.1
    __version_major__
    __version_minor__
    __version_patch__
    __version_suffix__
    __timestamp__
    >>> the versions of all images in a build are also available in the following format
    __<name>__version__
    __<name>__version_major__
    __<name>__version_minor__
    __<name>__version_patch__
    __<name>__version_suffix__

Arguments
#########
You can also pass in arguments at build time using the form ``@@ <name> @@``, but don't forget to add the
argument in ``specs.yaml`` so that is gets added to the build command or the build will fail.

Conditionals
############
If there is a line in a template that you only want under certain conditions use ``?? <condition> |> <text> ??``.
The whole conditional will be replaced with the <text> section if the condition is true; otherwise, it will substitute
an empty string. The conditionals can include the following components, ``system=<value>``, ``backend=<value>``,
``distro=<value>`` and a dependency in the form ``^<value>``.

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

@copy
-----
The `@copy` section takes a list of files/dir to be copied in the <src> <dest> format.

@run
----
The `@run` section takes a list of commands to be run in the container. These commands should be written as if they all
occur one after the other in the same shell. One added feature to the @run section is the ``!envar`` directive. This
directive will add the following variable definition to the @env section as well as to the current @run section. Use
the format ``!envar <name> <value>``.

@env
----
The `@env` section sets environment variables. These variables will only be available when the container is run or in
the next build so if there is a variable that is needed in the run section use the ``!envar`` directive in the @run section.

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
