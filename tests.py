from pathlib import Path

import pytest

from querypp import Query

TESTS_DIR = Path(__file__).parent / 'tests'

def test_no_params():
	with open(TESTS_DIR / 'no_params.txt') as f:
		text = f.read()
	assert text == Query(text).text

def test_nested():
	with open(TESTS_DIR / 'nested' / 'query.txt') as f:
		text = f.read().strip()

	params = {'foo', 'bar'}

	q = Query(text)
	assert q(*params).strip() == text

	assert set(q.params) == params

	cases = []
	for param in params:
		with open(TESTS_DIR / 'nested' / f'expected_{param}.txt') as f:
			cases.append((param, f.read().strip()))

	for param, expected in cases:
		print(param)  # in case one fails we wanna see which one
		assert q(param).strip() == expected
