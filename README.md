![icon.drawio.png](misc/artwork/icon_name.drawio.png)

-----------------------------------------------------------

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/olcf/velocity/tests.yaml?style=flat-square&label=tests)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/olcf/velocity/docs.yaml?style=flat-square&label=docs)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/olcf/velocity/build.yaml?event=release&style=flat-square&label=build)
![GitHub - Version](https://img.shields.io/github/v/release/olcf/velocity?display_name=tag&style=flat-square&label=github&color=%23782D84)
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
