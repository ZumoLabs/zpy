import client.zpy as zpy


def test_params(*args, **kwargs):
    """Prints out the available sim params."""
    zpy.init(**kwargs)
    dataset = zpy.Dataset(**kwargs)
    dataset.show_params()


def test_preview(*args, **kwargs):
    zpy.init(**kwargs)
    dataset = zpy.Dataset(**kwargs)

    # Won't exist on anything besides my custom local tests
    dataset.cool_nested_prop = "c"
    dataset.preview()

    # Unset it
    dataset.cool_nested_prop = None

    if "sim_specific_properties" in kwargs:
        # Testing sim specific properties
        for k, v in kwargs["sim_specific_properties"].items():
            dataset.add_sim_specific_param(k, v)

    dataset.preview()


def test_generate(*args, **kwargs):
    zpy.init(**kwargs)
    dataset = zpy.Dataset(**kwargs)

    if "sim_specific_properties" in kwargs:
        # Testing sim specific properties
        for k, v in kwargs["sim_specific_properties"].items():
            dataset.add_sim_specific_param(k, v)

    dataset.generate(*args)


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
        "auth_token": "XXXX",  # Auth token from localStorage
        "project_uuid": "5eb222e1-45ef-46bb-b999-3e07a948b20b",  # Hugo's project has the most sims
        "sim_uuid": "675b25c5-a497-4111-aeba-8e05cca2d409",  # can_v5 - looked to have the most interesting params
        "sim_specific_properties": {
            "probability_glass_effect": 0.1,
            # 'use_distractors': False,
            # 'blur_jitter': False,
        },
    }

    test_params(**local_kwargs)
    test_preview(**local_kwargs)

    test_params(**staging_kwargs)
    test_preview(**staging_kwargs)

    test_generate("can_v5", **staging_kwargs)
