# encoding: utf-8
"""
This module provides utility methods for dealing with path-specs.
"""

import os
import os.path
import posixpath
import stat

from .compat import collection_type, string_types

NORMALIZE_PATH_SEPS = [sep for sep in [os.sep, os.altsep] if sep and sep != posixpath.sep]
"""
*NORMALIZE_PATH_SEPS* (:class:`list` of :class:`str`) contains the path
separators that need to be normalized to the POSIX separator for the
current operating system. The separators are determined by examining
:data:`os.sep` and :data:`os.altsep`.
"""

_registered_patterns = {}
"""
*_registered_patterns* (``dict``) maps a name (``str``) to the
registered pattern factory (``callable``).
"""

def iter_tree(root, on_error=None, follow_links=None):
	"""
	Walks the specified directory for all files.

	*root* (:class:`str`) is the root directory to search for files.

	*on_error* (:class:`~collections.abc.Callable` or :data:`None`)
	optionally is the error handler for file-system exceptions. It will be
	called with the exception (:exc:`OSError`). Reraise the exception to
	abort the walk. Default is :data:`None` to ignore file-system
	exceptions.

	*follow_links* (:class:`bool` or :data:`None`) optionally is whether
	to walk symbolik links that resolve to directories. Default is
	:data:`None` for :data:`True`.

	Raises :exc:`RecursionError` if recursion is detected.

	Returns an :class:`~collections.abc.Iterable` yielding the path to
	each file (:class:`str`) relative to *root*.
	"""
	if on_error is not None and not callable(on_error):
		raise TypeError("on_error:{!r} is not callable.".format(on_error))

	if follow_links is None:
		follow_links = True

	for file_rel in _iter_tree_next(os.path.abspath(root), '', {}, on_error, follow_links):
		yield file_rel

def _iter_tree_next(root_full, dir_rel, memo, on_error, follow_links):
	"""
	Scan the directory for all descendant files.

	*root_full* (:class:`str`) the absolute path to the root directory.

	*dir_rel* (:class:`str`) the path to the directory to scan relative to
	*root_full*.

	*memo* (:class:`dict`) keeps track of ancestor directories
	encountered. Maps each ancestor real path (:class:`str``) to relative
	path (:class:`str`).

	*on_error* (:class:`~collections.abc.Callable` or :data:`None`)
	optionally is the error handler for file-system exceptions.

	*follow_links* (:class:`bool`) is whether to walk symbolik links that
	resolve to directories.
	"""
	dir_full = os.path.join(root_full, dir_rel)
	dir_real = os.path.realpath(dir_full)

	# Remember each encountered ancestor directory and its canonical
	# (real) path. If a canonical path is encountered more than once,
	# recursion has occurred.
	if dir_real not in memo:
		memo[dir_real] = dir_rel
	else:
		raise RecursionError(real_path=dir_real, first_path=memo[dir_real], second_path=dir_rel)

	for node in os.listdir(dir_full):
		node_rel = os.path.join(dir_rel, node)
		node_full = os.path.join(root_full, node_rel)

		# Inspect child node.
		try:
			node_stat = os.lstat(node_full)
		except OSError as e:
			if on_error is not None:
				on_error(e)
			continue

		if stat.S_ISLNK(node_stat.st_mode):
			# Child node is a link, inspect the target node.
			is_link = True
			try:
				node_stat = os.stat(node_full)
			except OSError as e:
				if on_error is not None:
					on_error(e)
				continue
		else:
			is_link = False

		if stat.S_ISDIR(node_stat.st_mode) and (follow_links or not is_link):
			# Child node is a directory, recurse into it and yield its
			# decendant files.
			for file_rel in _iter_tree_next(root_full, node_rel, memo, on_error, follow_links):
				yield file_rel

		elif stat.S_ISREG(node_stat.st_mode):
			# Child node is a file, yield it.
			yield node_rel

	# NOTE: Make sure to remove the canonical (real) path of the directory
	# from the ancestors memo once we are done with it. This allows the
	# same directory to appear multiple times. If this is not done, the
	# second occurance of the directory will be incorrectly interpreted as
	# a recursion. See <https://github.com/cpburnz/python-path-specification/pull/7>.
	del memo[dir_real]

def lookup_pattern(name):
	"""
	Lookups a registered pattern factory by name.

	*name* (:class:`str`) is the name of the pattern factory.

	Returns the registered pattern factory (:class:`~collections.abc.Callable`).
	If no pattern factory is registered, raises :exc:`KeyError`.
	"""
	return _registered_patterns[name]

def match_file(patterns, file):
	"""
	Matches the file to the patterns.

	*patterns* (:class:`~collections.abc.Iterable` of :class:`~pathspec.pattern.Pattern`)
	contains the patterns to use.

	*file* (:class:`str`) is the normalized file path to be matched
	against *patterns*.

	Returns :data:`True` if *file* matched; otherwise, :data:`False`.
	"""
	matched = False
	for pattern in patterns:
		if pattern.include is not None:
			if file in pattern.match((file,)):
				matched = pattern.include
	return matched

def match_files(patterns, files):
	"""
	Matches the files to the patterns.

	*patterns* (:class:`~collections.abc.Iterable` of :class:`~pathspec.pattern.Pattern`)
	contains the patterns to use.

	*files* (:class:`~collections.abc.Iterable` of :class:`str`) contains
	the normalized file paths to be matched against *patterns*.

	Returns the matched files (:class:`set` of :class:`str`).
	"""
	all_files = files if isinstance(files, collection_type) else list(files)
	return_files = set()
	for pattern in patterns:
		if pattern.include is not None:
			result_files = pattern.match(all_files)
			if pattern.include:
				return_files.update(result_files)
			else:
				return_files.difference_update(result_files)
	return return_files

