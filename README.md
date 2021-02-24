<div align="center">

<img src="doc/zl_tile_logo.png" width="100px">

**`zpy`: Synthetic data in Blender.**

<p align="center">
  <a href="https://zumolabs.ai/">Website</a> •
  <a href="#Install">Install</a> •
  <a href="#Examples">Examples</a> •
  <a href="#CLI">CLI</a> •
  <a href="#Contribute">Contribute</a> •
  <a href="#Licence">Licence</a>
</p>

<p align="center">
  <a href="https://discord.gg/nXvXweHtG8"><img alt="Discord" title="Discord" src="https://img.shields.io/badge/-ZPY Devs-grey?style=for-the-badge&logo=discord&logoColor=white"/></a>
  <a href="https://twitter.com/ZumoLabs"><img alt="Twitter" title="Twitter" src="https://img.shields.io/badge/-@ZumoLabs-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white"/></a>
  <a href="https://www.youtube.com/channel/UCcU2Z8ArljfDzfq7SOz-ytQ"><img alt="Youtube" title="Youtube" src="https://img.shields.io/badge/-ZumoLabs-red?style=for-the-badge&logo=youtube&logoColor=white"/></a>
  <a href="https://pypi.org/project/zpy-zumo/"><img alt="PyPI" title="PyPI" src="https://img.shields.io/badge/-PyPI-yellow?style=for-the-badge&logo=PyPI&logoColor=white"/></a>
</p>

</div>

## Abstract

Collecting, labeling, and cleaning data for computer vision is a pain. Jump into the future and create your own data instead! Synthetic data is faster to develop with, effectively infinite, and gives you full control to prevent bias and privacy issues from creeping in. We created `zpy` to make synthetic data easy, by simplifying the scene creation process and providing an easy way to generate synthetic data at scale.

## Install

- [Install from .zip within Blender UI **(Windows/Mac/Linux)**](#installzip).
- [Install from script **(Mac/Linux)**](#installscript_linux)
- [Developer mode **(Linux)**](https://github.com/ZumoLabs/zpy/tree/main/doc/developer_mode.md#install-linux-developer-environment-)
- [Developer mode **(Windows)**](https://github.com/ZumoLabs/zpy/tree/main/doc/developer_mode.md#install-windows-developer-environment-)

### Install: Using Blender GUI <a name="installzip"></a>

First download the latest [zip](https://github.com/ZumoLabs/zpy/releases) (you want the one called `zpy_addon-v*.zip`). Then open up Blender. Navigate to `Edit` -> `Preferences` -> `Add-ons`. You should be able to install and enable the addon from there.

![Enabling the addon](./doc/install_zpy.png)

### Install: Linux: Using Install Script <a name="installscript_linux"></a>

``` 
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/ZumoLabs/zpy/main/install.sh?token=<token>)"
```

Set these environment variables for specific versions:

```
export BLENDER_VERSION="2.91"
export BLENDER_VERSION_FULL="2.91.0"
export ZPY_VERSION="v1.0.0"
```

## Examples

**Tutorials**
- [Suzanne: Part 1](https://github.com/ZumoLabs/zpy/tree/main/examples/suzanne)
- [Suzanne: Part 2](https://github.com/ZumoLabs/zpy/tree/main/examples/suzanne_2)
- [Suzanne: Part 3](https://github.com/ZumoLabs/zpy/tree/main/examples/suzanne_3)
- [Uploading a Scene](https://github.com/ZumoLabs/zpy/tree/main/examples/uploading_a_scene)

**Projects**
- [Raspberry Pi Component Detection](https://towardsdatascience.com/training-ai-with-cgi-b2fb3ca43929)
- [Vote Counting](https://towardsdatascience.com/patrick-vs-squidward-training-vote-detection-ai-with-synthetic-data-d8e24eca114d)

## CLI

We provide a simple CLI, you can find documentation [here](https://github.com/ZumoLabs/zpy/tree/main/doc/cli/README.md).

<p align="center"><img src="doc/cli/gif/createdataset.gif?raw=true"/></p>

## Contributing

We welcome community contributions! Search through the [current issues](https://github.com/ZumoLabs/zpy/issues) or open your own.

## Licence

This release of zpy is under the GPLv3 license, a free copyleft license used by Blender. TLDR: Its free, use it!

## BibTeX

If you use `zpy` in your research, we would appreciate the citation!

```bibtex
@article{zpy,
  title={zpy: Synthetic data for Blender.},
  author={Ponte, H. and Ponte, N. and Karatas, K},
  journal={GitHub. Note: https://github.com/ZumoLabs/zpy},
  volume={1},
  year={2020}
}
```
