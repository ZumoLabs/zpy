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
aws s3 cp s3://zumo-labs/prod/ragnarok-scenes/$SCENE_ID.zip test.zip
unzip test.zip -d /bender/scene

# create fake assets dir
export ASSETS="/tmp"
cp /bender/scene/textures/test_hdri.hdr /tmp/lib/hdris/1k/test_hdri.hdr
cp /bender/scene/textures/test_texture.jpg /tmp/lib/textures/random/test_texture.jpg

/bin/blender-softwaregl --background --enable-autoexec --python /bender/launcher.py &
${BLENDERPY} /bender/launcher_helper.py --generate --scene_dir /bender/scene
