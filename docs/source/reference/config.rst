*************
Configuration
*************

Configuration for Velocity comes from three places. Command line options, environment variables and the configuration file.

Commandline Options
###################
These take the highest level of precedence and can be viewed by using the ``--help`` option in the command line.

Variables
#########
Variables are the second highest level of configuration.

.. _velocity_image_path:

`VELOCITY_IMAGE_PATH`
---------------------

This variable points to the directories containing the the image definitions.

`VELOCITY_SYSTEM`
-----------------
This variable specifies what computer system you are building for (e.g. frontier).

`VELOCITY_BACKEND`
------------------
This variable specifies the container backend that should be used (e.g podman).

.. important::

    Available backends are ``apptainer``, ``docker``, ``podman`` and ``singularity``.

`VELOCITY_DISTRO`
-----------------
This variable specifies the distro of the container images that will be built. This name is flexable and completely
up to the user. It is used purely for organizational purposes.

.. _build_dir:

`VELOCITY_BUILD_DIR`
--------------------
This variable specifies a scratch space for Velocity to preform builds in.

.. _velocity_config_dir:

`VELOCITY_CONFIG_DIR`
---------------------

This variable specifies where to look for the configuration file.

Configuration File
##################
The configuration file is the lowest level of configuration. By default Velocity looks for ``config.yaml`` in
``~/.velocity`` unless :ref:`velocity_config_dir` is set. A number of configuration option for velocity can be set.

.. code-block:: yaml

    velocity:
      system: frontier
      backend: apptainer
      distro: ubuntu
      debug: INFO   # set the debug level
      image_path:   # a list of : seperated paths
      build_dir:    # path to a scratch space

Additionally you can set :ref:`arguments` and :ref:`specVariables` at a global level in the constraints section. As an example here
we are adding ``--disable-cache`` as an argument for every image build we do with apptainer.

.. code-block:: yaml

    constraints:
      arguments:
        - value: --disable-cache
          when: backend=apptainer

.. note::

    Arguments and variables can also be set from the command line when building by passing something like
    ``-A "value: --disable-cache; when: backend=apptainer"`` to the build command for as many arguments as needed.