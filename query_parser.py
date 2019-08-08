import io
import collections
import re
import textwrap

from utils import AttrDict

ParamNode = collections.namedtuple('ParamNode', 'name tree')

class Query:
	"""A pre-processed SQL query.

	Queries consist of plain text with parameter comments as follows:
	-	A parameter block consists of a line -- :param <param name> followed by 0 or more lines of text
		followed by a line consisting of -- :endparam. Consecutive whitespace is ignored.
	-	A parameter line consists of optional text, followed by -- :param <param name> <param content>
	Parameter names may be used more than once.

	Calling a query object as a function with names of parameters will return query text
	that has only those parameters and no others.
	Nested parameters are supported: including a parameter will not include nested parameters unless also requested.

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
		else:
			raise TypeError('__init__ takes 0 to 2 positional arguments but {} were given'.format(len(args)))

		self.name = name
		self.text = text
		self._replace_inline_syntax()
		self.tree = self._parse(self.text.splitlines())

	def _replace_inline_syntax(self):
		"""convert inline syntax (e.g. "abc -- :param foo bar") with multiline syntax"""
		out = io.StringIO()
		for line in self.text.splitlines(keepends=True):
			m = re.search(r'(.*)\s*(?P<tag>--\s*?:param\s*?\S+?)\s+(?P<content>\S.*)', line)
			if not m:
				out.write(line)
				continue

			for group in m.groups():
				out.write(group)
				out.write('\n')
			out.write('-- :endparam\n')

		self.text = out.getvalue()

	def _parse(self, lines):
		ast = []
		name = None
		buffer = []
		depth = 0
		for line in lines:
			m = re.search(
				r'--\s*?:(?P<end>end)??param'  # "-- :param" or "-- :endparam"
				r'\s*(?P<name>\S+)?',  # "-- :param user_id"
				line)

			if depth < 0:
				raise AssertionError('endparam found but not in a param')

			if m and m['name'] and m['end']:
				raise AssertionError('`-- :endparam` found with a name')

			if depth:
				buffer.append(line)
				if m and m['end']:
					depth -= 1
					if depth == 0:
						ast.append(ParamNode(name, self._parse(tuple(buffer))))
						name, buffer = None, []
				if m and m['name']:
					depth += 1
			elif m and m['name']:
				depth += 1
				name = m['name']
			else:
				ast.append(line)

		if depth:
			raise AssertionError('EOF seen but there were params open')

		return ast

	def __call__(self, *params: str):
		"""return the query as text, including the given params and no others"""
		params = frozenset(params)

		def gen(tree):
			for node in tree:
				if type(node) is str:  # pylint: disable=unidiomatic-typecheck
					yield node
					continue

				param, tree = node
				if param in params:
					yield from gen(tree)

		return '\n'.join(gen(self.tree))

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
			current_tag = match[1]
		if current_tag:
			vars(queries).setdefault(current_tag, []).append(line)

	for tag, query in vars(queries).items():
		queries[tag] = Query(tag, ''.join(query))

	return queries
