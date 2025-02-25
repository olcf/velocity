# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import datetime as dt
import sys

from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent.parent.joinpath("src").absolute()))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Velocity'
copyright = f'{dt.datetime.now().year}, OLCF'
author = 'OLCF'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_copybutton',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon'
]

templates_path = ['_templates']
exclude_patterns = []

# copybutton configuration
copybutton_prompt_text = "$ "


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '_static/icon.png'
html_favicon = '_static/icon.png'
html_theme_options = {
    'style_nav_header_background': '#909d9e'
}
