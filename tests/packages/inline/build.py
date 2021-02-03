import os
import sys

from textwrap import dedent
from zipfile import ZipFile


name = 'demo_pkg_inline'
pkg_name = name.replace('_', '-')

version = '1.0.0'
dist_info = '{}-{}.dist-info'.format(name, version)

metadata = '{}/METADATA'.format(dist_info)
wheel = '{}/WHEEL'.format(dist_info)
entry_points = '{}/entry_points.txt'.format(dist_info)
record = '{}/RECORD'.format(dist_info)
init = '{}/__init__.py'.format(name)
content = {
    init: "def do():\n    print('greetings from {}')".format(name),
    metadata: """
        Metadata-Version: 2.1
        Name: {}
        Version: {}
        Summary: Summary of package
        Home-page: Does not exists
        Author: someone
        Author-email: a@o.com
        License: MIT
        Platform: ANY

        Desc
       """.format(
        pkg_name, version
    ),
    wheel: """
        Wheel-Version: 1.0
        Generator: {}-{}
        Root-Is-Purelib: true
        Tag: py3-none-any
       """.format(
        name, version
    ),
    '{}/top_level.txt'.format(dist_info): name,
    entry_points: '\n[console_scripts]\ndemo-pkg-inline = demo_pkg_inline:do',
    record: """
        {0}/__init__.py,,
        {1}/METADATA,,
        {1}/WHEEL,,
        {1}/top_level.txt,,
        {1}/RECORD,,
       """.format(
        name, dist_info
    ),
}


def build_wheel(wheel_directory, metadata_directory=None, config_settings=None):
    base_name = '{}-{}-py{}-none-any.whl'.format(name, version, sys.version_info.major)
    path = os.path.join(wheel_directory, base_name)
    with ZipFile(str(path), 'w') as zip_file_handler:
        for arc_name, data in content.items():
            zip_file_handler.writestr(arc_name, dedent(data).strip())
    print('created wheel {}'.format(path))
    return base_name


def get_requires_for_build_wheel(config_settings):
    return []
