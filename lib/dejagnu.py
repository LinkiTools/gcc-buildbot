#   Copyright 2014 David Malcolm <dmalcolm@redhat.com>
#   Copyright 2014 Red Hat, Inc.
#
#   This is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see
#   <http://www.gnu.org/licenses/>.
#
# Shamelessly adapted from jamais-vu by David Malcolm
# https://github.com/davidmalcolm/jamais-vu/blob/master/jv
#
import os

OUTCOMES = 'FAIL PASS XFAIL KFAIL XPASS KPASS UNTESTED UNRESOLVED UNSUPPORTED'.split()


############################################################################
# .sum and .log files
############################################################################
class DejaFile:
    """
    Output from dejagnu, either a .log or a .sum file
    """
    def __init__(self, path):
        self.path = path

        # Mapping from test name to outcome
        # e.g. from 'libffi.call/closure_fn0.c -O0 -W -Wall (test for excess errors)'
        # to 'PASS'
        self.testname_to_outcome = {}

        # Mapping from outcome to set of test names
        self.outcome_to_testnames = {}
        for outcome in OUTCOMES:
            self.outcome_to_testnames[outcome] = set()

        # Mapping from test name to line index
        self.testname_to_lineidx = {}

        # Parse the file and build the above dicts:
        for idx, line in enumerate(open(self.path)):
            for outcome in OUTCOMES:
                prefix = '{}: '.format(outcome)
                if line.startswith(prefix):
                    testname = line[len(prefix):].rstrip()
                    self.testname_to_outcome[testname] = outcome
                    self.testname_to_lineidx[testname] = idx
                    self.outcome_to_testnames[outcome].add(testname)
                    break  # OUTCOMES loop

    def find(self, testname):
        if testname in self.testname_to_outcome:
            print('{}:{}: {}: {}'
                  .format(self.path,
                          self.testname_to_lineidx[testname] + 1,
                          self.testname_to_outcome[testname],
                          testname))
            return 1
        else:
            return 0


class LogFile(DejaFile):
    """
    A .log file from dejagnu
    """
    def __init__(self, path):
        DejaFile.__init__(self, path)

    def __repr__(self):
        return 'LogFile({})'.format(self.path)


class SumFile(DejaFile):
    """
    A .sum file from dejagnu
    """
    def __init__(self, path):
        DejaFile.__init__(self, path)

        # Locate the .log file that this is a summary of:
        root, _ = os.path.splitext(path)
        self.logpath = root + '.log'

        # ...but don't parse it yet, as that's expensive:
        self.logfile = None

    def load_log_file(self):
        if not self.logfile:
            self.logfile = LogFile(self.logpath)

    def __repr__(self):
        return 'SumFile({})'.format(self.path)

    def __cmp__(self, other):
        return cmp(self.path, other.path)

    def relative_path(self, basedir):
        return os.path.relpath(self.path, basedir)

    def find(self, testname):
        count = DejaFile.find(self, testname)
        if count:
            # Also find within .log file:
            self.load_log_file()
            count += self.logfile.find(testname)

        return count

    def summarize(self, tr):
        tr.begin_section(self.path)
        for outcome in OUTCOMES:
            if self.outcome_to_testnames[outcome]:
                tr.writeln('{}: {} tests'
                           .format(outcome,
                                   len(self.outcome_to_testnames[outcome])))
        tr.end_section()


class TestRun:
    """
    A collection of .sum files (and their .log files); either
    one or more individual ones, or a directory.
    """
    def __init__(self, path):
        self.path = path
        self.sumfiles = []
        if os.path.isdir(path):
            # Locate within the directory structure:
            def visit(_, dirname, names):
                for name in sorted(names):
                    if name.endswith('.sum'):
                        sf = SumFile(os.path.join(dirname, name))
                        self.sumfiles.append(sf)
            os.path.walk(path, visit, None)
        else:
            # Locate individual file:
            if path.endswith('.sum'):
                sf = SumFile(path)
                self.sumfiles.append(sf)

    def make_dict_by_rel_path(self):
        result = {}
        for sumfile in self.sumfiles:
            result[sumfile.relative_path(self.path)] = sumfile
        return result

    def compare(self, other):
        pass

    def dump(self, tr):
        for sumfile in sorted(self.sumfiles):
            tr.begin_section(sumfile.path)
            for outcome in OUTCOMES:
                tr.begin_section('{}: {} tests'
                                 .format(outcome, len(sumfile.outcome_to_testnames[outcome])))
                for testname in sorted(sumfile.outcome_to_testnames[outcome]):
                    tr.writeln(testname)
                tr.end_section()
            tr.end_section()

    def find(self, testname):
        count = 0
        for sumfile in sorted(self.sumfiles):
            count += sumfile.find(testname)
        return count

    def summarize(self, tr):
        for sumfile in sorted(self.sumfiles):
            sumfile.summarize(tr)


############################################################################
# Various kinds of output
############################################################################
class TextReporter:
    def __init__(self):
        self.indent = 0

    def begin_section(self, title):
        self.writeln(title)
        self.writeln('-' * len(title))
        self.writeln('')
        self.indent += 1

    def end_section(self):
        self.writeln('')
        self.indent -= 1

    def writeln(self, text):
        if text == '':
            print('')
        else:
            print('{}{}'.format(' ' * self.indent, text))

