

test-build: clean
	virtualenv test-ve
	test-ve/bin/python setup.py install

clean:
	rm -rf a8.egg-info build dist

