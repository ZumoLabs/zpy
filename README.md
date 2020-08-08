# zpy

Utility bundle for use with bpy.

## Install

Download the latest Blender [here](https://www.blender.org/download/). This code has been tested using Blender version:

```
export BLENDER_VERSION = "2.83"
```

Set this environment variable to the path of your Blender install. An example command:

**You will have to change these paths depending on your system.**

```
export BLENDER_PATH="/home/ook/Downloads/blender-2.83.3-linux64/2.83"
export BLENDER_LIB_PY="${BLENDER_PATH}/python/lib/python3.7"
export BLENDER_BIN_PY="${BLENDER_PATH}/python/bin/python3.7m"
export BLENDER_BIN_PIP="${BLENDER_PATH}/python/bin/pip3"
```

Symlink (or copy) this folder to the python libraries folder in your blender installation.

```
ln -s ~/zumolabs/zpy $BLENDER_LIB_PY/zpy
```

You will also need to install some additional pip modules into Blender. First install and upgrade pip itself:

```
$BLENDER_BIN_PY -m ensurepip
$BLENDER_BIN_PIP install --upgrade pip
```

Then install the needed pip modules

```
$BLENDER_BIN_PIP install numpy
$BLENDER_BIN_PIP install gin-config
```