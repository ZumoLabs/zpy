#!/bin/bash

set -e
set -u
set -o pipefail

ZPY_VERSION=$(git describe --tags --dirty --always)
DATASET_NAME="${test-$ZPY_VERSION}"
DATASET_STATE="NONE"
SCENE_NAME="test_full_v1"
SLEEP_TIME=20

# CLI Login + Create the Test Dataset
zpy login ${ZPY_USER} ${ZPY_PASS}
zpy create dataset ${DATASET_NAME} ${SCENE_NAME}

# Loop until failure or success
while [ $DATASET_STATE != "GENERATING_FAILED" -o $DATASET_STATE == "READY"]; do
DATASET_STATE=$(zpy list datasets | grep ${DATASET_NAME} | awk '{print $2}')
sleep ${SLEEP_TIME}
done

if [$DATASET_STATE == "GENERATING_FAILED"]; do
exit -1
done

exit 1
