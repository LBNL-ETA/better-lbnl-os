"""Configuration file for the Sphinx documentation builder."""

import os
import sys
from datetime import datetime

# Add source directory to path
sys.path.insert(0, os.path.abspath("../src"))

# Project information
project = "BETTER-LBNL"
copyright = f"{datetime.now().year}, Lawrence Berkeley National Laboratory"
author = "Han Li"
release = "0.1.0"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx_rtd_theme",
    "nbsphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"
autodoc_mock_imports = ["plotly", "matplotlib"]

# Napoleon settings for Google style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "pydantic": ("https://docs.pydantic.dev", None),
}

# HTML output settings
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "style_nav_header_background": "#2980B9",
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

html_static_path = ["_static"]
html_logo = None  # Add logo file later
html_favicon = None  # Add favicon later

# LaTeX output settings
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
    "preamble": "",
    "figure_align": "htbp",
}

latex_documents = [
    (
        "index",
        "better-lbnl.tex",
        "BETTER-LBNL Documentation",
        "Han Li",
        "manual",
    ),
]

# nbsphinx settings for Jupyter notebooks
nbsphinx_execute = "never"  # Don't execute notebooks during build
nbsphinx_allow_errors = False
nbsphinx_timeout = 60
