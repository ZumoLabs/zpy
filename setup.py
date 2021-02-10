#!/usr/bin/env python
import os
from distutils.core import setup
from setuptools import find_packages
import versioneer

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
  name='zpy-zumo',
  version=versioneer.get_version(),
  cmdclass=versioneer.get_cmdclass(),
  description='Zumo Labs Utility Bundle',
  author='Zumo Labs',
  author_email='infra@zumolabs.ai',
  packages=find_packages(),
  install_requires=required,
  include_package_data=True,
)
