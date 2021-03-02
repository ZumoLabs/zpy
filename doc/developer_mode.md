
# Developer Mode

More nuanced instructions for installing zpy if you want to contribute.

## Install: Linux: Developer Environment <a name="developermode_linux"></a>

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
${BLENDER_BIN_PIP} install -r ${ZPY_SRC_PATH}/requirements.txt
```

If you are setting up a development environment it will be easier to symlink the zpy pip module directly into the Blender python library. This can be achieved with something like:

```
ln -s ${ZPY_SRC_PATH}/zpy ${BLENDER_LIB_PY}/site-packages/
mkdir -p ~/.config/blender/${BLENDER_VERSION}/scripts/addons
ln -s ${ZPY_SRC_PATH}/zpy_addon ~/.config/blender/${BLENDER_VERSION}/scripts/addons/zpy_addon
```

## Install: Windows: Developer Environment <a name="developermode_windows"></a>

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
