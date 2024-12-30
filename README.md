![icon.drawio.png](misc/artwork/icon_name.drawio.png)

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/olcf/velocity/tests.yaml?label=tests)](https://github.com/olcf/velocity/actions/workflows/tests.yaml)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/olcf/velocity/docs.yaml?label=docs)](https://github.com/olcf/velocity/actions/workflows/docs.yaml)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/olcf/velocity/linter.yaml?label=linter)](https://github.com/olcf/velocity/actions/workflows/linter.yaml)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/olcf/velocity/build.yaml?label=build&color=https%3A%2F%2Fgithub.com%2Folcf%2Fvelocity%2Factions%2Fworkflows%2Flinter.yaml)](https://github.com/olcf/velocity/actions/workflows/build.yaml)
[![GitHub Release](https://img.shields.io/github/v/release/olcf/velocity?label=github&color=%23782D84)](https://github.com/olcf/velocity/releases)
[![PyPI - Version](https://img.shields.io/pypi/v/olcf-velocity?color=%23FFD242)](https://pypi.org/project/olcf-velocity)
[![Spack](https://img.shields.io/spack/v/py-olcf-velocity?color=%230F3A80)](https://packages.spack.io/package.html?name=py-olcf-velocity)

-----------------------------------------------------------

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
