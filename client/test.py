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
    """In local env, simruns exist for config { "run.padding_style": "square" }"""
    zpy.init(
        base_url="http://localhost:8000",
        project_uuid="aad8e2b2-5431-4104-a205-dc3b638b0dab",
        auth_token="214540cbd525f1ecf2bc52e2ddb7ef76801048e3f55aa4b33a9e501b115a736e",
    )
    dataset_config = zpy.DatasetConfig("can_v7")
    dataset_config.set("run\\.padding_style", "square")
    print(dataset_config.config)
    previews = zpy.preview(dataset_config)
    urls = [preview["url"] for preview in previews]
    print(json.dumps(urls, indent=4, sort_keys=True))


def test_2():
    """In local env, simruns do NOT exist for config { "run.padding_style": "messy" }"""
    zpy.init(
        base_url="http://localhost:8000",
        project_uuid="aad8e2b2-5431-4104-a205-dc3b638b0dab",
        auth_token="214540cbd525f1ecf2bc52e2ddb7ef76801048e3f55aa4b33a9e501b115a736e",
    )
    dataset_config = zpy.DatasetConfig("can_v7")
    dataset_config.set("run\\.padding_style", "messy")
    print(dataset_config.config)
    previews = zpy.preview(dataset_config)
    urls = [preview["url"] for preview in previews]
    print(json.dumps(urls, indent=4, sort_keys=True))


def test_3():
    """"""
    # zpy.init(
    #     base_url="https://ragnarok.stage.zumok8s.org",
    #     project_uuid="",
    #     auth_token="",
    # )
    zpy.init(
        base_url="http://localhost:8000",
        project_uuid="aad8e2b2-5431-4104-a205-dc3b638b0dab",
        auth_token="214540cbd525f1ecf2bc52e2ddb7ef76801048e3f55aa4b33a9e501b115a736e",
    )
    dataset_config = zpy.DatasetConfig("can_v7")
    dataset_config.set("run\\.padding_style", "messy")
    zpy.generate("can_v7 test.10", dataset_config, num_datapoints=10, materialize=True)


if __name__ == "__main__":
    print("Running test_1:")
    test_1()
    print("Running test_2:")
    test_2()
    print("Running test_3:")
    test_3()
