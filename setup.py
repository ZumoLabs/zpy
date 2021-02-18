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


try:
    setup(
        name='zpy-zumo',
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        description='Zumo Labs Utility Bundle',
        author='Zumo Labs',
        author_email='infra@zumolabs.ai',
        packages=find_packages(),
        install_requires=get_requirements_from_file('requirements.txt'),
        include_package_data=True,
        entry_points='''
  [console_scripts]
  zpy=cli.cli:cli
  '''
    )
except:
    # TODO: Why does versioner causes issues on Windows
    this_file_path = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.abspath(
        os.path.join(this_file_path, 'requirements.txt'))
    setup(
        name='zpy',
        description='Zumo Labs Utility Bundle',
        author='Zumo Labs',
        author_email='infra@zumolabs.ai',
        packages=find_packages(),
        install_requires=get_requirements_from_file(requirements_path),
    )
