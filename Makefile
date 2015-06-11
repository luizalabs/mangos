test:
	ASYNC_TEST_TIMEOUT=30.0 nosetests -v --stop --with-coverage --cover-package=braspag

coverage:
	ASYNC_TEST_TIMEOUT=30.0 nosetests -v --stop --with-coverage --cover-package=braspag --cover-html
	open cover/index.html

clean:
	rm -rf cover/
