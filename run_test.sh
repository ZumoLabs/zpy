#!/bin/bash

set -eo pipefail

SCENE_NAME="test_full_v1"

# apt setup
apt-get update
apt-get install

# pip setup
${BLENDERPIP} install -r requirements.txt
${BLENDERPIP} install .

# CLI Login + Create the Test Dataset
zpy login ${ZPY_USER} ${ZPY_PASS}
zpy get scene "$SCENE_NAME" .
unzip "${SCENE_NAME}*"

/bin/blender-softwaregl --background --enable-autoexec --python launcher.py
python launcher_helper.py --generate --scene_dir /bender
