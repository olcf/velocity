#!/usr/bin/env bash

# VELOCITY_ROOT (& PATH)
echo
VELOCITY_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "VELOCITY_ROOT=$VELOCITY_ROOT"
export VELOCITY_ROOT
export PATH=$VELOCITY_ROOT:$PATH

# VELOCITY_IMAGE_DIR
echo
read -rp "Set VELOCITY_IMAGE_DIR [$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )-images]: " VELOCITY_IMAGE_DIR
if [[ -z $VELOCITY_IMAGE_DIR ]]; then
  VELOCITY_IMAGE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )-images"
fi
echo "VELOCITY_IMAGE_DIR=$VELOCITY_IMAGE_DIR"
export VELOCITY_IMAGE_DIR


# VELOCITY_SYSTEM
echo
old_ifs=$IFS
IFS='.'
read -ra split_hostname <<< "$(hostname -f)"
IFS=$old_ifs
read -rp "Set VELOCITY_SYSTEM [${split_hostname[1]}]: " VELOCITY_SYSTEM
if [[ -z $VELOCITY_SYSTEM ]]; then
  VELOCITY_SYSTEM=${split_hostname[1]}
fi
echo "VELOCITY_SYSTEM=$VELOCITY_SYSTEM"
export VELOCITY_SYSTEM

# VELOCITY_BACKEND
echo
echo "Select VELOCITY_BACKEND: "
select VELOCITY_BACKEND in podman apptainer; do
    case $VELOCITY_BACKEND in
      podman)
        break
        ;;
      apptainer)
        break
        ;;
      *)
        continue
        ;;
    esac
done
echo "VELOCITY_BACKEND=$VELOCITY_BACKEND"
export VELOCITY_BACKEND

# VELOCITY_DISTRO
echo
echo "Select VELOCITY_DISTRO: "
select VELOCITY_DISTRO in centos ubuntu opensuse fedora; do
    case $VELOCITY_DISTRO in
      centos)
        break
        ;;
      ubuntu)
        break
        ;;
      opensuse)
        break
        ;;
      fedora)
        break
        ;;
      *)
        continue
        ;;
    esac
done
echo "VELOCITY_DISTRO=$VELOCITY_DISTRO"
export VELOCITY_DISTRO

# VELOCITY_BUILD_DIR
echo
read -rp "Set VELOCITY_BUILD_DIR [/tmp/velocity/build]: " VELOCITY_BUILD_DIR
if [[ -z $VELOCITY_BUILD_DIR ]]; then
  VELOCITY_BUILD_DIR="/tmp/velocity/build"
fi
echo "VELOCITY_BUILD_DIR=$VELOCITY_BUILD_DIR"
export VELOCITY_BUILD_DIR
