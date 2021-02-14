<div align="center">

<img src="doc/zl_tile_logo.png" width="100px">

**`zpy`: Synthetic data in Blender.**

<p align="center">
  <a href="https://zumolabs.ai/">Website</a> •
  <a href="#Install">Install</a> •
  <a href="#Examples">Examples</a> •
  <a href="#Contribute">Contribute</a> •
  <a href="#Licence">Licence</a>
</p>

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/zpy)](https://pypi.org/project/zpy/)
[![PyPI Status](https://badge.fury.io/py/zpy.svg)](https://badge.fury.io/py/zpy)
[![Discord](https://img.shields.io/badge/discord-Community-green.svg?logo=discord)](https://discord.gg/UrR97Tyd)
[![license](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://github.com/ZumoLabs/zpy/blob/master/LICENSE)
</div>

## Abstract

Collecting, labeling, and cleaning data for computer vision is a pain. Jump into the future and create your own data instead! This synthetic data is faster to develop with, effectively infinite, and gives you full control to prevent bias and privacy issues from creeping in. We created `zpy` to make synthetic data easy, by simplifying the scene creation process and providing an easy way to generate synthetic data at scale.

## Install

- Windows/Mac/Linux
  - [Install from .zip inside Blender UI](#installzip).
- Linux
  - [Install from script](#installscript_linux)
  - [Developer mode](#developermode_linux)
- Windows
  - [Developer mode](#developermode_windows)

### Install: Using Blender GUI <a name="installzip"></a>

You can install the addon from within Blender itself. Navigate to `Edit` -> `Preferences` -> `Add-ons`. You should be able to install and enable the addon from there there.

![Enabling the addon](./doc/install_zpy.png)

### Install: Linux: Using Install Script <a name="installscript_linux"></a>

``` 
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/ZumoLabs/zpy/main/install.sh?token=<token>)"
```

Set these environment variables for specific versions:

```
export BLENDER_VERSION="2.91"
export BLENDER_VERSION_FULL="2.91.0"
export ZPY_VERSION="v1.3.4"
```

### Install: Linux: Developer Environment <a name="developermode_linux"></a>

First clone the zpy repository:

```
mkdir -p $HOME/zumolabs && cd $HOME/zumolabs
git clone https://github.com/ZumoLabs/zpy.git zpy
```

Set the following environment variables:

```
export ZPY_SRC_PATH="$HOME/zumolabs/zpy"
export BLENDER_VERSION="2.91"
export BLENDER_VERSION_FULL="2.91.0"
export BLENDER_PATH="$HOME/Downloads/blender-${BLENDER_VERSION_FULL}-linux64/${BLENDER_VERSION}"
export BLENDER_LIB_PY="${BLENDER_PATH}/python/lib/python3.7"
export BLENDER_BIN_PY="${BLENDER_PATH}/python/bin/python3.7m"
export BLENDER_BIN_PIP="${BLENDER_PATH}/python/bin/pip3"
```

Install additional Python dependencies using Blender Python's pip:

```
${BLENDER_BIN_PY} -m ensurepip
${BLENDER_BIN_PIP} install --upgrade pip
${BLENDER_BIN_PIP} install -r ${ZPY_SRC_PATH}requirements.txt
```

If you are setting up a development environment it will be easier to symlink the zpy pip module directly into the Blender python library. This can be achieved with something like:

```
ln -s ${ZPY_SRC_PATH}/zpy ${BLENDER_LIB_PY}/site-packages/
mkdir -p ~/.config/blender/${BLENDER_VERSION}/scripts/addons
ln -s ${ZPY_SRC_PATH}/zpy_addon ~/.config/blender/${BLENDER_VERSION}/scripts/addons/zpy_addon
```

### Install: Windows: Developer Environment <a name="developermode_windows"></a>

These instructions use GitBash terminal, make sure to run as administrator!

First clone the zpy repository:

```
mkdir -p $HOME/zumolabs && cd $HOME/zumolabs
git clone https://github.com/ZumoLabs/zpy.git zpy
```

Set the following environment variables:

```
export ZPY_SRC_PATH="$HOME/zumolabs/zpy"
export BLENDER_VERSION="2.91"
export BLENDER_PATH="/c/Program\ Files/Blender\ Foundation/Blender\ ${BLENDER_VERSION}/${BLENDER_VERSION}"
export BLENDER_BIN_PY="${BLENDER_PATH}/python/lib/python.exe"
export BLENDER_BIN_PIP="${BLENDER_PATH}/python/bin/pip3"
```

If you are setting up a development environment it will be easier to symlink the zpy pip module directly into the Blender python library. This can be achieved with something like:

```
ln -s ${ZPY_SRC_PATH}/zpy ${BLENDER_PATH}/python/lib/
ln -s ${ZPY_SRC_PATH}/zpy_addon ${BLENDER_PATH}/scripts/addons
```

Install the dependencies
```
${BLENDER_BIN_PY} -m ensurepip
${BLENDER_BIN_PY} -m pip install --upgrade pip
${BLENDER_BIN_PY} -m pip install -r ${ZPY_SRC_PATH}/requirements.txt
```

## Examples

**Tutorial**
- [Suzanne: Part 1](https://github.com/ZumoLabs/zpy/main/examples/suzzane/README.md)
- [Suzanne: Part 2](https://github.com/ZumoLabs/zpy/main/examples/suzzane_2/README.md)
- [Uploading a Scene](https://github.com/ZumoLabs/zpy/main/examples/uploading_a_scene/README.md)
- [Using the CLI](https://github.com/ZumoLabs/zpy/main/examples/using_the_cli/README.md)

**Projects**
- [Raspberry Pi Component Detection](https://towardsdatascience.com/training-ai-with-cgi-b2fb3ca43929)
- [Vote Counting](https://towardsdatascience.com/patrick-vs-squidward-training-vote-detection-ai-with-synthetic-data-d8e24eca114d)

## Contributing

We welcome community contributions! Search through the [current issues](https://github.com/ZumoLabs/zpy/issues) or open your own.

## Licence

This release of zpy is under the GPLv3 license, a free copyleft license used by Blender. TLDR: Its free, use it!

## BibTeX

If you use `zpy` in your research, we would appreciate the citation!

```bibtex
@article{zpy,
  title={zpy: Synthetic data for Blender.},
  author={Ponte, H. and Ponte, N. and Karatas, K},
  journal={GitHub. Note: https://github.com/ZumoLabs/zpy},
  volume={1},
  year={2020}
}
```
