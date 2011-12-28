# (c) 2005-2011 PIDA Authors


test-build: clean
	virtualenv test-ve
	test-ve/bin/python setup.py install


sdist: clean MANIFEST.in
	python setup.py sdist --formats=gztar,zip


sdist: clean MANIFEST.in
	python setup.py sdist --formats=gztar,zip


clean:
	rm -rf a8.egg-info build dist MANIFEST.in

define MANIFEST_BODY
include a8/*.py
include a8/data/a8.vim
include a8/data/icons/*.png
include README
endef

export MANIFEST_BODY

MANIFEST.in:
	echo "$$MANIFEST_BODY" > MANIFEST.in

