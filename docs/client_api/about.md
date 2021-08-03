# Python client

## Overview

The zpy client enables you to generate and download synthetic datasets.

This API is in early access. If you're interested in using it, email us at info@zumolabs.ai.

## Quick start guide

### Install

You can install `zpy` with pip:

```bash
pip install zpy-zumo
```

### Generating your first dataset

```python
# Make sure you're using the latest version of the zpy library:
#   pip install zpy-zumo --upgrade
import zpy.client as zpy

# We'll provide your project id during on-boarding
project_uuid="..."

# This is your temporary auth token. It can be found by visiting:
#     https://app.zumolabs.ai/settings/auth-token
#
# The auth token will expire when you log out of the web app
auth_token="..."

zpy.init(project_uuid=project_uuid, auth_token=auth_token)

# The simulation (sim) is the packaged version of the blender assets and
# generations script.
# 
# We'll give you the sim for your specific project and share new sim names when we
# create new versions.
sim_name = "demo_sim_v1"

# A DatasetConfig defines what synthetic data you want generated.
# 
# For now, there are no parameters to configure. But in the future, this will include
# sim specific parameters like: changing the cropping style or selecting which classes
# should be included in a dataset.
dataset_config = zpy.DatasetConfig(sim_name)

# The generate call will cause our backend to actually generate a dataset. 
#
# Currently known issues:
# * Takes ~5 minutes to provision and spin up machines for larger generation jobs >200
#   images.
zpy.generate(dataset_config, num_datapoints=50, materialize=True)
```
