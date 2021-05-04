#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages
import versioneer


def get_requirements_from_file(python_requirements_file="./requirements.txt"):
    """
    Purpose:
        Get python requirements from a specified requirements file.
    Args:
        python_requirements_file (String): Path to the requirements file (usually
            it is requirements.txt in the same directory as the setup.py)
    Return:
        requirements (List of Strings): The python requirements necessary to run
            the library
    """

    requirements = []
    with open(python_requirements_file) as requirements_file:
        requirement = requirements_file.readline()
        while requirement:
            if requirement.strip().startswith("#"):
                pass
            elif requirement.strip() == "":
                pass
            else:
                requirements.append(requirement.strip())
            requirement = requirements_file.readline()

    return requirements


def get_long_description(filepath):
    with open(filepath, "r", encoding="utf-8") as fh:
        long_description = fh.read()
    return long_description


setup(
    name="zpy-zumo",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Create synthetic data with Blender.",
    long_description=get_long_description("README.md"),
    long_description_content_type="text/markdown",
    author="Zumo Labs",
    author_email="infra@zumolabs.ai",
    url="https://github.com/ZumoLabs/zpy",
    packages=find_packages(),
    install_requires=get_requirements_from_file(),
    include_package_data=True,
    entry_points="[console_scripts]\nzpy=cli.cli:cli\n",
)
