import os
import sys

from textwrap import dedent
from zipfile import ZipFile


name = 'demo_pkg_inline'
pkg_name = name.replace('_', '-')

version = '1.0.0'
dist_info = f'{name}-{version}.dist-info'

metadata = f'{dist_info}/METADATA'
wheel = f'{dist_info}/WHEEL'
entry_points = f'{dist_info}/entry_points.txt'
record = f'{dist_info}/RECORD'
init = f'{name}/__init__.py'
content = {
    init: f"def do():\n    print('greetings from {name}')",
    metadata: f"""
        Metadata-Version: 2.1
        Name: {pkg_name}
        Version: {version}
        Summary: Summary of package
        Home-page: Does not exists
        Author: someone
        Author-email: a@o.com
        License: MIT
        Platform: ANY

        Desc
       """,
    wheel: f"""
        Wheel-Version: 1.0
        Generator: {name}-{version}
        Root-Is-Purelib: true
        Tag: py3-none-any
       """,
    f'{dist_info}/top_level.txt': name,
    entry_points: '\n[console_scripts]\ndemo-pkg-inline = demo_pkg_inline:do',
    record: f"""
        {name}/__init__.py,,
        {dist_info}/METADATA,,
        {dist_info}/WHEEL,,
        {dist_info}/top_level.txt,,
        {dist_info}/RECORD,,
       """,
}


def build_wheel(wheel_directory, metadata_directory=None, config_settings=None):
    base_name = f'{name}-{version}-py{sys.version_info.major}-none-any.whl'
    path = os.path.join(wheel_directory, base_name)
    with ZipFile(str(path), 'w') as zip_file_handler:
        for arc_name, data in content.items():
            zip_file_handler.writestr(arc_name, dedent(data).strip())
    print(f'created wheel {path}')
    return base_name


def get_requires_for_build_wheel(config_settings):
    return []
