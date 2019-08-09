#!/usr/bin/env python3

import re

from setuptools import setup

with open('querypp/__init__.py') as f:
	version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
	raise RuntimeError('version is not set')

with open('README.md') as f:
	long_description = f.read()

setup(
	name='querypp',
	version=version,

	description='preprocesses SQL queries to make them modular',
	long_description=long_description,
	long_description_content_type='text/markdown',

	license='CC0 1.0',

	author='Benjamin Mintz',
	author_email='bmintz@protonmail.com',
	url='https://github.com/bmintz/querypp',

	packages=['querypp'],

	extras_require={
		'test': [
			'isort',
			'pylint',
			'pytest',
			'pytest-cov',
		],
	},

	classifiers=[
		'Topic :: Software Development :: Pre-processors',
		'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',

		'Programming Language :: Python :: 3 :: Only',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 3.8',
	],
)
