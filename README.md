# zpy

Utility bundle for use with bpy.

## Cutting a Release

Fetch and list existing tags

```
git fetch --tag
git tag
```

Cut a release candidate (ex. v1.0.0-rc0) or release (ex. v1.0.0)

```
git tag <version>
git push origin <version>
```

Check progress on [CI](https://app.circleci.com/pipelines/github/ZumoLabs/zpy)

Check progress on [packagecloud](https://packagecloud.io/zumolabs/pypi)

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

Export packagecloud pypi as external index url.

```
export PIP_EXTRA_INDEX_URL="https://74ab8c3212f97d202fdfe59ce6ff9baa2fed10cae3552aee:@packagecloud.io/zumolabs/pypi/pypi/simple"
```

Then install the pip module

```
$BLENDER_BIN_PIP install zpy-zumo
```
