"""
Sphinx configuration file for the arithmetic_client_server project documentation.

This file contains settings and extensions used to generate the project documentation.
"""

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys


# Add the src directory to sys.path so autodoc can find your modules
sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = "arithmetic_client_server"
copyright = "2025, Clement Burtscher"
author = "Clement Burtscher"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    "myst_parser",  # Allows the use of Markdown in Sphinx documentation
    "sphinx.ext.autodoc",  # Enables automatic documentation generation from docstrings
    "sphinx.ext.napoleon",  # Supports NumPy and Google style docstrings
    "sphinx_autodoc_typehints",  # Shows type hints in function/method signatures in the documentation
    "sphinx_copybutton",  # Adds "Copy" buttons to code blocks
]

# Include both class and __init__ docstrings
autoclass_content = "both"

# Settings for autodoc
autodoc_default_options = {
    "members": True,  # Include documented members
    "undoc-members": True,  # Include members without docstrings
    "private-members": False,  # Don't include _private members
    "special-members": "__init__",  # Include __init__ method
    "inherited-members": True,  # Include members from base classes
    "show-inheritance": True,  # Show class inheritance info
}

# -- Paths for templates and static files (optional) -------------------------
templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Settings for Napoleon to support NumPy docstrings
napoleon_numpy_docstring = True
napoleon_google_docstring = False  # You can enable this if needed
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False

# -- Pydantic-specific settings ----------------------------------------------
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_field_list_validators = False
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_field_show_constraints = False
autodoc_pydantic_model_signature_prefix = "class"
autodoc_pydantic_field_show_required = True
autodoc_pydantic_model_member_order = "bysource"

# Configure sphinx-copybutton
copybutton_selector = "div.highlight pre"  # Selector for the code blocks (where the copy button will appear)
copybutton_text = "copy"  # Text that will be displayed on the "Copy" button