############################################################################
# Command-line interface
############################################################################

# class JV(cmdln.Cmdln):
#     name = 'jv'

#     def do_compare(self, subcmd, opts, before_path, after_path):
#         """
#         Compare a "before" run to an "after" run.
#         Accepts a pair of directories, or a pair of .sum files.
#         If a pair of directories, assume that they have the same
#         underlying structure when peer-matching.
#         Returns the number of issues found (missing .sum files,
#         new failures, etc).
#         """
#         runA = TestRun(before_path)
#         runB = TestRun(after_path)
#         dict_by_rel_pathA = runA.make_dict_by_rel_path()
#         dict_by_rel_pathB = runB.make_dict_by_rel_path()
#         #print(dict_by_rel_pathA)
#         #print(dict_by_rel_pathB)
#         relpathsA = set(dict_by_rel_pathA.keys())
#         relpathsB = set(dict_by_rel_pathB.keys())

#         #print('relpathsA: %r' % relpathsA)
#         #print('relpathsB: %r' % relpathsB)

#         issue_count = 0

#         tr = TextReporter()

#         missing_relpaths = relpathsA - relpathsB
#         if missing_relpaths:
#             tr.begin_section('sum files that went away: %i'
#                              % len(missing_relpaths))
#             for relpath in sorted(missing_relpaths):
#                 dict_by_rel_pathA[relpath].summarize(tr)
#                 issue_count += 1
#             tr.end_section()

#         new_relpaths = relpathsB - relpathsA
#         if new_relpaths:
#             tr.begin_section('sum files that appeared: %i'
#                              % len(new_relpaths))
#             for relpath in sorted(new_relpaths):
#                 dict_by_rel_pathB[relpath].summarize(tr)
#                 issue_count += 1
#             tr.end_section()

#         # Compare .sum files for which there are matching peers:
#         tr.begin_section('Comparing %i common .sum files'
#                          % len(relpathsA & relpathsB))
#         for relpath in sorted(relpathsA & relpathsB):
#             tr.writeln(relpath)
#         tr.end_section()

#         for relpath in sorted(relpathsA & relpathsB):
#             sumfileA = dict_by_rel_pathA[relpath]
#             sumfileB = dict_by_rel_pathB[relpath]

#             # Compare the individual tests
#             testnamesA = set(sumfileA.testname_to_outcome.keys())
#             testnamesB = set(sumfileB.testname_to_outcome.keys())
#             missing_testnames = testnamesA - testnamesB
#             if missing_testnames:
#                 tr.begin_section('Tests that went away in %s: %i'
#                                  % (relpath, len(missing_testnames)))
#                 for testname in sorted(missing_testnames):
#                     tr.writeln('%s: %s'
#                                % (sumfileA.testname_to_outcome[testname],
#                                   testname))
#                     issue_count += 1
#                 tr.end_section()

#             new_testnames = testnamesB - testnamesA
#             if new_testnames:
#                 tr.begin_section('Tests appeared in %s: %i'
#                                  % (relpath, len(new_testnames)))
#                 for testname in sorted(new_testnames):
#                     tr.writeln('%s: %s'
#                                % (sumfileB.testname_to_outcome[testname],
#                                   testname))
#                     issue_count += 1
#                 tr.end_section()

#             # dicts mapping from testname to (before, after) outcome pair
#             changing = {}
#             for testname in sorted(testnamesA & testnamesB):
#                 outcomeA = sumfileA.testname_to_outcome[testname]
#                 outcomeB = sumfileB.testname_to_outcome[testname]
#                 if outcomeA != outcomeB:
#                     changing[testname] = (outcomeA, outcomeB)
#             if changing:
#                 tr.begin_section('Tests changing outcome in %s: %i'
#                                  % (relpath, len(changing)))
#                 for testname in sorted(changing.keys()):
#                     outcomeA, outcomeB = changing[testname]
#                     tr.writeln('%s -> %s : %s'
#                                % (outcomeA, outcomeB, testname))
#                     issue_count += 1
#                 tr.end_section()

#         if relpathsA & relpathsB and issue_count == 0:
#             tr.writeln('No differences found in %i common .sum files'
#                        % len(relpathsA & relpathsB))

#         return issue_count

#     def do_dump(self, subcmd, opts, *paths):
#         """
#         Print a dump of one or more .sum files, or directories, categorized
#         by outcome.
#         """
#         for path in paths:
#             run = TestRun(path)
#             tr = TextReporter()
#             run.dump(tr)

#     def do_find(self, subcmd, opts, testname, *paths):
#         """
#         Locate a test, by name, in the given .sum files or directories.
#         If a test is located in a .sum file, jv will also look for the
#         test in the corresponding .log file.
#         Example:
#           ./jv find \
#             "c-c++-common/Wcast-qual-1.c -std=gnu++11  (test for warnings, line 100)" \
#             testdata/control
#         Return the number of matches found
#         """
#         count = 0
#         for path in paths:
#             run = TestRun(path)
#             count += run.find(testname)
#         return count

#     def do_summarize(self, subcmd, opts, *paths):
#         """
#         Print a short summary of one or more .sum files or directories.
#         """
#         for path in paths:
#             run = TestRun(path)
#             tr = TextReporter()
#             run.summarize(tr)
