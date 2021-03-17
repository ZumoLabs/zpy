#!/bin/bash

set -eo pipefail

SCENE_NAME="test_full_v1"

# pip setup
pip install /bender/zpy

# CLI Login + Create the Test Dataset
zpy login ${ZPY_USER} ${ZPY_PASS}
zpy get scene "$SCENE_NAME" .
unzip "$SCENE_NAME"*

/bin/blender-softwaregl --background --enable-autoexec --python launcher.py
python launcher_helper.py --generate --scene_dir /bender
