import json

import client as zpy


def test_params(*args, **kwargs):
    """Prints out the available sim params."""
    zpy.init(**kwargs)
    # dataset = zpy.Dataset(**kwargs)
    # dataset.show_params()
    sim = zpy.Sim("can_v5")
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


def test_1():
    # zpy.init(
    #     base_url="https://ragnarok.stage.zumok8s.org",
    #     project_uuid="",
    #     auth_token="",
    # )
    zpy.init(
        base_url="http://localhost:8000",
        project_uuid="",
        auth_token=""
    )
    dataset_config = zpy.DatasetConfig("can_v7")
    print(json.dumps(dataset_config.available_params, indent=4, sort_keys=True))

    zpy.preview(dataset_config)
    zpy.generate('can_v7 test.5', dataset_config, num_datapoints=10, materialize=True)


def test_2():
    zpy.init(
        base_url="http://localhost:8000",
        project_uuid="aad8e2b2-5431-4104-a205-dc3b638b0dab",
        auth_token="214540cbd525f1ecf2bc52e2ddb7ef76801048e3f55aa4b33a9e501b115a736e"
    )
    dataset_config = zpy.DatasetConfig("can_v7")
    dataset_config.set("run\\.padding_style", "square")
    print(dataset_config.config)
    zpy.preview(dataset_config)


if __name__ == "__main__":
    # local_kwargs = {
    #     "base_url": "http://localhost:8000",
    #     # The rest need to match something in the dev's local
    #     "auth_token": "c98d1edd78f8e3416c72525942cdb5242b1d518f0582bed8e48ae0fa6be09508",
    #     "project_uuid": "fd914c42-1f50-4b45-82d7-78e9ae440b78",
    #     "sim_uuid": "a7188bb0-07b4-4817-9874-53c684eb4d6c",
    # }
    # staging_kwargs = {
    #     "base_url": "https://ragnarok.zumok8s.org",
    #     # The rest need to match something on staging
    #     "auth_token": "4345497e868c4d4a7a563c05f604c41ed4825a049dbc9c38523254d53ef498c9",  # Auth token from localStorage
    #     "project_uuid": "4b0035d6-7bdd-4be3-adde-939c790437c3",  # Hugo's project has the most sims
    #     "sim_uuid": "3dc167cd-1f80-4548-9662-7a36a822ea8f",  # can_v5 - looked to have the most interesting params
    #     "sim_specific_properties": {
    #         "probability_glass_effect": 0.1,
    #         # 'use_distractors': False,
    #         # 'blur_jitter': False,
    #     },
    # }

    # test_params(**local_kwargs)
    # test_preview(**local_kwargs)

    # test_params(**staging_kwargs)
    # test_preview(**staging_kwargs)

    # test_1()
    test_2()
