# this does not extend dict so that public method names, such as "clear"
# which may be desirable as keys, are not dispatched to the dict class
class AttrDict:
	def __init__(self, *args, **kwargs):
		vars(self).update(dict(*args, **kwargs))

	def __getitem__(self, key):
		try:
			return getattr(self, key)
		except AttributeError:
			raise KeyError(key)

	def __setitem__(self, key, value):
		setattr(self, key, value)

	def __delitem__(self, key):
		try:
			delattr(self, key)
		except AttributeError:
			raise KeyError(key)

	def __iter__(self):
		return iter(vars(self))

	def __len__(self):
		return len(vars(self))

	def __bool__(self):
		return bool(vars(self))

	def __eq__(self, other):
		return vars(self) == vars(other)

	def __repr__(self):
		return '{}({})'.format(type(self).__qualname__, vars(self))
