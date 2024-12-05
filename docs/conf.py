# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Transformer Service"
copyright = "2024, Michał Kołomański & Wiktor Florian"
author = "Michał Kołomański & Wiktor Florian"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.autodoc_pydantic",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


# -- Dynamic .rst generation -------------------------------------------------
def run_apidoc(app):
    """Generate .rst files dynamically."""
    base_dir = os.path.abspath("..")
    apidoc_output_dirs = {
        "app": "../app",
        "schemas": "../schemas",
        "tests": "../tests",
    }

    for input_folder, module in apidoc_output_dirs.items():
        if os.path.exists(input_folder):
            for f in os.listdir(input_folder):
                if f.endswith(".rst"):
                    os.remove(os.path.join(input_folder, f))

        try:
            print(f"sphinx-apidoc -o {input_folder}, {module}")
            subprocess.run(
                ["sphinx-apidoc", "-o", input_folder, module],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error during apidoc generation: {e}")


def setup(app):
    """Connect the apidoc generation to the Sphinx builder."""
    app.connect("builder-inited", run_apidoc)
