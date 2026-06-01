# SPDX-License-Identifier: MIT


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    import os.path
    import zipfile

    from build._compat import tomllib

    with open('pyproject.toml', 'rb') as f:
        metadata = tomllib.load(f)

    wheel_basename = f'{metadata["project"]["name"].replace("-", "_")}-{metadata["project"]["version"]}'
    build_tag = metadata['project'].get('build-tag')
    wheel_filename = f'{wheel_basename}-{build_tag}-py3-none-any.whl' if build_tag else f'{wheel_basename}-py3-none-any.whl'
    with zipfile.ZipFile(os.path.join(wheel_directory, wheel_filename), 'w') as wheel:
        wheel.writestr(
            f'{wheel_basename}.dist-info/METADATA',
            f"""\
Metadata-Version: 2.2
Name: {metadata['project']['name']}
Version: {metadata['project']['version']}
Summary: {metadata['project']['description']}
""",
        )

    return wheel.filename
