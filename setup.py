#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup


cwd = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(cwd, 'README.md')).read()


setup(
    name='mangos',
    version='0.0.3',
    description="Tornado library to consume Braspag REST Web services",
    long_description=readme,
    author='Daniel Urbano',
    author_email='daniel.urbano@luizalabs.com',
    url='https://github.com/luizalabs/mangos',
    packages=['braspag_rest'],
    test_suite='tests.suite',
    tests_require=['Mock'],
    zip_safe=False,
    classifiers=[
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ]
)
