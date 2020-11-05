#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages
import versioneer

setup(
  name='zpy-zumo',
  version=versioneer.get_version(),
  cmdclass=versioneer.get_cmdclass(),
  description='Zumo Labs Utility Bundle',
  author='Zumo Labs',
  author_email='infra@zumolabs.ai',
  packages=find_packages(),
  install_requires=[
    'numpy==1.19.4',
    'gin-config==0.3.0',
    'scikit-image==0.17.2',
    'shapely==1.7.1',
    'seaborn==0.11.0',
    'ptvsd==4.3.2'
  ],
  include_package_data=True,
)
