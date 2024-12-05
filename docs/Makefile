# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build
SPHINXAPIDOC = sphinx-apidoc
APIDOC_MODULES = schemas app tests
APIDOC_OUTPUT  = docs

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Generate .rst files using sphinx-apidoc
apidocs:
	@echo "Generating .rst files with sphinx-apidoc..."
	@for module in $(APIDOC_MODULES); do \
	    echo "Processing $$module"; \
	    $(SPHINXAPIDOC) -o $$module ../$$module; \
	done

html: apidocs
	@echo "Building HTML documentation..."
	@$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)

clean:
	rm -rf $(BUILDDIR)
	rm -rf docs/schemas/*
	rm -rf docs/app/*
	rm -rf docs/tests/*

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
