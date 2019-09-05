#!/usr/bin/env python3

import re

from setuptools import setup

with open('querypp.py') as f:
	version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
	raise RuntimeError('version is not set')

with open('README.md') as f:
	long_description = f.read()

setup(
	name='querypp',
	version=version,

	description='SQL query templating shorthand',
	long_description=long_description,
	long_description_content_type='text/markdown',

	license='CC0 1.0',

	author='Benjamin Mintz',
	author_email='bmintz@protonmail.com',
	url='https://github.com/bmintz/querypp',

	py_modules=['querypp'],

	install_requires=[
		'jinja2>=2.10.1,<3.0.0',
	],

	classifiers=[
		'Topic :: Software Development',
		'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',

		'Programming Language :: Python :: 3 :: Only',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 3.8',
	],
)
