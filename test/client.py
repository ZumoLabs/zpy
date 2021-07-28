import json
import re
import shutil
from os import listdir
from os.path import join

import zpy.client as zpy


def test_1(**init_kwargs):
    """In local env, simruns exist for config { "run.padding_style": "square" }"""
    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig(sim_name="can_v7")
    dataset_config.set("run\\.padding_style", "square")
    print(dataset_config.config)
    previews = zpy.preview(dataset_config)
    urls = [preview["url"] for preview in previews]
    print(json.dumps(urls, indent=4, sort_keys=True))


def test_2(**init_kwargs):
    """In local env, simruns do NOT exist for config { "run.padding_style": "messy" }"""
    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig("can_v7")
    dataset_config.set("run\\.padding_style", "messy")
    print(dataset_config.config)
    previews = zpy.preview(dataset_config)
    urls = [preview["url"] for preview in previews]
    print(json.dumps(previews, indent=4, sort_keys=True))
    print(json.dumps(urls, indent=4, sort_keys=True))


def test_3(**init_kwargs):
    """"""
    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig("dumpster_v2")
    # dataset_config.set("run\\.padding_style", "square")
    zpy.generate("dumpster_v2.39", dataset_config, num_datapoints=3, materialize=True)


def test_4():
    zpy.init(project_uuid='feb6e594-55e0-4f87-9e75-5a128221499f',
             auth_token='a4a13763b0dc0017b1fc9af890e9efea58fd072074ab9a169e5dcf0633310f28')
    # zpy.init(project_uuid='aad8e2b2-5431-4104-a205-dc3b638b0dab',
    #          auth_token='9344ca735850d929748c9fda008f7479f2411e0876a593d6160f99fcc25762a4',
    #          base_url="http://localhost:8000")
    # init_kwargs = {
    #     "base_url": "https://ragnarok.stage.zumok8s.org",
    #     "project_uuid": "feb6e594-55e0-4f87-9e75-5a128221499f",
    #     "auth_token": "33032c0cc774c9211d861eaf5d92740076c4034cd408b535a5c1858d44425cb7",
    # }
    zpy.init(**init_kwargs)
    sim_name = "dumpster_v5"
    dataset_config = zpy.DatasetConfig(sim_name)
    print(dataset_config.categories)
    dataset_config.categories = 3
    print(dataset_config.categories)
    help(dataset_config)
    dataset_config = zpy.DatasetConfig("can_v7")
    help(dataset_config)
    # help(zpy.DatasetConfig)
    # categories: Dict[int, str] = {
    #     0: 'full',
    #     1: 'ok',
    #     #        2: 'not in dumpster',
    #     #        3: 'can not see'
    # }
    # dataset_config.set('only_category', 'full')
    # dataset_config.set('categories', {0: 'not in dumpster'})
    # print(dataset_config.config)
    # samples = zpy.preview(dataset_config, num_samples=10)
    # pprint(samples)
    # zpy.generate("dumpster_v8_ktest_6", dataset_config, num_datapoints=8)


def test_saver_func(images, annotations):
    """
    Same output as:
    https://gist.github.com/steven-zumo/d44b16ae5173931c7943f8f4531cda41

    """
    output_path = "/mnt/c/Users/georg/Zumo/Datasets/dumpster_v2.1_formatted"
    for img in images:
        # maybe an awkward way to match an image to it's annotation
        img_annotation = next(
            (a for a in annotations["annotations"] if a["filename_image"] in img), None
        )
        if img_annotation is not None:
            category_id = str(img_annotation["category_id"])
            category_label = annotations["categories"][category_id]["name"]
            # awkward way to access batch name from image uri
            batch = img.split("/")[-2]
            # save same result as stevens example
            output_file_uri = join(
                output_path,
                category_label
                + "-"
                + batch[:4]
                + "-"
                + img_annotation["filename_image"]
                + ".jpg",
            )
            shutil.copy(img, output_file_uri)


def format_dataset(path_to_zipped_dataset, saver_func):
    # https://www.geeksforgeeks.org/how-to-validate-image-file-extension-using-regular-expression/
    # https://realpython.com/regex-python/ - How to fix from example - DeprecationWarning: Flags not at the start of the expression
    regex = "(?i)([^\\s]+(\\.(jpe?g|png|gif|bmp))$)"  # Regex to check valid image file extension.
    pattern = re.compile(regex)
    annotation_file_name = "_annotations.zumo.json"
    for batch in listdir(path_to_zipped_dataset):
        batch_uri = join(path_to_zipped_dataset, batch)
        image_names = [str for str in listdir(batch_uri) if re.search(pattern, str)]
        image_uris = [join(path_to_zipped_dataset, batch, p) for p in image_names]
        annotation_file_uri = join(batch_uri, annotation_file_name)
        metadata = json.load(open(annotation_file_uri))
        saver_func(image_uris, metadata)


if __name__ == "__main__":
    init_kwargs = {
        "base_url": "http://localhost:8000",
        "version": "v2",
        "project_uuid": "aad8e2b2-5431-4104-a205-dc3b638b0dab",
        "auth_token": "214540cbd525f1ecf2bc52e2ddb7ef76801048e3f55aa4b33a9e501b115a736e",
    }
    # init_kwargs = {
    #     "base_url": "https://ragnarok.stage.zumok8s.org",
    #     "project_uuid": "91419af0-4815-41e7-9b77-5ef8154148c8",  # Compology
    #     "auth_token": "a51cacaa01082ba5237b49f74cd6ffa5cf88339345383d97bcadd1f99e5f9a01",
    # }
    # init_kwargs = {
    #     "base_url": "https://ragnarok.zumok8s.org",
    #     "project_uuid": "91419af0-4815-41e7-9b77-5ef8154148c8",  # Compology
    #     "auth_token": "7c1baae380c14a89b558a2fbf5f1c0ad923e61298c3ec87a0bdae6debbe549cb",
    # }
    # print("Running test_1:")
    # test_1(**init_kwargs)
    # print("Running test_2:")
    # test_2(**init_kwargs)
    # print("Running test_3:")
    # test_3(**init_kwargs)
    test_4()
    # test format dataset
    # input_path = "/mnt/c/Users/georg/Zumo/Datasets/dumpster_v2.1"
    # format_dataset(input_path, test_saver_func)
