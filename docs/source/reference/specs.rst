*******************
Specs.yaml
*******************

About
#####
The `specs.yaml` file defines image availability, dependencies and a number of other available
options for an image.

Config Options
##############

versions
--------
The `versions` section defines a list of versions and their availability.

.. code-block:: yaml

    versions:
      - spec: 45
        when: distro=ubuntu
      - spec:
          - 46
          - 47
        when: backend=podman

dependencies
------------
The `dependencies` section is used to specify prerequist images.

.. code-block:: yaml

    dependencies:
      - spec: ubuntu
        when: distro=ubuntu
      - spec:
          - "gcc@12:"
          - pytorch
        when: myapp@:2.3

templates
---------
By default velocity looks for a template called ``default.vtmp``, but using the `templates` section you can specify an
alternate template.

.. code-block:: yaml

    templates:
      - name: second_tmp
        when: "myapp@2:"

.. _arguments:

arguments
---------
Use the `argument` section to add build time arguments to an image.

.. code-block:: yaml

    arguments:
      - value: --disable-cache
        when: backend=apptainer

.. _specVariables:

variables
---------
Use the `variables` section to set template variables.

.. code-block:: yaml

    variables:
      - name: test_var
        value: "Test value."

files
-----
Use the `files` section to specify files or directories in the `files` folder that you want copied to the build directory.

.. code-block:: yaml

    files:
      - name: config.json

prologs
-------
Use the `prologs` section to bash commands that you want to run before the build.

.. code-block:: yaml

    prologs:
      - script: |
          git clone ...
        when: system=summit

Using ``when``
##############
A few notes about using ``when`` to filter config options. The ``when`` option can be used to filter configs as shown
above by system, backend, distro and dependencies. The only exception to this is the `versions` section which cannot
be filtered by dependencies. List each item that you want to filter by separated by a space e.g. ``gcc@12.3 system=frontier``.
Additionally you can specify the scope of a ``when`` by specifying the ``scope``. The default scope is ``image`` which means
that the when statement is evaluated on the current image. So say you want to apply a config in the gcc `specs.yaml` file
to every gcc version greater than 10.3.0, you would use ``when: ^ubuntu:``. Alternatively you can set the scope to ``build``
when you want the when statement evaluated on the current build.

.. code-block:: yaml

    variable:
      - name: TEST
        value: "1 2 3 4"
        when: ubuntu
        scope: build

This can be read as "If the ubuntu image is in the current set of images to be built then add the TEST variable."
