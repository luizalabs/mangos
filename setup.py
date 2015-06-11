#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup


cwd = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(cwd, 'README.md')).read()


setup(
    name='mangos',
    version='0.0.1',
    description="Tornado library to consume Braspag REST Web services",
    long_description=readme,
    author='Daniel Urbano',
    author_email='daniel.urbano@luizalabs.com',
    url='https://github.com/luizalabs/mangos',
    packages=['braspag'],
    test_suite='tests.suite',
    tests_require=['Mock'],
    zip_safe=False,
)
