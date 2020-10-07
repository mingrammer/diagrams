"""isort.py.

Exposes a simple library to sort through imports within Python code

usage:
    SortImports(file_name)
or:
    sorted = SortImports(file_contents=file_contents).output

Copyright (C) 2013  Timothy Edmund Crosley

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import codecs
import copy
import io
import itertools
import os
import re
import sys
from collections import OrderedDict, namedtuple
from datetime import datetime
from difflib import unified_diff

from . import settings
from .finders import FindersManager
from .natural import nsorted
from .pie_slice import input


class SortImports(object):
    incorrectly_sorted = False
    skipped = False

    def __init__(self, file_path=None, file_contents=None, file_=None, write_to_stdout=False, check=False,
                 show_diff=False, settings_path=None, ask_to_apply=False, run_path='', check_skip=True,
                 extension=None, **setting_overrides):
        if not settings_path and file_path:
            settings_path = os.path.dirname(os.path.abspath(file_path))
        settings_path = settings_path or os.getcwd()

        self.config = settings.from_path(settings_path).copy()
        for key, value in setting_overrides.items():
            access_key = key.replace('not_', '').lower()
            # The sections config needs to retain order and can't be converted to a set.
            if access_key != 'sections' and type(self.config.get(access_key)) in (list, tuple):
                if key.startswith('not_'):
                    self.config[access_key] = list(set(self.config[access_key]).difference(value))
                else:
                    self.config[access_key] = list(set(self.config[access_key]).union(value))
            else:
                self.config[key] = value

        if self.config['force_alphabetical_sort']:
            self.config.update({'force_alphabetical_sort_within_sections': True,
                                'no_sections': True,
                                'lines_between_types': 1,
                                'from_first': True})

        indent = str(self.config['indent'])
        if indent.isdigit():
            indent = " " * int(indent)
        else:
            indent = indent.strip("'").strip('"')
            if indent.lower() == "tab":
                indent = "\t"
        self.config['indent'] = indent

        self.config['comment_prefix'] = self.config['comment_prefix'].strip("'").strip('"')

        self.place_imports = {}
        self.import_placements = {}
        self.remove_imports = [self._format_simplified(removal) for removal in self.config['remove_imports']]
        self.add_imports = [self._format_natural(addition) for addition in self.config['add_imports']]
        self._section_comments = ["# " + value for key, value in self.config.items() if
                                  key.startswith('import_heading') and value]

        self.file_encoding = 'utf-8'
        file_name = file_path
        self.file_path = file_path or ""
        if file_path:
            file_path = os.path.abspath(file_path)
            if check_skip:
                if run_path and file_path.startswith(run_path):
                    file_name = file_path.replace(run_path, '',  1)
                else:
                    file_name = file_path
                    run_path = ''

                if settings.should_skip(file_name, self.config, run_path):
                    self.skipped = True
                    if self.config['verbose']:
                        print("WARNING: {0} was skipped as it's listed in 'skip' setting"
                            " or matches a glob in 'skip_glob' setting".format(file_path))
                    file_contents = None
            if not self.skipped and not file_contents:
                with io.open(file_path, 'rb') as f:
                    file_encoding = coding_check(f)
                with io.open(file_path, encoding=file_encoding, newline='') as file_to_import_sort:
                    try:
                        file_contents = file_to_import_sort.read()
                        self.file_path = file_path
                        self.file_encoding = file_encoding
                        encoding_success = True
                    except UnicodeDecodeError:
                        encoding_success = False

                if not encoding_success:
                    with io.open(file_path, newline='') as file_to_import_sort:
                        try:
                            file_contents = file_to_import_sort.read()
                            self.file_path = file_path
                            self.file_encoding = file_to_import_sort.encoding
                        except UnicodeDecodeError:
                            encoding_success = False
                            file_contents = None
                            self.skipped = True
                            if self.config['verbose']:
                                print("WARNING: {} was skipped as it couldn't be opened with the given "
                                      "{} encoding or {} fallback encoding".format(file_path,
                                                                                   self.file_encoding,
                                                                                   file_to_import_sort.encoding))
        elif file_:
            try:
                file_.seek(0)
                self.file_encoding = coding_check(file_)
                file_.seek(0)
            except (io.UnsupportedOperation, IOError):
                pass
            reader = codecs.getreader(self.file_encoding)
            file_contents = reader(file_).read()

        # try to decode file_contents
        if file_contents:
            try:
                basestring
                # python 2
                need_decode = (str, bytes)
            except NameError:
                # python 3
                need_decode = bytes

            if isinstance(file_contents, need_decode):
                file_contents = file_contents.decode(coding_check(file_contents.splitlines()))

        if file_contents is None or ("isort:" + "skip_file") in file_contents:
            self.skipped = True
            self.output = None
            if write_to_stdout and file_contents:
                sys.stdout.write(file_contents)
            return

        if self.config['line_ending']:
            self.line_separator = self.config['line_ending']
        else:
            if '\r\n' in file_contents:
                self.line_separator = '\r\n'
            elif '\r' in file_contents:
                self.line_separator = '\r'
            else:
                self.line_separator = '\n'
        self.in_lines = file_contents.split(self.line_separator)
        self.original_length = len(self.in_lines)
        if (self.original_length > 1 or self.in_lines[:1] not in ([], [""])) or self.config['force_adds']:
            for add_import in self.add_imports:
                self.in_lines.append(add_import)
        self.number_of_lines = len(self.in_lines)

        if not extension:
            self.extension = file_name.split('.')[-1] if file_name else "py"
        else:
            self.extension = extension

        self.out_lines = []
        self.comments = {'from': {}, 'straight': {}, 'nested': {}, 'above': {'straight': {}, 'from': {}}}
        self.imports = OrderedDict()
        self.as_map = {}

        section_names = self.config['sections']
        self.sections = namedtuple('Sections', section_names)(*[name for name in section_names])
        for section in itertools.chain(self.sections, self.config['forced_separate']):
            self.imports[section] = {'straight': OrderedDict(), 'from': OrderedDict()}

        self.finder = FindersManager(config=self.config, sections=self.sections)

        self.index = 0
        self.import_index = -1
        self._first_comment_index_start = -1
        self._first_comment_index_end = -1
        self._parse()
        if self.import_index != -1:
            self._add_formatted_imports()
        self.length_change = len(self.out_lines) - self.original_length
        while self.out_lines and self.out_lines[-1].strip() == "":
            self.out_lines.pop(-1)
        self.out_lines.append("")
        self.output = self.line_separator.join(self.out_lines)
        if self.config['atomic']:
            try:
                compile(self._strip_top_comments(self.out_lines, self.line_separator), self.file_path, 'exec', 0, 1)
            except SyntaxError:
                self.output = file_contents
                self.incorrectly_sorted = True
                try:
                    compile(self._strip_top_comments(self.in_lines, self.line_separator), self.file_path, 'exec', 0, 1)
                    print("ERROR: {0} isort would have introduced syntax errors, please report to the project!".
                          format(self.file_path))
                except SyntaxError:
                    print("ERROR: {0} File contains syntax errors.".format(self.file_path))

                return
        if check:
            check_output = self.output
            check_against = file_contents
            if self.config['ignore_whitespace']:
                check_output = check_output.replace(self.line_separator, "").replace(" ", "").replace("\x0c", "")
                check_against = check_against.replace(self.line_separator, "").replace(" ", "").replace("\x0c", "")

            if check_output.strip() == check_against.strip():
                if self.config['verbose']:
                    print("SUCCESS: {0} Everything Looks Good!".format(self.file_path))
                return

            print("ERROR: {0} Imports are incorrectly sorted.".format(self.file_path))
            self.incorrectly_sorted = True
        if show_diff or self.config['show_diff']:
            self._show_diff(file_contents)
        elif write_to_stdout:
            if sys.version_info[0] < 3:
                self.output = self.output.encode(self.file_encoding)
            sys.stdout.write(self.output)
        elif file_name and not check:
            if self.output == file_contents:
                return

            if ask_to_apply:
                self._show_diff(file_contents)
                answer = None
                while answer not in ('yes', 'y', 'no', 'n', 'quit', 'q'):
                    answer = input("Apply suggested changes to '{0}' [y/n/q]? ".format(self.file_path)).lower()
                    if answer in ('no', 'n'):
                        return
                    if answer in ('quit', 'q'):
                        sys.exit(1)
            with io.open(self.file_path, encoding=self.file_encoding, mode='w', newline='') as output_file:
                if not self.config['quiet']:
                    print("Fixing {0}".format(self.file_path))
                output_file.write(self.output)

    @property
    def correctly_sorted(self):
        return not self.incorrectly_sorted

    def _show_diff(self, file_contents):
        for line in unified_diff(
            file_contents.splitlines(1),
            self.output.splitlines(1),
            fromfile=self.file_path + ':before',
            tofile=self.file_path + ':after',
            fromfiledate=str(datetime.fromtimestamp(os.path.getmtime(self.file_path))
                             if self.file_path else datetime.now()),
            tofiledate=str(datetime.now())
        ):
            sys.stdout.write(line)

    @staticmethod
    def _strip_top_comments(lines, line_separator):
        """Strips # comments that exist at the top of the given lines"""
        lines = copy.copy(lines)
        while lines and lines[0].startswith("#"):
            lines = lines[1:]
        return line_separator.join(lines)

    def place_module(self, module_name):
        """Tries to determine if a module is a python std import, third party import, or project code:

        if it can't determine - it assumes it is project code

        """
        return self.finder.find(module_name)

    def _get_line(self):
        """Returns the current line from the file while incrementing the index."""
        line = self.in_lines[self.index]
        self.index += 1
        return line

    @staticmethod
    def _import_type(line):
        """If the current line is an import line it will return its type (from or straight)"""
        if "isort:skip" in line:
            return
        elif line.startswith('import '):
            return "straight"
        elif line.startswith('from '):
            return "from"

    def _at_end(self):
        """returns True if we are at the end of the file."""
        return self.index == self.number_of_lines

    @staticmethod
    def _module_key(module_name, config, sub_imports=False, ignore_case=False, section_name=None):
        match = re.match(r'^(\.+)\s*(.*)', module_name)
        if match:
            sep = ' ' if config['reverse_relative'] else '_'
            module_name = sep.join(match.groups())

        prefix = ""
        if ignore_case:
            module_name = str(module_name).lower()
        else:
            module_name = str(module_name)

        if sub_imports and config['order_by_type']:
            if module_name.isupper() and len(module_name) > 1:
                prefix = "A"
            elif module_name[0:1].isupper():
                prefix = "B"
            else:
                prefix = "C"
        if not config['case_sensitive']:
            module_name = module_name.lower()
        if section_name is None or 'length_sort_' + str(section_name).lower() not in config:
            length_sort = config['length_sort']
        else:
            length_sort = config['length_sort_' + str(section_name).lower()]
        return "{0}{1}{2}".format(module_name in config['force_to_top'] and "A" or "B", prefix,
                                  length_sort and (str(len(module_name)) + ":" + module_name) or module_name)

    def _add_comments(self, comments, original_string=""):
        """
            Returns a string with comments added if ignore_comments is not set.
        """

        if not self.config['ignore_comments']:
            return comments and "{0}{1} {2}".format(self._strip_comments(original_string)[0],
                                                    self.config['comment_prefix'],
                                                    "; ".join(comments)) or original_string

        return comments and self._strip_comments(original_string)[0]

    def _wrap(self, line):
        """
            Returns an import wrapped to the specified line-length, if possible.
        """
        wrap_mode = self.config['multi_line_output']
        if len(line) > self.config['line_length'] and wrap_mode != settings.WrapModes.NOQA:
            line_without_comment = line
            comment = None
            if '#' in line:
                line_without_comment, comment = line.split('#', 1)
            for splitter in ("import ", ".", "as "):
                exp = r"\b" + re.escape(splitter) + r"\b"
                if re.search(exp, line_without_comment) and not line_without_comment.strip().startswith(splitter):
                    line_parts = re.split(exp, line_without_comment)
                    if comment:
                        line_parts[-1] = '{0}#{1}'.format(line_parts[-1], comment)
                    next_line = []
                    while (len(line) + 2) > (self.config['wrap_length'] or self.config['line_length']) and line_parts:
                        next_line.append(line_parts.pop())
                        line = splitter.join(line_parts)
                    if not line:
                        line = next_line.pop()

                    cont_line = self._wrap(self.config['indent'] + splitter.join(next_line).lstrip())
                    if self.config['use_parentheses']:
                        if splitter == "as ":
                            output = "{0}{1}{2}".format(line, splitter, cont_line.lstrip())
                        else:
                            output = "{0}{1}({2}{3}{4}{5})".format(
                                line, splitter, self.line_separator, cont_line,
                                "," if self.config['include_trailing_comma'] else "",
                                self.line_separator if wrap_mode in (settings.WrapModes.VERTICAL_HANGING_INDENT,
                                                                     settings.WrapModes.VERTICAL_GRID_GROUPED)
                                else "")
                        lines = output.split(self.line_separator)
                        if self.config['comment_prefix'] in lines[-1] and lines[-1].endswith(')'):
                            line, comment = lines[-1].split(self.config['comment_prefix'], 1)
                            lines[-1] = line + ')' + self.config['comment_prefix'] + comment[:-1]
                        return self.line_separator.join(lines)
                    return "{0}{1}\\{2}{3}".format(line, splitter, self.line_separator, cont_line)
        elif len(line) > self.config['line_length'] and wrap_mode == settings.WrapModes.NOQA:
            if "# NOQA" not in line:
                return "{0}{1} NOQA".format(line, self.config['comment_prefix'])

        return line

    def _add_straight_imports(self, straight_modules, section, section_output):
        for module in straight_modules:
            if module in self.remove_imports:
                continue

            if module in self.as_map:
                import_definition = ''
                if self.config['keep_direct_and_as_imports']:
                    import_definition = "import {0}\n".format(module)
                import_definition += "import {0} as {1}".format(module, self.as_map[module])
            else:
                import_definition = "import {0}".format(module)

            comments_above = self.comments['above']['straight'].pop(module, None)
            if comments_above:
                section_output.extend(comments_above)
            section_output.append(self._add_comments(self.comments['straight'].get(module), import_definition))

    def _add_from_imports(self, from_modules, section, section_output, ignore_case):
        for module in from_modules:
            if module in self.remove_imports:
                continue

            import_start = "from {0} import ".format(module)
            from_imports = list(self.imports[section]['from'][module])
            if not self.config['no_inline_sort'] or self.config['force_single_line']:
                from_imports = nsorted(from_imports, key=lambda key: self._module_key(key, self.config, True, ignore_case, section_name=section))
            if self.remove_imports:
                from_imports = [line for line in from_imports if not "{0}.{1}".format(module, line) in
                                self.remove_imports]

            sub_modules = ['{0}.{1}'.format(module, from_import) for from_import in from_imports]
            as_imports = {
                from_import: "{0} as {1}".format(from_import, self.as_map[sub_module])
                for from_import, sub_module in zip(from_imports, sub_modules)
                if sub_module in self.as_map
            }
            if self.config['combine_as_imports'] and not ("*" in from_imports and self.config['combine_star']):
                for from_import in copy.copy(from_imports):
                    if from_import in as_imports:
                        from_imports[from_imports.index(from_import)] = as_imports.pop(from_import)

            while from_imports:
                comments = self.comments['from'].pop(module, ())
                if "*" in from_imports and self.config['combine_star']:
                    import_statement = self._wrap(self._add_comments(comments, "{0}*".format(import_start)))
                    from_imports = None
                elif self.config['force_single_line']:
                    import_statements = []
                    while from_imports:
                        from_import = from_imports.pop(0)
                        if from_import in as_imports:
                            from_comments = self.comments['straight'].get('{}.{}'.format(module, from_import))
                            import_statements.append(self._add_comments(from_comments,
                                                     self._wrap(import_start + as_imports[from_import])))
                            continue
                        single_import_line = self._add_comments(comments, import_start + from_import)
                        comment = self.comments['nested'].get(module, {}).pop(from_import, None)
                        if comment:
                            single_import_line += "{0} {1}".format(comments and ";" or self.config['comment_prefix'],
                                                                   comment)
                        import_statements.append(self._wrap(single_import_line))
                        comments = None
                    import_statement = self.line_separator.join(import_statements)
                else:
                    while from_imports and from_imports[0] in as_imports:
                        from_import = from_imports.pop(0)
                        from_comments = self.comments['straight'].get('{}.{}'.format(module, from_import))
                        above_comments = self.comments['above']['from'].pop(module, None)
                        if above_comments:
                            section_output.extend(above_comments)

                        section_output.append(self._add_comments(from_comments,
                                                                 self._wrap(import_start + as_imports[from_import])))

                    star_import = False
                    if "*" in from_imports:
                        section_output.append(self._add_comments(comments, "{0}*".format(import_start)))
                        from_imports.remove('*')
                        star_import = True
                        comments = None

                    for from_import in copy.copy(from_imports):
                        if from_import in as_imports:
                            continue
                        comment = self.comments['nested'].get(module, {}).pop(from_import, None)
                        if comment:
                            single_import_line = self._add_comments(comments, import_start + from_import)
                            single_import_line += "{0} {1}".format(comments and ";" or self.config['comment_prefix'],
                                                                   comment)
                            above_comments = self.comments['above']['from'].pop(module, None)
                            if above_comments:
                                section_output.extend(above_comments)
                            section_output.append(self._wrap(single_import_line))
                            from_imports.remove(from_import)
                            comments = None

                    from_import_section = []
                    while from_imports and from_imports[0] not in as_imports:
                        from_import_section.append(from_imports.pop(0))
                    if star_import:
                        import_statement = import_start + (", ").join(from_import_section)
                    else:
                        import_statement = self._add_comments(comments, import_start + (", ").join(from_import_section))
                    if not from_import_section:
                        import_statement = ""

                    do_multiline_reformat = False

                    force_grid_wrap = self.config['force_grid_wrap']
                    if force_grid_wrap and len(from_import_section) >= force_grid_wrap:
                        do_multiline_reformat = True

                    if len(import_statement) > self.config['line_length'] and len(from_import_section) > 1:
                        do_multiline_reformat = True

                    # If line too long AND have imports AND we are NOT using GRID or VERTICAL wrap modes
                    if (len(import_statement) > self.config['line_length'] and len(from_import_section) > 0 and
                            self.config['multi_line_output'] not in (1, 0)):
                        do_multiline_reformat = True

                    if do_multiline_reformat:
                        import_statement = self._multi_line_reformat(import_start, from_import_section, comments)
                        if self.config['multi_line_output'] == 0:
                            self.config['multi_line_output'] = 4
                            try:
                                other_import_statement = self._multi_line_reformat(import_start, from_import_section, comments)
                                if (max(len(x)
                                        for x in import_statement.split('\n')) > self.config['line_length']):
                                    import_statement = other_import_statement
                            finally:
                                self.config['multi_line_output'] = 0
                    if not do_multiline_reformat and len(import_statement) > self.config['line_length']:
                        import_statement = self._wrap(import_statement)

                if import_statement:
                    above_comments = self.comments['above']['from'].pop(module, None)
                    if above_comments:
                        section_output.extend(above_comments)
                    section_output.append(import_statement)

    def _multi_line_reformat(self, import_start, from_imports, comments):
        output_mode = settings.WrapModes._fields[self.config['multi_line_output']].lower()
        formatter = getattr(self, "_output_" + output_mode, self._output_grid)
        dynamic_indent = " " * (len(import_start) + 1)
        indent = self.config['indent']
        line_length = self.config['wrap_length'] or self.config['line_length']
        import_statement = formatter(import_start, copy.copy(from_imports),
                                     dynamic_indent, indent, line_length, comments)
        if self.config['balanced_wrapping']:
            lines = import_statement.split(self.line_separator)
            line_count = len(lines)
            if len(lines) > 1:
                minimum_length = min(len(line) for line in lines[:-1])
            else:
                minimum_length = 0
            new_import_statement = import_statement
            while (len(lines[-1]) < minimum_length and
                    len(lines) == line_count and line_length > 10):
                import_statement = new_import_statement
                line_length -= 1
                new_import_statement = formatter(import_start, copy.copy(from_imports),
                                                dynamic_indent, indent, line_length, comments)
                lines = new_import_statement.split(self.line_separator)
        if import_statement.count(self.line_separator) == 0:
            return self._wrap(import_statement)
        return import_statement

    def _add_formatted_imports(self):
        """Adds the imports back to the file.

        (at the index of the first import) sorted alphabetically and split between groups

        """
        sort_ignore_case = self.config['force_alphabetical_sort_within_sections']
        sections = itertools.chain(self.sections, self.config['forced_separate'])

        if self.config['no_sections']:
            self.imports['no_sections'] = {'straight': [], 'from': {}}
            for section in sections:
                self.imports['no_sections']['straight'].extend(self.imports[section].get('straight', []))
                self.imports['no_sections']['from'].update(self.imports[section].get('from', {}))
            sections = ('no_sections', )

        output = []
        pending_lines_before = False
        for section in sections:
            straight_modules = self.imports[section]['straight']
            straight_modules = nsorted(straight_modules, key=lambda key: self._module_key(key, self.config, section_name=section))
            from_modules = self.imports[section]['from']
            from_modules = nsorted(from_modules, key=lambda key: self._module_key(key, self.config, section_name=section))

            section_output = []
            if self.config['from_first']:
                self._add_from_imports(from_modules, section, section_output, sort_ignore_case)
                if self.config['lines_between_types'] and from_modules and straight_modules:
                    section_output.extend([''] * self.config['lines_between_types'])
                self._add_straight_imports(straight_modules, section, section_output)
            else:
                self._add_straight_imports(straight_modules, section, section_output)
                if self.config['lines_between_types'] and from_modules and straight_modules:
                    section_output.extend([''] * self.config['lines_between_types'])
                self._add_from_imports(from_modules, section, section_output, sort_ignore_case)

            if self.config['force_sort_within_sections']:
                def by_module(line):
                    section = 'B'
                    if line.startswith('#'):
                        return 'AA'

                    line = re.sub('^from ', '', line)
                    line = re.sub('^import ', '', line)
                    if line.split(' ')[0] in self.config['force_to_top']:
                        section = 'A'
                    if not self.config['order_by_type']:
                        line = line.lower()
                    return '{0}{1}'.format(section, line)
                section_output = nsorted(section_output, key=by_module)

            section_name = section
            no_lines_before = section_name in self.config['no_lines_before']

            if section_output:
                if section_name in self.place_imports:
                    self.place_imports[section_name] = section_output
                    continue

                section_title = self.config.get('import_heading_' + str(section_name).lower(), '')
                if section_title:
                    section_comment = "# {0}".format(section_title)
                    if section_comment not in self.out_lines[0:1] and section_comment not in self.in_lines[0:1]:
                        section_output.insert(0, section_comment)

                if pending_lines_before or not no_lines_before:
                    output += ([''] * self.config['lines_between_sections'])

                output += section_output

                pending_lines_before = False
            else:
                pending_lines_before = pending_lines_before or not no_lines_before

        while output and output[-1].strip() == '':
            output.pop()
        while output and output[0].strip() == '':
            output.pop(0)

        output_at = 0
        if self.import_index < self.original_length:
            output_at = self.import_index
        elif self._first_comment_index_end != -1 and self._first_comment_index_start <= 2:
            output_at = self._first_comment_index_end
        self.out_lines[output_at:0] = output

        imports_tail = output_at + len(output)
        while [character.strip() for character in self.out_lines[imports_tail: imports_tail + 1]] == [""]:
            self.out_lines.pop(imports_tail)

        if len(self.out_lines) > imports_tail:
            next_construct = ""
            self._in_quote = False
            tail = self.out_lines[imports_tail:]

            for index, line in enumerate(tail):
                in_quote = self._in_quote
                if not self._skip_line(line) and line.strip():
                    if line.strip().startswith("#") and len(tail) > (index + 1) and tail[index + 1].strip():
                        continue
                    next_construct = line
                    break
                elif not in_quote:
                    parts = line.split()
                    if len(parts) >= 3 and parts[1] == '=' and "'" not in parts[0] and '"' not in parts[0]:
                        next_construct = line
                        break

            if self.config['lines_after_imports'] != -1:
                self.out_lines[imports_tail:0] = ["" for line in range(self.config['lines_after_imports'])]
            elif self.extension != "pyi" and (next_construct.startswith("def ") or
                                              next_construct.startswith("class ") or
                                              next_construct.startswith("@") or
                                              next_construct.startswith("async def")):
                self.out_lines[imports_tail:0] = ["", ""]
            else:
                self.out_lines[imports_tail:0] = [""]

        if self.place_imports:
            new_out_lines = []
            for index, line in enumerate(self.out_lines):
                new_out_lines.append(line)
                if line in self.import_placements:
                    new_out_lines.extend(self.place_imports[self.import_placements[line]])
                    if len(self.out_lines) <= index or self.out_lines[index + 1].strip() != "":
                        new_out_lines.append("")
            self.out_lines = new_out_lines

    def _output_grid(self, statement, imports, white_space, indent, line_length, comments):
        statement += "(" + imports.pop(0)
        while imports:
            next_import = imports.pop(0)
            next_statement = self._add_comments(comments, statement + ", " + next_import)
            if len(next_statement.split(self.line_separator)[-1]) + 1 > line_length:
                lines = ['{0}{1}'.format(white_space, next_import.split(" ")[0])]
                for part in next_import.split(" ")[1:]:
                    new_line = '{0} {1}'.format(lines[-1], part)
                    if len(new_line) + 1 > line_length:
                        lines.append('{0}{1}'.format(white_space, part))
                    else:
                        lines[-1] = new_line
                next_import = self.line_separator.join(lines)
                statement = (self._add_comments(comments, "{0},".format(statement)) +
                             "{0}{1}".format(self.line_separator, next_import))
                comments = None
            else:
                statement += ", " + next_import
        return statement + ("," if self.config['include_trailing_comma'] else "") + ")"

    def _output_vertical(self, statement, imports, white_space, indent, line_length, comments):
        first_import = self._add_comments(comments, imports.pop(0) + ",") + self.line_separator + white_space
        return "{0}({1}{2}{3})".format(
            statement,
            first_import,
            ("," + self.line_separator + white_space).join(imports),
            "," if self.config['include_trailing_comma'] else "",
        )

    def _output_hanging_indent(self, statement, imports, white_space, indent, line_length, comments):
        statement += imports.pop(0)
        while imports:
            next_import = imports.pop(0)
            next_statement = self._add_comments(comments, statement + ", " + next_import)
            if len(next_statement.split(self.line_separator)[-1]) + 3 > line_length:
                next_statement = (self._add_comments(comments, "{0}, \\".format(statement)) +
                                  "{0}{1}{2}".format(self.line_separator, indent, next_import))
                comments = None
            statement = next_statement
        return statement

    def _output_vertical_hanging_indent(self, statement, imports, white_space, indent, line_length, comments):
        return "{0}({1}{2}{3}{4}{5}{2})".format(
            statement,
            self._add_comments(comments),
            self.line_separator,
            indent,
            ("," + self.line_separator + indent).join(imports),
            "," if self.config['include_trailing_comma'] else "",
         )

    def _output_vertical_grid_common(self, statement, imports, white_space, indent, line_length, comments,
                                     need_trailing_char):
        statement += self._add_comments(comments, "(") + self.line_separator + indent + imports.pop(0)
        while imports:
            next_import = imports.pop(0)
            next_statement = "{0}, {1}".format(statement, next_import)
            current_line_length = len(next_statement.split(self.line_separator)[-1])
            if imports or need_trailing_char:
                # If we have more imports we need to account for a comma after this import
                # We might also need to account for a closing ) we're going to add.
                current_line_length += 1
            if current_line_length > line_length:
                next_statement = "{0},{1}{2}{3}".format(statement, self.line_separator, indent, next_import)
            statement = next_statement
        if self.config['include_trailing_comma']:
            statement += ','
        return statement

    def _output_vertical_grid(self, statement, imports, white_space, indent, line_length, comments):
        return self._output_vertical_grid_common(statement, imports, white_space, indent, line_length, comments,
                                                 True) + ")"

    def _output_vertical_grid_grouped(self, statement, imports, white_space, indent, line_length, comments):
        return self._output_vertical_grid_common(statement, imports, white_space, indent, line_length, comments,
                                                 True) + self.line_separator + ")"

    def _output_vertical_grid_grouped_no_comma(self, statement, imports, white_space, indent, line_length, comments):
        return self._output_vertical_grid_common(statement, imports, white_space, indent, line_length, comments,
                                                 False) + self.line_separator + ")"

    def _output_noqa(self, statement, imports, white_space, indent, line_length, comments):
        retval = '{0}{1}'.format(statement, ', '.join(imports))
        comment_str = ' '.join(comments)
        if comments:
            if len(retval) + len(self.config['comment_prefix']) + 1 + len(comment_str) <= line_length:
                return '{0}{1} {2}'.format(retval, self.config['comment_prefix'], comment_str)
        else:
            if len(retval) <= line_length:
                return retval
        if comments:
            if "NOQA" in comments:
                return '{0}{1} {2}'.format(retval, self.config['comment_prefix'], comment_str)
            else:
                return '{0}{1} NOQA {2}'.format(retval, self.config['comment_prefix'], comment_str)
        else:
            return '{0}{1} NOQA'.format(retval, self.config['comment_prefix'])

    @staticmethod
    def _strip_comments(line, comments=None):
        """Removes comments from import line."""
        if comments is None:
            comments = []

        new_comments = False
        comment_start = line.find("#")
        if comment_start != -1:
            comments.append(line[comment_start + 1:].strip())
            new_comments = True
            line = line[:comment_start]

        return line, comments, new_comments

    @staticmethod
    def _format_simplified(import_line):
        import_line = import_line.strip()
        if import_line.startswith("from "):
            import_line = import_line.replace("from ", "")
            import_line = import_line.replace(" import ", ".")
        elif import_line.startswith("import "):
            import_line = import_line.replace("import ", "")

        return import_line

    @staticmethod
    def _format_natural(import_line):
        import_line = import_line.strip()
        if not import_line.startswith("from ") and not import_line.startswith("import "):
            if "." not in import_line:
                return "import {0}".format(import_line)
            parts = import_line.split(".")
            end = parts.pop(-1)
            return "from {0} import {1}".format(".".join(parts), end)

        return import_line

    def _skip_line(self, line):
        skip_line = self._in_quote
        if self.index == 1 and line.startswith("#"):
            self._in_top_comment = True
            return True
        elif self._in_top_comment:
            if not line.startswith("#") or line in self._section_comments:
                self._in_top_comment = False
                self._first_comment_index_end = self.index - 1

        if '"' in line or "'" in line:
            index = 0
            if self._first_comment_index_start == -1 and (line.startswith('"') or line.startswith("'")):
                self._first_comment_index_start = self.index
            while index < len(line):
                if line[index] == "\\":
                    index += 1
                elif self._in_quote:
                    if line[index:index + len(self._in_quote)] == self._in_quote:
                        self._in_quote = False
                        if self._first_comment_index_end < self._first_comment_index_start:
                            self._first_comment_index_end = self.index
                elif line[index] in ("'", '"'):
                    long_quote = line[index:index + 3]
                    if long_quote in ('"""', "'''"):
                        self._in_quote = long_quote
                        index += 2
                    else:
                        self._in_quote = line[index]
                elif line[index] == "#":
                    break
                index += 1

        return skip_line or self._in_quote or self._in_top_comment

    def _strip_syntax(self, import_string):
        import_string = import_string.replace("_import", "[[i]]")
        for remove_syntax in ['\\', '(', ')', ',']:
            import_string = import_string.replace(remove_syntax, " ")
        import_list = import_string.split()
        for key in ('from', 'import'):
            if key in import_list:
                import_list.remove(key)
        import_string = ' '.join(import_list)
        import_string = import_string.replace("[[i]]", "_import")
        return import_string.replace("{ ", "{|").replace(" }", "|}")

    def _parse(self):
        """Parses a python file taking out and categorizing imports."""
        self._in_quote = False
        self._in_top_comment = False
        while not self._at_end():
            raw_line = line = self._get_line()
            line = line.replace("from.import ", "from . import ")
            line = line.replace("\t", " ").replace('import*', 'import *')
            line = line.replace(" .import ", " . import ")
            statement_index = self.index
            skip_line = self._skip_line(line)

            if line in self._section_comments and not skip_line:
                if self.import_index == -1:
                    self.import_index = self.index - 1
                continue

            if "isort:imports-" in line and line.startswith("#"):
                section = line.split("isort:imports-")[-1].split()[0].upper()
                self.place_imports[section] = []
                self.import_placements[line] = section

            if ";" in line:
                for part in (part.strip() for part in line.split(";")):
                    if part and not part.startswith("from ") and not part.startswith("import "):
                        skip_line = True

            import_type = self._import_type(line)
            if not import_type or skip_line:
                self.out_lines.append(raw_line)
                continue

            for line in (line.strip() for line in line.split(";")):
                import_type = self._import_type(line)
                if not import_type:
                    self.out_lines.append(line)
                    continue

                if self.import_index == -1:
                    self.import_index = self.index - 1
                nested_comments = {}
                import_string, comments, new_comments = self._strip_comments(line)
                stripped_line = [part for part in self._strip_syntax(import_string).strip().split(" ") if part]
                if import_type == "from" and len(stripped_line) == 2 and stripped_line[1] != "*" and new_comments:
                    nested_comments[stripped_line[-1]] = comments[0]

                if "(" in line.split("#")[0] and not self._at_end():
                    while not line.strip().endswith(")") and not self._at_end():
                        line, comments, new_comments = self._strip_comments(self._get_line(), comments)
                        stripped_line = self._strip_syntax(line).strip()
                        if import_type == "from" and stripped_line and " " not in stripped_line and new_comments:
                            nested_comments[stripped_line] = comments[-1]
                        import_string += self.line_separator + line
                else:
                    while line.strip().endswith("\\"):
                        line, comments, new_comments = self._strip_comments(self._get_line(), comments)

                        # Still need to check for parentheses after an escaped line
                        if "(" in line.split("#")[0] and ")" not in line.split("#")[0] and not self._at_end():
                            stripped_line = self._strip_syntax(line).strip()
                            if import_type == "from" and stripped_line and " " not in stripped_line and new_comments:
                                nested_comments[stripped_line] = comments[-1]
                            import_string += self.line_separator + line

                            while not line.strip().endswith(")") and not self._at_end():
                                line, comments, new_comments = self._strip_comments(self._get_line(), comments)
                                stripped_line = self._strip_syntax(line).strip()
                                if import_type == "from" and stripped_line and " " not in stripped_line and new_comments:
                                    nested_comments[stripped_line] = comments[-1]
                                import_string += self.line_separator + line

                        stripped_line = self._strip_syntax(line).strip()
                        if import_type == "from" and stripped_line and " " not in stripped_line and new_comments:
                            nested_comments[stripped_line] = comments[-1]
                        if import_string.strip().endswith(" import") or line.strip().startswith("import "):
                            import_string += self.line_separator + line
                        else:
                            import_string = import_string.rstrip().rstrip("\\") + " " + line.lstrip()

                if import_type == "from":
                    import_string = import_string.replace("import(", "import (")
                    parts = import_string.split(" import ")
                    from_import = parts[0].split(" ")
                    import_string = " import ".join([from_import[0] + " " + "".join(from_import[1:])] + parts[1:])

                imports = [item.replace("{|", "{ ").replace("|}", " }") for item in
                           self._strip_syntax(import_string).split()]
                if "as" in imports and (imports.index('as') + 1) < len(imports):
                    while "as" in imports:
                        index = imports.index('as')
                        if import_type == "from":
                            module = imports[0] + "." + imports[index - 1]
                            self.as_map[module] = imports[index + 1]
                        else:
                            module = imports[index - 1]
                            self.as_map[module] = imports[index + 1]
                        if not self.config['combine_as_imports']:
                            self.comments['straight'][module] = comments
                            comments = []
                        del imports[index:index + 2]
                if import_type == "from":
                    import_from = imports.pop(0)
                    placed_module = self.place_module(import_from)
                    if self.config['verbose']:
                        print("from-type place_module for %s returned %s" % (import_from, placed_module))
                    if placed_module == '':
                        print(
                            "WARNING: could not place module {0} of line {1} --"
                            " Do you need to define a default section?".format(import_from, line)
                        )
                    root = self.imports[placed_module][import_type]
                    for import_name in imports:
                        associated_comment = nested_comments.get(import_name)
                        if associated_comment:
                            self.comments['nested'].setdefault(import_from, {})[import_name] = associated_comment
                            comments.pop(comments.index(associated_comment))
                    if comments:
                        self.comments['from'].setdefault(import_from, []).extend(comments)

                    if len(self.out_lines) > max(self.import_index, self._first_comment_index_end + 1, 1) - 1:
                        last = self.out_lines and self.out_lines[-1].rstrip() or ""
                        while (last.startswith("#") and not last.endswith('"""') and not last.endswith("'''") and
                               'isort:imports-' not in last):
                            self.comments['above']['from'].setdefault(import_from, []).insert(0, self.out_lines.pop(-1))
                            if len(self.out_lines) > max(self.import_index - 1, self._first_comment_index_end + 1, 1) - 1:
                                last = self.out_lines[-1].rstrip()
                            else:
                                last = ""
                        if statement_index - 1 == self.import_index:
                            self.import_index -= len(self.comments['above']['from'].get(import_from, []))

                    if import_from not in root:
                        root[import_from] = OrderedDict()
                    root[import_from].update((module, None) for module in imports)
                else:
                    for module in imports:
                        if comments:
                            self.comments['straight'][module] = comments
                            comments = None

                        if len(self.out_lines) > max(self.import_index, self._first_comment_index_end + 1, 1) - 1:

                            last = self.out_lines and self.out_lines[-1].rstrip() or ""
                            while (last.startswith("#") and not last.endswith('"""') and not last.endswith("'''") and
                                   'isort:imports-' not in last):
                                self.comments['above']['straight'].setdefault(module, []).insert(0,
                                                                                                 self.out_lines.pop(-1))
                                if len(self.out_lines) > 0 and len(self.out_lines) != self._first_comment_index_end:
                                    last = self.out_lines[-1].rstrip()
                                else:
                                    last = ""
                            if self.index - 1 == self.import_index:
                                self.import_index -= len(self.comments['above']['straight'].get(module, []))
                        placed_module = self.place_module(module)
                        if self.config['verbose']:
                            print("else-type place_module for %s returned %s" % (module, placed_module))
                        if placed_module == '':
                            print(
                                "WARNING: could not place module {0} of line {1} --"
                                " Do you need to define a default section?".format(import_from, line)
                            )
                        self.imports[placed_module][import_type][module] = None


def coding_check(lines, default='utf-8'):

    # see https://www.python.org/dev/peps/pep-0263/
    pattern = re.compile(br'coding[:=]\s*([-\w.]+)')

    for line_number, line in enumerate(lines, 1):
        groups = re.findall(pattern, line)
        if groups:
            return groups[0].decode('ascii')
        if line_number > 2:
            break

    return default
