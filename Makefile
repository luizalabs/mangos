test:
	ASYNC_TEST_TIMEOUT=30.0 nosetests -v --stop --with-coverage --cover-package=braspag_rest

coverage:
	ASYNC_TEST_TIMEOUT=30.0 nosetests -v --stop --with-coverage --cover-package=braspag_rest --cover-html
	open cover/index.html

clean:
	rm -rf cover/
