.. Velocity documentation master file, created by
   sphinx-quickstart on Mon Mar 18 12:43:01 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Velocity Container Build Management
===================================
Velocity is a tool to help with the maintenance of container build scripts on multiple systems, backends
(e.g podman or apptainer) and distros.

Often, when building containers, you may want to try different distros or combinations of software. Usually, this requires
copying your container script and making modifications. Velocity aims to cut down on the time wasted in this repetitive process and the
clutter of numerous scripts with minor changes. Velocity does this by compartmentalizing your software stack and
templating your software installations.

.. important::

   Documentation hosted at `olcf.github.io/velocity <https://olcf.github.io/velocity>`_ follows the ``develop`` branch.

.. toctree::
   :maxdepth: 2

   starting/index

.. toctree::
   :maxdepth: 2

   reference/index
