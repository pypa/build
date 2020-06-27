# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SPHINXAPIDOC  ?= sphinx-apidoc
SOURCEDIR     = source
BUILDDIR      = build
SRCBUILDDIR   = srcbuild
MODULEDIR     = ../src/build
SRCDIR        = ../src

.DEFAULT_GOAL := html

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SRCBUILDDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help apidoc Makefile

apidoc:
	@$(SPHINXAPIDOC) -f -e -o "$(SRCBUILDDIR)" "$(MODULEDIR)"

clean:
	@$(SPHINXBUILD) -M $@ "$(SRCBUILDDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	rm -rf $(SRCBUILDDIR)/*

coverage: Makefile apidoc
	cp -r "$(SOURCEDIR)"/* "$(SRCBUILDDIR)"
	sed -i /:undoc-members:/d "$(SRCBUILDDIR)"/$(notdir $(MODULEDIR))*.rst
	@$(SPHINXBUILD) -M $@ "$(SRCBUILDDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile apidoc
	cp -r "$(SOURCEDIR)"/* "$(SRCBUILDDIR)"
	@PYTHONPATH=$(SRCDIR) $(SPHINXBUILD) -M $@ "$(SRCBUILDDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
