import builtins
import sys
from pathlib import Path

import pytest

from querypp import Query, QuerySyntaxError, load_sql

TESTS_DIR = Path(__file__).parent / 'tests'

if sys.version_info <= (3, 5):
	# py 3.5 does not support opening Paths
	open = lambda file, **kwargs: builtins.open(str(file), **kwargs)  # pylint: disable=invalid-name

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
		with open(TESTS_DIR / 'nested' / 'expected_{}.txt'.format(param)) as f:
			cases.append((param, f.read().strip()))

	for param, expected in cases:
		print(param)  # in case one fails we wanna see which one
		assert q(param).strip() == expected

def test_invalid_syntax():
	with pytest.raises(QuerySyntaxError, match='endparam found but not in a param'):
		Query('-- :endparam')

	with pytest.raises(QuerySyntaxError, match='EOF seen but there were params open'):
		Query('-- :param foo')
		Query('-- :param foo\n--:param bar\n-- :endparam')

def test_inline():
	...  # TODO

# pylint: disable=no-member
def test_load_sql():
	with open(TESTS_DIR / 'multi.txt') as f:
		queries = load_sql(f)

	assert len(queries) == 2
	assert queries.a().strip() == '\n'.join(['-- :name a', 'foo', 'bar', 'baz'])
	assert queries.b().strip() == '\n'.join(['-- :name b', 'quux', 'garply', 'waldo'])

def test_arg_parsing():
	q = Query('foo', 'bar')
	assert q.name == 'foo'
	assert q.text == 'bar'

	q = Query('baz')
	assert q.name is None
	assert q.text == 'baz'

	q = Query(text='quux')
	assert q.name is None
	assert q.text == 'quux'

	q = Query(name='garply', text='waldo')
	assert q.name == 'garply'
	assert q.text == 'waldo'

	with pytest.raises(TypeError):
		Query('fred', name='shit i ran out of names')

	with pytest.raises(TypeError):
		Query('a', 'b', 'c')

def test_param_arg_validation():
	with open(TESTS_DIR / 'nested' / 'query.txt') as f:
		text = f.read()

	q = Query(text)
	with pytest.raises(TypeError):
		q(1)

	with pytest.raises(ValueError):
		q('baz')
