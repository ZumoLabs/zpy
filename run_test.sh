#!/bin/bash

set -eo pipefail

SCENE_ID="fac16daa-6c55-499e-aee6-dcf97ce75a43"
ASSETS="/tmp"

# apt setup
apt-get update
apt-get install -qy awscli

# pip setup
${BLENDERPIP} install .

# fetch scene
mkdir /bender/scene
aws s3 cp s3://zumo-labs/prod/ragnarok-scenes/$SCENE_ID.zip /bender/scene/test.zip
unzip /bender/scene/test.zip

/bin/blender-softwaregl --background --enable-autoexec --python launcher.py &
python launcher_helper.py --generate --scene_dir /bender/scene
