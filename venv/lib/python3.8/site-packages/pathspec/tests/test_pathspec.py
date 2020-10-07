# encoding: utf-8
"""
This script tests ``PathSpec``.
"""

import unittest

import pathspec


class PathSpecTest(unittest.TestCase):
	"""
	The ``PathSpecTest`` class tests the ``PathSpec`` class.
	"""

	def test_01_current_dir_paths(self):
		"""
		Tests that paths referencing the current directory will be properly
		normalized and matched.
		"""
		spec = pathspec.PathSpec.from_lines('gitwildmatch', [
			'*.txt',
			'!test1/',
		])
		results = set(spec.match_files([
			'./src/test1/a.txt',
			'./src/test1/b.txt',
			'./src/test1/c/c.txt',
			'./src/test2/a.txt',
			'./src/test2/b.txt',
			'./src/test2/c/c.txt',
		]))
		self.assertEqual(results, {
			'./src/test2/a.txt',
			'./src/test2/b.txt',
			'./src/test2/c/c.txt',
		})

	def test_01_match_files(self):
		"""
		Tests that matching files one at a time yields the same results as
		matching multiples files at once.
		"""
		spec = pathspec.PathSpec.from_lines('gitwildmatch', [
			'*.txt',
			'!test1/',
		])
		test_files = [
			'src/test1/a.txt',
			'src/test1/b.txt',
			'src/test1/c/c.txt',
			'src/test2/a.txt',
			'src/test2/b.txt',
			'src/test2/c/c.txt',
		]
		single_results = set(filter(spec.match_file, test_files))
		multi_results = set(spec.match_files(test_files))
		self.assertEqual(single_results, multi_results)

	def test_01_windows_current_dir_paths(self):
		"""
		Tests that paths referencing the current directory will be properly
		normalized and matched.
		"""
		spec = pathspec.PathSpec.from_lines('gitwildmatch', [
			'*.txt',
			'!test1/',
		])
		results = set(spec.match_files([
			'.\\src\\test1\\a.txt',
			'.\\src\\test1\\b.txt',
			'.\\src\\test1\\c\\c.txt',
			'.\\src\\test2\\a.txt',
			'.\\src\\test2\\b.txt',
			'.\\src\\test2\\c\\c.txt',
		], separators=('\\',)))
		self.assertEqual(results, {
			'.\\src\\test2\\a.txt',
			'.\\src\\test2\\b.txt',
			'.\\src\\test2\\c\\c.txt',
		})

	def test_01_windows_paths(self):
		"""
		Tests that Windows paths will be properly normalized and matched.
		"""
		spec = pathspec.PathSpec.from_lines('gitwildmatch', [
			'*.txt',
			'!test1/',
		])
		results = set(spec.match_files([
			'src\\test1\\a.txt',
			'src\\test1\\b.txt',
			'src\\test1\\c\\c.txt',
			'src\\test2\\a.txt',
			'src\\test2\\b.txt',
			'src\\test2\\c\\c.txt',
		], separators=('\\',)))
		self.assertEqual(results, {
			'src\\test2\\a.txt',
			'src\\test2\\b.txt',
			'src\\test2\\c\\c.txt',
		})

	def test_02_eq(self):
		"""
		Tests equality.
		"""
		first_spec = pathspec.PathSpec.from_lines('gitwildmatch', [
			'*.txt',
			'!test1/',
		])
		second_spec = pathspec.PathSpec.from_lines('gitwildmatch', [
			'*.txt',
			'!test1/',
		])
		self.assertEqual(first_spec, second_spec)

	def test_02_ne(self):
		"""
		Tests equality.
		"""
		first_spec = pathspec.PathSpec.from_lines('gitwildmatch', [
			'*.txt',
		])
		second_spec = pathspec.PathSpec.from_lines('gitwildmatch', [
			'!*.txt',
		])
		self.assertNotEqual(first_spec, second_spec)
