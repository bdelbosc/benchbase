# benchbase Makefile
#
.PHONY: build pkg sdist egg install clean

TARGET := gateway:/opt/public-dev/benchbase

# use TAG=a for alpha, b for beta, rc for release candidate
ifdef TAG
	PKGTAG := egg_info --tag-build=$(TAG) --tag-date
else
    PKGTAG :=
endif


build:
	python setup.py $(PKGTAG) build

pkg: sdist egg

sdist:
	python setup.py $(PKGTAG) sdist

egg:
	-python2.6 setup.py $(PKGTAG) bdist_egg
	-python2.7 setup.py $(PKGTAG) bdist_egg

distrib:
	-scp dist/benchbase-*.tar.gz $(TARGET)/snapshots
	-scp dist/benchbase-*.egg $(TARGET)/snapshots

install:
	python setup.py $(PKGTAG) install

register:
	-python2.6 setup.py register $(PKGTAG) sdist bdist_egg upload
	-python2.7 setup.py register $(PKGTAG) bdist_egg upload

uninstall:
	-rm -rf /usr/local/lib/python2.6/dist-packages/benchbase-*
	-rm -f /usr/local/bin/benchbase

test:
	nosetests -v

env:
	pip install -I --upgrade -s -E env -r deps.txt
	@echo "Remember to run 'source env/bin/activate'"

check:
	pyflakes benchbase

clean:
	find . "(" -name "*~" -or  -name ".#*" -or  -name "#*#" -or -name "*.pyc" ")" -print0 | xargs -0 rm -f
	rm -rf ./build ./dist ./MANIFEST ./benchbase.egg-info
