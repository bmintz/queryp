import io
import re
import textwrap
import typing
from collections import defaultdict

from utils import AttrDict

LineNumber = typing.NewType('LineNumber', int)

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
		self.params = defaultdict(list)
		self._replace_inline_syntax()
		self._parse()

	def _replace_inline_syntax(self):
		"""convert inline syntax (e.g. "abc -- :param foo bar") with multiline syntax"""
		out = io.StringIO()
		for line in self.text.splitlines(keepends=True):
			m = re.search(r'(.*)?\s*(?P<tag>--\s*?:param\s*?\S+?)\s+(?P<text>\S.*)', line)
			if m:
				for group in m.groups():
					out.write(group)
				out.write('-- :endparam\n')
			else:
				out.write(line)

		self.text = out.getvalue()

	def _parse(self):
		stack = []
		current_param: List[LineNumber] = []
		for lineno, line in enumerate(self.text.splitlines()):
			m = re.search(
				r'--\s*?:(?P<end>end)??param'  # "-- :param" or "-- :endparam"
				r'\s*(?P<name>\S+)?',  # "-- :param user_id"
				line)

			# if we're in a param, append all linenos up until the start of another one
			if stack and not (m and m['name']):
				current_param.append(lineno)

			if not m:  # nothing more we can do
				continue

			if m['end'] and m['name']:
				raise AssertionError('`-- :endparam` found with a name')

			# we have a valid match, either it's a start tag:
			if m['name']:
				if stack:
					# start of a new param means we need the linenos from the previous one too (if there was one)
					self.params[stack[-1]].extend(current_param)
					current_param.clear()
				stack.append(m['name'])
				current_param.append(lineno)
			# or an end tag:
			if m['end']:
				try:
					self.params[stack.pop()].extend(current_param)
				except IndexError as exc:
					raise AssertionError('endparam found but not in a param', lineno)
				current_param.clear()

		if stack:
			raise AssertionError('EOF seen but there were params open', stack)

		# no more defaultdict
		self.params = dict(self.params)

	def __call__(self, *params):
		"""return the query as text, including the given params and no others"""
		unwanted = set(self.params) - set(params)
		lines = self.text.splitlines()
		linenos = []
		for query_linenos in map(self.params.get, unwanted):
			linenos.extend(query_linenos)
		for lineno in sorted(linenos, reverse=True):
			del lines[lineno]
		return '\n'.join(lines)

	def __repr__(self):
		shortened = textwrap.shorten('\n'.join(self.text.splitlines()[1:]), 50)
		return f'{type(self).__qualname__}(name={self.name!r}, text={shortened!r})'


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
			queries.__dict__.setdefault(current_tag, []).append(line)

	for tag, query in vars(queries).items():
		queries[tag] = Query(tag, ''.join(query))

	return queries
