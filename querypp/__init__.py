import collections
import io
import re
import textwrap

from .utils import AttrDict

__version__ = '0.0.3'

class QuerySyntaxError(Exception):
	pass

# pylint: disable=unidiomatic-typecheck
class Query:
	"""A pre-processed SQL query.

	Queries consist of plain text with "block" comments as follows:
	-	A block consists of a line -- :block <block name> followed by 0 or more lines of text
		followed by a line consisting of -- :endblock. Consecutive whitespace is ignored.
	-	An inline blick consists of optional text, followed by -- :block <block name> <block content>
	Block names may be used more than once.

	Calling a query object as a function with names of blocks will return query text
	that has only those blocks and no others.
	Nested blocks are supported: including a block will not include nested blocks unless also requested.

	Usage:
	-	Query(text)
	-	Query(name, text)
	-	Query(name=name, text=text)
	-	Query(text=text)
	"""
	def __init__(self, *args, name=None, text=None):
		if args and (name is not None or text is not None):
			raise TypeError('args and kwargs may not both be passed')
		if len(args) == 1:
			text = args[0]
		elif len(args) == 2:
			name, text = args
		elif args:
			raise TypeError('__init__ takes 0 to 2 positional arguments but {} were given'.format(len(args)))

		self.name = name
		self.text = self._replace_inline_syntax(text)
		self.tree = self._parse(self.text.splitlines())
		self.blocks = frozenset(self._extract_blocks(self.tree))

	@staticmethod
	def _replace_inline_syntax(text):
		"""convert inline syntax (e.g. "abc -- :block foo def") with multiline syntax"""
		out = io.StringIO()
		for line in text.splitlines(keepends=True):
			m = re.search(
				r'(.*)'
				r'\s*(?P<tag>--\s*?:block\s+?\S+?)'
				r'\s+(?P<content>\S.*)',
				line)
			if not m:
				out.write(line)
				continue

			for group in m.groups():
				out.write(group)
				out.write('\n')
			out.write('-- :endblock\n')

		return out.getvalue()

	@classmethod
	def _parse(cls, lines):
		ast = []
		name = None
		buffer = []
		depth = 0
		for line in lines:
			m = re.search(
				r'--\s*?:(?P<end>end)??block'  # "-- :block" or "-- :endblock"
				r'\s*(?P<name>\S+)?',  # "-- :block user_id"
				line)

			if depth < 0 or not depth and m and m.group('end'):
				raise QuerySyntaxError('endblock found but not in a block', line)

			if depth:
				name, buffer, depth = cls._parse_block_line(ast, name, buffer, depth, m, line)
			elif m and m.group('name'):  # start of block
				depth += 1  # this depth += 1 is duplicated so that depth is incremented regardless of current depth
				name = m.group('name')
				buffer.append(line)
			else:  # top level line (outside of a block)
				ast.append(line)

		if depth:
			# pylint: disable=undefined-loop-variable  # depth > 0 only if the loop ran
			raise QuerySyntaxError('EOF seen but there were blocks open', line, name)

		return ast

	# pylint: disable=too-many-arguments
	@classmethod
	def _parse_block_line(cls, ast, name, buffer, depth, m, line):
		buffer.append(line)
		if m and m.group('end'):
			depth -= 1
			if not depth:
				# we've gathered all the lines for this block, so it's time to parse them
				# don't send the tags to the recursive call or it'll try to parse them again
				without_tags = buffer[1:-1]
				ast.append((name, [buffer[0]] + cls._parse(without_tags) + [buffer[-1]]))
				name, buffer = None, []
		elif m and m.group('name'):  # start of block
			depth += 1

		return name, buffer, depth

	def __call__(self, *blocks: str):
		"""return the query as text, including the given blocks and no others"""

		for block in blocks:
			if not isinstance(block, str):
				raise TypeError('block name must be a string', block)
			if block not in self.blocks:
				raise ValueError('block name not valid', block)

		blocks = frozenset(blocks)

		def gen(tree):
			for node in tree:
				if type(node) is str:
					yield node
					continue

				block, tree = node
				if block in blocks:
					yield from gen(tree)

		return '\n'.join(gen(self.tree))

	@classmethod
	def _extract_blocks(cls, tree):
		for node in tree:
			if type(node) is str:
				continue

			block, tree = node
			yield block
			yield from cls._extract_blocks(tree)

	def __repr__(self):
		shortened = textwrap.shorten('\n'.join(self.text.splitlines()[1:]), 50)
		return '{0.__class__.__qualname__}(name={0.name!r}, text={1!r})'.format(self, shortened)


def load_sql(fp):
	"""given a file-like object, read the queries delimited by `-- :name foo` comment lines
	return a dict mapping these names to their respective SQL queries
	the file-like is not closed afterwards.
	"""
	# tag -> list[lines]
	queries = AttrDict()
	current_tag = ''

	for line in fp:
		match = re.match(r'\s*--\s*:name\s*(\S+).*?$', line)
		if match:
			current_tag = match.group(1)
		if current_tag:
			vars(queries).setdefault(current_tag, []).append(line)

	for tag, query in vars(queries).items():
		queries[tag] = Query(tag, ''.join(query))

	return queries
