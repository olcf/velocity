*******************
Specifications.yaml
*******************

Basic Layout
############
The `specifications.yaml` file defines image availability, dependencies and a number of other available
options for an image. Velocity doesn't care about any extraneous data you may have in it. All that Velocity looks
for is a base level section called `build_specifications`. Any other sections that you may add for your own purposes
are ignored by Velocity. Under `build_specifications` there should be a tree defining under what conditions the image
can be built in the order `system` > `backend` > `distro`. For example if I am creating an `centos` based image for use on
frontier which only has Apptainer on it then I should have the following structure in my `specifications.yaml` file.

.. code-block:: yaml

    build_specifications:
      frontier:
        apptainer:
          ubuntu:
            # config options

If I wanted it to be available on summit as well which has Apptainer and Podman I would add the following.

.. code-block:: yaml

    build_specifications:
      frontier:
        apptainer:
          centos:
            # config options
      summit:
        apptainer:
          centos:
            # config options
        podman:
          centos:
            # config options

While `system` and `backend` are fairly self explanatory the `distro` is a little more obscure. Velocity does not do
any checks to make sure that the image being built is actually of the right distro. All that the distro tells Velocity to do is
look in the `templates` folder of an image for a template called `<distro>.vtmp` (e.g. centos.vtmp). If a template with
the right name cannot be found Velocity will error.

.. code-block:: bash
    :caption: image structure

    .
    └── <image name>
        └── <image version>
            ├── specifications.yaml
            └── templates
                └── <distro>.vtmp


Config Options
##############
Under each `system` > `backend` > `distro` section there are a variaty of config options available.

dependencies
------------
The `dependencies` section is a list of images that must be built before the current one can be.

.. code-block:: yaml

    build_specifications:
      frontier:
        apptainer:
          ubuntu:
            dependencies:
              - dep_one
              - dep_two
                # ...

Some times you may want a specific version of a dependency in which case Velocity provides several ways to specify dependency
relationships. Versions are compared by splitting the version string up based on periods and then comparing the sections
left to right alphanumerically.

.. code-block:: yaml

    build_specifications:
      frontier:
        apptainer:
          ubuntu:
            dependencies:
              - dep_one@=11.5       # equal to 11.5
              - dep_two@_11.5       # less than or equal to 11.5
              - dep_three@^11.5     # greater than or equal to 11.5
              - dep_four@11.2%11.8  # inbetween 11.2 and 11.8 (inclusive)
                # ...

prolog
------
There are certain occasions when some commands need to be run on the host machine before an image is built. These
commands can be placed in a bash script in a directory which matches the system name. All that you need to do in the
`specifications.yaml` file is put the script name.

.. code-block:: yaml

    build_specifications:
      frontier:
        apptainer:
          ubuntu:
            dependencies:
              - dep_one
              - dep_two
                # ...
            prolog: example_prolog.sh

.. code-block:: bash
    :caption: VELOCITY_IMAGE_DIR

    .
    ├── <image name>
        └── <image version>
            ├── <system>
            │    └── example_prolog.sh
            ├── specifications.yaml
            └── templates
                └── <distro>.vtmp

arguments
---------
Any arguments specified here will be added to the build command.

.. code-block:: yaml

    build_specifications:
      frontier:
        apptainer:
          ubuntu:
            dependencies:
              - dep_one
              - dep_two
                # ...
            prolog: example_prolog.sh
            arguments:
              - '--build-arg EXAMPLE=8046'

This will result in `apptainer build --build-arg EXAMPLE=8046 ...` when the image is built.

variables
---------
Here you can define :ref:`variables<variables>` for the VTMP file to use when it is parsed.

.. code-block:: yaml

    build_specifications:
      frontier:
        apptainer:
          ubuntu:
            dependencies:
              - dep_one
              - dep_two
                # ...
            prolog: example_prolog.sh
            arguments:
              - '--build-arg EXAMPLE=8046'
            variables:
              - arch: x86_64
              - url: 'https://example.com'
