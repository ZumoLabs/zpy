#!/usr/bin/env python
import os
from distutils.core import setup
from setuptools import find_packages
import versioneer


def get_requirements_from_file(filepath):
    requires = []
    with open(filepath, 'r') as f:
        requires.append(f.readline())
    return requires


def get_long_description(filepath):
    with open(filepath, 'r', encoding='utf-8') as fh:
        long_description = fh.read()
    return long_description


setup(
    name='zpy-zumo',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='Create synthetic data with Blender.',
    long_description=get_long_description('README.md'),
    long_description_content_type="text/markdown",
    author='Zumo Labs',
    author_email='infra@zumolabs.ai',
    url='https://github.com/ZumoLabs/zpy',
    packages=find_packages(),
    install_requires=get_requirements_from_file('requirements.txt'),
    include_package_data=True,
    entry_points='[console_scripts]\nzpy=cli.cli:cli\n',
)
