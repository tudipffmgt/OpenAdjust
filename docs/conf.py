"""
Sphinx documentation configuration.
"""

project = 'OpenAdjust'
copyright = '2024, OpenAdjust Contributors'
author = 'OpenAdjust Contributors'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
