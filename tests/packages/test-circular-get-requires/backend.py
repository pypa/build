# SPDX-License-Identifier: MIT


def get_requires_for_build_sdist(config_settings=None):
    return ['recursive_dep']


def get_requires_for_build_wheel(config_settings=None):
    return ['recursive_dep']


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    raise NotImplementedError


def build_sdist(sdist_directory, config_settings=None):
    raise NotImplementedError