def normalize_file(file, separators=None):
	"""
	Normalizes the file path to use the POSIX path separator (i.e., ``'/'``).

	*file* (:class:`str`) is the file path.

	*separators* (:class:`~collections.abc.Collection` of :class:`str`; or
	:data:`None`) optionally contains the path separators to normalize.
	This does not need to include the POSIX path separator (``'/'``), but
	including it will not affect the results. Default is :data:`None` for
	:data:`NORMALIZE_PATH_SEPS`. To prevent normalization, pass an empty
	container (e.g., an empty tuple ``()``).

	Returns the normalized file path (:class:`str`).
	"""
	# Normalize path separators.
	if separators is None:
		separators = NORMALIZE_PATH_SEPS
	norm_file = file
	for sep in separators:
		norm_file = norm_file.replace(sep, posixpath.sep)

	# Remove current directory prefix.
	if norm_file.startswith('./'):
		norm_file = norm_file[2:]

	return norm_file

def normalize_files(files, separators=None):
	"""
	Normalizes the file paths to use the POSIX path separator.

	*files* (:class:`~collections.abc.Iterable` of :class:`str`) contains
	the file paths to be normalized.

	*separators* (:class:`~collections.abc.Collection` of :class:`str`; or
	:data:`None`) optionally contains the path separators to normalize.
	See :func:`normalize_file` for more information.

	Returns a :class:`dict` mapping the each normalized file path (:class:`str`)
	to the original file path (:class:`str`)
	"""
	norm_files = {}
	for path in files:
		norm_files[normalize_file(path, separators=separators)] = path
	return norm_files

def register_pattern(name, pattern_factory, override=None):
	"""
	Registers the specified pattern factory.

	*name* (:class:`str`) is the name to register the pattern factory
	under.

	*pattern_factory* (:class:`~collections.abc.Callable`) is used to
	compile patterns. It must accept an uncompiled pattern (:class:`str`)
	and return the compiled pattern (:class:`.Pattern`).

	*override* (:class:`bool` or :data:`None`) optionally is whether to
	allow overriding an already registered pattern under the same name
	(:data:`True`), instead of raising an :exc:`AlreadyRegisteredError`
	(:data:`False`). Default is :data:`None` for :data:`False`.
	"""
	if not isinstance(name, string_types):
		raise TypeError("name:{!r} is not a string.".format(name))
	if not callable(pattern_factory):
		raise TypeError("pattern_factory:{!r} is not callable.".format(pattern_factory))
	if name in _registered_patterns and not override:
		raise AlreadyRegisteredError(name, _registered_patterns[name])
	_registered_patterns[name] = pattern_factory


class AlreadyRegisteredError(Exception):
	"""
	The :exc:`AlreadyRegisteredError` exception is raised when a pattern
	factory is registered under a name already in use.
	"""

	def __init__(self, name, pattern_factory):
		"""
		Initializes the :exc:`AlreadyRegisteredError` instance.

		*name* (:class:`str`) is the name of the registered pattern.

		*pattern_factory* (:class:`~collections.abc.Callable`) is the
		registered pattern factory.
		"""
		super(AlreadyRegisteredError, self).__init__(name, pattern_factory)

	@property
	def message(self):
		"""
		*message* (:class:`str`) is the error message.
		"""
		return "{name!r} is already registered for pattern factory:{pattern_factory!r}.".format(
			name=self.name,
			pattern_factory=self.pattern_factory,
		)

	@property
	def name(self):
		"""
		*name* (:class:`str`) is the name of the registered pattern.
		"""
		return self.args[0]

	@property
	def pattern_factory(self):
		"""
		*pattern_factory* (:class:`~collections.abc.Callable`) is the
		registered pattern factory.
		"""
		return self.args[1]


class RecursionError(Exception):
	"""
	The :exc:`RecursionError` exception is raised when recursion is
	detected.
	"""

	def __init__(self, real_path, first_path, second_path):
		"""
		Initializes the :exc:`RecursionError` instance.

		*real_path* (:class:`str`) is the real path that recursion was
		encountered on.

		*first_path* (:class:`str`) is the first path encountered for
		*real_path*.

		*second_path* (:class:`str`) is the second path encountered for
		*real_path*.
		"""
		super(RecursionError, self).__init__(real_path, first_path, second_path)

	@property
	def first_path(self):
		"""
		*first_path* (:class:`str`) is the first path encountered for
		:attr:`self.real_path <RecursionError.real_path>`.
		"""
		return self.args[1]

	@property
	def message(self):
		"""
		*message* (:class:`str`) is the error message.
		"""
		return "Real path {real!r} was encountered at {first!r} and then {second!r}.".format(
			real=self.real_path,
			first=self.first_path,
			second=self.second_path,
		)

	@property
	def real_path(self):
		"""
		*real_path* (:class:`str`) is the real path that recursion was
		encountered on.
		"""
		return self.args[0]

	@property
	def second_path(self):
		"""
		*second_path* (:class:`str`) is the second path encountered for
		:attr:`self.real_path <RecursionError.real_path>`.
		"""
		return self.args[2]
