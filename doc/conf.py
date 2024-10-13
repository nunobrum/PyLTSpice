# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.abspath('../doc/media'))

print(sys.path)

# -- Project information -----------------------------------------------------

project = 'PyLTSpice'
copyright = '2024, Nuno Brum'
author = 'Nuno Brum'

release = '5.4.0'

try:
	# Read the version from the .toml file
	from toml import load
	with open('../pyproject.toml') as f:
		pyproject = load(f)
		project = pyproject['project']['name']
		release = pyproject['project']['version']
		author = pyproject['project']['authors'][0]['name']
except:
	pass


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
	# 'docxbuilder',
	# 'sphinx-docxbuilder',
	'sphinx.ext.todo', 
	'sphinx.ext.viewcode', 
	'sphinx.ext.autodoc',
	#'sphinx.ext.autosummary',
    #'rinoh.frontend.sphinx'
]

#autodoc_default_flags = ['members']
#autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['doc_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'agogo'
html_theme_options = {
    'rightsidebar' : False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']
