import os

from setuptools import setup

SRC_FILE = os.path.join('src', 'build', 'version.py')
TEMPLATE = 'from __future__ import unicode_literals\n\n__version__ = \'{version}\'\n'
try:
    from setuptools_scm import get_version

    version = get_version(write_to=SRC_FILE, write_to_template=TEMPLATE)
except Exception:  # noqa
    with open('version.fallback', 'rt') as read_handler, open(SRC_FILE, 'wt') as write_handler:
        version = read_handler.read().strip()
        write_handler.write(TEMPLATE.format(version=version))

setup(version=version)
