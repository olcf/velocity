![icon.drawio.png](misc/artwork/icon_name.drawio.png)

-----------------------------------------------------------

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/olcf/velocity/tests?event=push&style=flat-square&label=test)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/olcf/velocity/docs?branch=develop&event=push&style=flat-square&label=deploy%20docs)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/olcf/velocity/build?event=release&style=flat-square&label=build)
[![PyPI - Version](https://img.shields.io/pypi/v/olcf-velocity?style=flat-square&color=%23FFD242)](https://pypi.org/project/olcf-velocity)
[![Spack](https://img.shields.io/spack/v/py-olcf-velocity?style=flat-square&color=%230F3A80)](https://packages.spack.io/package.html?name=py-olcf-velocity)

## Description
Velocity is a tool to help with the maintenance of container build scripts on 
multiple systems, backends (e.g podman or apptainer) and distros.

## Documentation
See <https://olcf.github.io/velocity/>.

## Installation
``` commandline
pip install olcf-velocity
alias velocity="python3 -m velocity"
velocity
```
