# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import build


# -- Project information -----------------------------------------------------

project = 'build'
copyright = '2020, Filipe Laíns'
author = 'Filipe Laíns'

# The short X.Y version
version = build.__version__
# The full version, including alpha/beta/rc tags
release = build.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
    'sphinx_argparse_cli',
    'sphinx_issues',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

default_role = 'any'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'
html_title = f'build {version}'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named 'default.css' will overwrite the builtin 'default.css'.
# html_static_path = ['_static']

autoclass_content = 'both'

nitpick_ignore = [
    # https://github.com/python/importlib_metadata/issues/316
    ('py:class', 'importlib.metadata._meta.PackageMetadata'),
]


issues_github_path = 'pypa/build'
