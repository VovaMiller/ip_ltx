# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Extra Installations -----------------------------------------------------
# pip install sphinx-pyproject
# pip install myst-parser
# pip install furo

# -- Making Project Discoverable ---------------------------------------------

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from sphinx_pyproject import SphinxConfig

config = SphinxConfig("../../pyproject.toml", globalns=globals())

project = "{}{}".format(
    globals().get("name", "ip_ltx"),
    f" ({globals()["version"]})" if ("version" in globals()) else ""
)
copyright = "2026, Vova Miller"
html_title = f"{project} — Документация"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "myst_parser",  # Allows processing .md files natively
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.12", None),
}

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ['_templates']
exclude_patterns = []

language = 'ru'

autodoc_typehints = "description"  # "signature"

nitpicky = True
nitpick_ignore = [
    ("py:class", "D"),
    ("py:class", "R"),
    ("py:class", "T"),
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ['_static']
