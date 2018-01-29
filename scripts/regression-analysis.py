#! env python3

# This regression analysis file implements regression analysis for
# GCC buildbot.
#
# Most of the features come from the use of jamais-vu by David Malcolm

# Available command line:

# Options:
# --lang <name>
# Name of language to analyse regressions for.
# --data-dir <path>
# Specifies which directory stores the data. This should take the shape of:
# <data-dir>/<builder>/<lang>/<branch>/r<commit>.sum.xz
# <data-dir>/<builder>/<lang>/<branch>/r<commit>.log.xz
# --builder <string>
# This is the name of the builder used.
# --branch <string>
# Name of the branch to analyse regressions for.
# Arguments: COMMIT
# The commit to compare with.

import logging as log
import lzma
import os
import re
import tempfile
import sys

import click
import plumbum

log.basicConfig(level=log.DEBUG)


def find_previous_revision_file(datadir: str,
                                builder: str,
                                lang: str,
                                branch: str,
                                commit: int) -> int:
    """From datadir, it tries to find the commit to compare the current commit with.

    This will return, if possible, the previous commit.
    If this is the first commit, and nothing can be analysed, returns None.
    """
    path = os.path.join(datadir, builder, lang, branch)
    filename_rexp = re.compile(r'r(\d+)\.sum\.xz')
    previous = None

    for f in os.listdir(path):
        m = filename_rexp.match(f)
        if not m:
            continue

        rev = int(m.group(1))
        if rev < commit:
            if (previous and rev > previous) \
               or not previous:
                previous = rev

    return previous


@click.command()
@click.option('--data-dir')
@click.option('--builder')
@click.option('--lang')
@click.option('--branch')
@click.argument('commit', type=int)
def analyze(data_dir: str, builder: str, lang: str, branch: str, commit: int) -> int:
    """Performs analysis of the current commit against the previous one.

    Returns 0 if no regressions were found or different than 0 otherwise.
    """
    log.info('GCC Regressions Analysis starting')

    previous = find_previous_revision_file(data_dir, builder, lang, branch, commit)
    if not previous:
        log.info('Nothing to do, first commit')
        return 0

    # Transform previous and commit into filenames
    prevfile = os.path.join(data_dir, builder, lang, branch, 'r{}.sum.xz'.format(previous))
    curfile = os.path.join(data_dir, builder, lang, branch, 'r{}.sum.xz'.format(commit))

    assert os.path.exists(prevfile), \
        'File does not exist for comparison: {}'.format(prevfile)
    assert os.path.exists(curfile), \
        'File does not exist for comparison: {}'.format(curfile)

    # Unpack files
    prevtmp = tempfile.NamedTemporaryFile(suffix='.sum', delete=False)
    with lzma.open(prevfile) as f:
        prevtmp.write(f.read())
    curtmp = tempfile.NamedTemporaryFile(suffix='.sum', delete=False)
    with lzma.open(curfile) as f:
        curtmp.write(f.read())

    # OK, use jv to compare current commit to previous commit
    try:
        jv = plumbum.local['jv']
        rc, stdout, stderr = jv.run(('compare', prevtmp.name, curtmp.name), retcode=None)
    except plumbum.ProcessExecutionError:
        log.error('Cannot execute jv')
        return 1

    # TODO if rc is not zero we should probable do some investigation on why.
    print(stdout)
    log.debug(stderr)
    log.debug('jv exited with %s', rc)
    return rc

if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
    sys.exit(analyze(standalone_mode=False))
