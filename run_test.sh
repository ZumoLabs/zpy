#!/bin/bash

set -e
set -u
set -o pipefail

ZPY_VERSION=$(git describe --tags --dirty --always)
DATASET_NAME="test ${ZPY_VERSION} $(date '+%d/%m/%Y %H:%M:%S')"
SCENE_NAME="test_full_v1"
SLEEP_TIME=20
DATASET_STATE="NONE"
END_STATES=(READY GENERATING_FAILED)

# CLI Login + Create the Test Dataset
zpy login ${ZPY_USER} ${ZPY_PASS}
zpy create dataset ${DATASET_NAME} ${SCENE_NAME}

# Loop until failure or success
while ! [[ ${END_STATES[*]} =~ "$DATASET_STATE" ]]; do
DATASET_STATE=$(zpy list datasets | grep ${DATASET_NAME:0:20} | awk '{print $2}')
echo "dataset '${DATASET_NAME}' :: ${DATASET_STATE}"
sleep ${SLEEP_TIME}
done

if [$DATASET_STATE == "GENERATING_FAILED"]; then
echo "dataset '${DATASET_NAME}' generation failed"
exit -1
fi
