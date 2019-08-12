import builtins
import sys
from pathlib import Path

import pytest

from querypp import Query, QuerySyntaxError, load_sql

TESTS_DIR = Path(__file__).parent / 'tests'

if sys.version_info < (3, 6):
	# py 3.5 does not support opening Paths
	open = lambda file, **kwargs: builtins.open(str(file), **kwargs)  # pylint: disable=invalid-name

def test_no_blocks():
	with open(TESTS_DIR / 'no_blocks.txt') as f:
		text = f.read()
	assert text == Query(text).text

def test_nested():
	with open(TESTS_DIR / 'nested' / 'query.txt') as f:
		text = f.read().strip()

	blocks = {'foo', 'bar'}

	q = Query(text)
	assert q(*blocks).strip() == text

	assert set(q.blocks) == blocks

	cases = []
	for block in blocks:
		with open(TESTS_DIR / 'nested' / 'expected_{}.txt'.format(block)) as f:
			cases.append((block, f.read().strip()))

	for block, expected in cases:
		print(block)  # in case one fails we wanna see which one
		assert q(block).strip() == expected

def test_invalid_syntax():
	with pytest.raises(QuerySyntaxError, match='endblock found but not in a block'):
		Query('-- :endblock')

	with pytest.raises(QuerySyntaxError, match='EOF seen but there were blocks open'):
		Query('-- :block foo')
		Query('-- :block foo\n--:block bar\n-- :endblock')

def test_inline():
	q = Query('-- :block username WHERE username = $1')
	assert not q().strip()
	assert len(q.blocks) == 1
	assert 'WHERE username = $1' in q('username').splitlines()

# pylint: disable=no-member
def test_load_sql():
	with open(TESTS_DIR / 'multi.txt') as f:
		queries = load_sql(f)

	assert len(queries) == 2
	assert queries.a().strip() == '\n'.join(['-- :name a', 'foo', 'bar', 'baz'])
	assert queries.b().strip() == '\n'.join(['-- :name b', 'quux', 'garply', 'waldo'])

	# necesssary to get 100% branch coverage
	assert not load_sql(iter(['']))

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

def test_block_arg_validation():
	with open(TESTS_DIR / 'nested' / 'query.txt') as f:
		text = f.read()

	q = Query(text)
	with pytest.raises(TypeError):
		q(1)

	with pytest.raises(ValueError):
		q('baz')

def test_repr():
	q = Query('', '')
	assert repr(q) == "Query(name='', text='')"
