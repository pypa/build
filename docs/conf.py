# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import warnings

import build


if hasattr(__builtins__, 'EncodingWarning'):
    warnings.filterwarnings('ignore', category=EncodingWarning, module='sphinx_copybutton')


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
    'sphinx_copybutton',
    'sphinx_inline_tabs',
    'sphinx_issues',
    'sphinxcontrib.mermaid',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'packaging': ('https://packaging.python.org/en/latest/', None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['changelog/*']

default_role = 'any'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'
html_title = f'build - {version}'
html_show_sourcelink = False
html_favicon = '_static/logo.svg'
html_theme_options = {
    'light_logo': 'logo.svg',
    'dark_logo': 'logo.svg',
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named 'default.css' will overwrite the builtin 'default.css'.
html_static_path = ['_static']
html_css_files = ['custom.css']

autoclass_content = 'both'

nitpick_ignore = [
    # https://github.com/python/importlib_metadata/issues/316
    ('py:class', 'importlib.metadata._meta.PackageMetadata'),
    ('py:data', 'typing.Union'),
]


issues_github_path = 'pypa/build'

copybutton_prompt_text = r'>>> |\.\.\. |\$ '
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = False
copybutton_remove_prompts = True
