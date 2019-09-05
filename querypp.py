__version__ = '0.1.0'

import io
import inspect
import os.path
import re
from pathlib import Path

import jinja2
from jinja2 import ext
from jinja2 import nodes

class AttrDict:
	def __init__(self, *args, **kwargs):
		vars(self).update(dict(*args, **kwargs))

class QueryExtension(ext.Extension):
	tags = {'query', 'qblock'}

	def parse(self, parser):
		token = next(parser.stream)
		return (self._parse_query if token.value == 'query' else self._parse_qblock)(parser, token.lineno)

	def _parse_query(self, parser, lineno):
		name = parser.parse_assign_target(with_tuple=False).name
		body = parser.parse_statements(['name:endquery'], drop_needle=True)
		# name, params, defaults, body
		return nodes.Macro(name, [nodes.Name('__blocks__', 'param')], [], body).set_lineno(lineno)

	def _parse_qblock(self, parser, lineno):
		name = parser.parse_assign_target(name_only=True).name
		body = parser.parse_statements(['name:endqblock'], drop_needle=True)
		return nodes.If(
			nodes.Compare(  # name in __blocks__
				nodes.Const(name),
				[nodes.Operand('in', nodes.Name('__blocks__', 'load'))]),
			body,
			[],  # elif_
			[]  # orelse
		).set_lineno(lineno)

class QueryLoader(jinja2.BaseLoader):
	def __init__(self, path):
		self.path = Path(path)

	def get_source(self, environment, template):
		path = self.path / template
		if not path.exists():
			raise jinja2.TemplateNotFound(template)
		mtime = os.path.getmtime(path)
		with path.open() as f:
			source = f.read()
		return self._replace_inline_syntax(source), None, lambda: mtime == os.path.getmtime(path)

	@staticmethod
	def _replace_inline_syntax(text):
		"""convert inline syntax (e.g. "abc -- :block foo def") with multiline syntax"""
		out = io.StringIO()
		for line in text.splitlines(keepends=True):
			m = re.search(
				r'(.*)'
				r'\s*(?P<tag>-- :qblock\s+?\S+?)'
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

class QueryEnvironment(jinja2.Environment):
	def __init__(self, base_path, **kwargs):
		super().__init__(
			loader=QueryLoader(base_path),
			extensions=[QueryExtension] + kwargs.get('extensions', []),
			line_statement_prefix='-- :',
			**kwargs)

	def get_template(self, name, *args, **kwargs):
		return self._wrap_module(super().get_template(name, *args, **kwargs).module)

	@staticmethod
	def _wrap_module(mod):
		for name, val in vars(mod).items():
			if not callable(val) or inspect.isfunction(val) or val.arguments != ('__blocks__',):
				continue

			def wrapped(*blocks, __macro=val):
				return __macro(frozenset(blocks))
			wrapped.__name__ = name
			vars(mod)[name] = wrapped

		return mod
