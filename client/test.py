import json

import client.zpy as zpy


def test_params(*args, **kwargs):
    """Prints out the available sim params."""
    zpy.init(**kwargs)
    # dataset = zpy.Dataset(**kwargs)
    # dataset.show_params()
    sim = zpy.Sim('can_v5')
    sim.show_params()
    sim.preview()

def test_preview(*args, **kwargs):
    zpy.init(**kwargs)
    dataset = zpy.Dataset(**kwargs)

    # Won't exist on anything besides my custom local tests
    # dataset.cool_nested_prop = "c"
    # dataset.preview()

    # Unset it
    # dataset.cool_nested_prop = None

    if "sim_specific_properties" in kwargs:
        # Testing sim specific properties
        for k, v in kwargs["sim_specific_properties"].items():
            dataset.add_sim_specific_param(k, v)

    dataset.preview()


def test_generate(*args, **kwargs):
    zpy.init(**kwargs)
    can_v5_sim = zpy.Sim('can_v5')
    can_v5_sim.show_params()
    can_v5_sim.preview({})

    dataset_config = zpy.DatasetConfig('can_v5')
    print(json.dumps(dataset_config.available_params, indent=4, sort_keys=True))
    # Won't support "generic" properties yet
    # config.paramA = 1
    # config.paramB = 'blah'
    dataset_config.set('custom_param', 'custom_val')
    dataset_config.set('nested__custom__param', 'nested_val')
    dataset_config.remove('nested__custom__param')

    # Still requires pre-generating datasets, throw warnings if none found
    zpy.preview(dataset_config, num_samples=5)
    dataset = zpy.generate('can_v5 test', dataset_config, num_datapoints=10, materialize=True)
    # Return urls or do ipython
    # /api/v1/files?dataset=dataset_id&name_icontains="00000001"
    dataset.sample()

    # dataset = zpy.Dataset(**kwargs)

    # if "sim_specific_properties" in kwargs:
    #     # Testing sim specific properties
    #     for k, v in kwargs["sim_specific_properties"].items():
    #         dataset.add_sim_specific_param(k, v)

    # dataset.generate(*args)


if __name__ == "__main__":
    local_kwargs = {
        "base_url": "http://localhost:8000",
        # The rest need to match something in the dev's local
        "auth_token": "c98d1edd78f8e3416c72525942cdb5242b1d518f0582bed8e48ae0fa6be09508",
        "project_uuid": "fd914c42-1f50-4b45-82d7-78e9ae440b78",
        "sim_uuid": "a7188bb0-07b4-4817-9874-53c684eb4d6c",
    }
    staging_kwargs = {
        "base_url": "https://ragnarok.stage.zumok8s.org",
        # The rest need to match something on staging
        "auth_token": "4345497e868c4d4a7a563c05f604c41ed4825a049dbc9c38523254d53ef498c9",  # Auth token from localStorage
        "project_uuid": "4b0035d6-7bdd-4be3-adde-939c790437c3",  # Hugo's project has the most sims
        "sim_uuid": "3dc167cd-1f80-4548-9662-7a36a822ea8f",  # can_v5 - looked to have the most interesting params
        "sim_specific_properties": {
            "probability_glass_effect": 0.1,
            # 'use_distractors': False,
            # 'blur_jitter': False,
        },
    }

    # test_params(**local_kwargs)
    # test_preview(**local_kwargs)

    test_params(**staging_kwargs)
    # test_preview(**staging_kwargs)

    test_generate("can_v5", 50, **staging_kwargs)
