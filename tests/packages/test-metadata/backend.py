# SPDX-License-Identifier: MIT

import pathlib
import textwrap


def get_requires_for_build_wheel(config_settings=None):
    return ['tomli']


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    import tomli

    with open('pyproject.toml', 'rb') as f:
        metadata = tomli.load(f)

    distinfo = pathlib.Path(
        metadata_directory,
        '{}-{}.dist-info'.format(
            metadata['project']['name'].replace('-', '-'),
            metadata['project']['version'],
        ),
    )
    distinfo.mkdir(parents=True, exist_ok=True)
    distinfo.joinpath('METADATA').write_text(
        textwrap.dedent(
            f"""
            Metadata-Version: 2.2
            Name: {metadata['project']['name']}
            Version: {metadata['project']['version']}
            Summary: {metadata['project']['description']}
            """
        ).strip()
    )
    return distinfo.name


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    raise NotImplementedError


def build_sdist(sdist_directory, config_settings=None):
    raise NotImplementedError
