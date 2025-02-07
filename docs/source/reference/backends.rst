********
Backends
********

This page describes the implemented backends and their available configuration.

Apptainer
#########

Uses the `apptainer <https://apptainer.org/docs/user/main/index.html>`_ container system.

Docker
######

Uses the `docker <https://docs.docker.com/>`_ container system.

OpenShift
#########

Uses the `openshift <https://www.redhat.com/en/technologies/cloud-computing/openshift>`_ platform.

CPU Limit
---------

Set the cpu limit for a build via
``VELOCITY_OPENSHIFT_CPU_LIMIT`` or ``openshift:cpu:limit`` in the :ref:`velocity_config_file`.
The default is ``1000m``.

Memory Limit
------------

Set the memory limit for a build via
``VELOCITY_OPENSHIFT_MEMORY_LIMIT`` or ``openshift:memory:limit`` in the :ref:`velocity_config_file`.
The default is ``2Gi``.

Podman
######

Uses the `podman <https://podman.io/docs>`_ container system.

Singularity
###########

Uses the `singularity <https://docs.sylabs.io/guides/latest/user-guide/>`_ container system.
