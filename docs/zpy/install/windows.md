# Install Developer Environment on Windows

These instructions use GitBash terminal, make sure to run as administrator!

First clone the zpy repository:

```
mkdir -p $HOME/zumolabs && cd $HOME/zumolabs
git clone https://github.com/ZumoLabs/zpy.git zpy
```

Set the following environment variables:

```
export ZPY_SRC_PATH="$HOME/zumolabs/zpy"
export BLENDER_VERSION="2.92"
export BLENDER_PATH="/c/Program\ Files/Blender\ Foundation/Blender\ ${BLENDER_VERSION}/${BLENDER_VERSION}"
export BLENDER_BIN_PY="${BLENDER_PATH}/python/bin/python.exe"
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
