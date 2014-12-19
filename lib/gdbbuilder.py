# Define a GDB builder of some kind.

from buildbot.process import factory
from buildbot.process.properties import WithProperties
from buildbot.schedulers.basic import SingleBranchScheduler, AnyBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.steps.shell import Compile
from buildbot.steps.shell import Configure
from buildbot.steps.shell import ShellCommand
from buildbot.steps.shell import SetPropertyFromCommand
from buildbot.steps.source.git import Git
from buildbot.changes.filter import ChangeFilter
from buildbot.steps.transfer import FileDownload
from buildbot.buildslave import BuildSlave
from gdbcommand import GdbCatSumfileCommand
from json import load
import random


## TODO:
##
## - Add comments on every function/class
## - License stuff (on all files)
## - Cross testing (needed?)
## - Improve way to store and compare testcases


class DeleteGDBBuildDir (ShellCommand):
    description = "deleting previous GDB build directory"
    descriptionDone = "deleted previous GDB build directory"
    command = ['rm', '-rf', WithProperties ("%s/build", 'builddir')]

class RandomWaitForClone (ShellCommand):
    description = "randomly waiting before git fetching"
    descriptionDone = "waited before git fetching"
    command = ['sleep', WithProperties ("%ss", 'randomWait')]

class CloneOrUpdateGDBMasterRepo (Git):
    description = "fetching GDB master sources"
    descriptionDone = "fetched GDB master sources"
    def __init__ (self):
        Git.__init__ (self,
                      repourl = 'git://sourceware.org/git/binutils-gdb.git',
                      workdir = WithProperties ("%s/../binutils-gdb-master/",
                                                'builddir'),
                      retryFetch = True,
                      mode = 'incremental')
        self.haltOnFailure = False
        self.flunkOnFailure = False

class CloneOrUpdateGDBRepo (Git):
    description = "fetching GDB sources"
    descriptionDone = "fetched GDB sources"
    def __init__ (self):
        Git.__init__ (self,
                      repourl = 'git://sourceware.org/git/binutils-gdb.git',
                      workdir = WithProperties ('%s/binutils-gdb/', 'builddir'),
                      reference = WithProperties ("%s/../binutils-gdb-master/",
                                                  'builddir'),
                      retryFetch = True)

class ConfigureGDB (Configure):
    description = "configure GDB"
    descriptionDone = "configured GDB"
    def __init__ (self, extra_conf_flags, **kwargs):
        Configure.__init__ (self, **kwargs)
        self.workdir = WithProperties ("%s", 'builddir')
        self.command = ['../binutils-gdb/configure',
                        '--enable-targets=all',
                        '--disable-binutils',
                        '--disable-ld',
                        '--disable-gold',
                        '--disable-gas',
                        '--disable-sim',
                        '--disable-gprof'] + extra_conf_flags

class CompileGDB (Compile):
    description = "compile GDB"
    descriptionDone = "compiled GDB"
    def __init__ (self, extra_make_flags = [], **kwargs):
        Compile.__init__ (self, **kwargs)
        self.workdir = WithProperties ("%s", 'builddir')
        self.command = ['make',
                        WithProperties ("-j%s", 'jobs'),
                        'all'] + extra_make_flags

class TestGDB (Compile):
    description = "testing GDB"
    descriptionDone = "tested GDB"
    def __init__ (self, extra_make_check_flags = [], test_env = {},
                  **kwargs):
        Compile.__init__ (self, **kwargs)

        self.workdir = WithProperties ("%s/build/gdb/testsuite", 'builddir')
        self.command = ['make',
                        '-k',
                        'check'] + extra_make_check_flags

        self.env = test_env
        # Needed because of dejagnu
        self.haltOnFailure = False
        self.flunkOnFailure = False



class BuildAndTestGDBFactory (factory.BuildFactory):
    ConfigureClass = ConfigureGDB
    CompileClass = CompileGDB
    TestClass = TestGDB

    extra_conf_flags = None
    extra_make_flags = None
    extra_make_check_flags = None
    test_env = None

    # Set this to false to disable parallel testing (i.e., do not use
    # FORCE_PARALLEL)
    no_test_parallel = False

    # Set this to False to disable using system's debuginfo files
    # (i.e., do not use '--with-separate-debug-dir')
    use_system_debuginfo = True

    def __init__ (self, architecture_triplet = []):
        factory.BuildFactory.__init__ (self)
        self.addStep (DeleteGDBBuildDir ())
        # Unfortunately we need to have this random wait, otherwise
        # git fetch won't work
        self.addStep (RandomWaitForClone ())
        self.addStep (CloneOrUpdateGDBMasterRepo ())
        self.addStep (CloneOrUpdateGDBRepo ())

        if not self.extra_conf_flags:
            self.extra_conf_flags = []

        if self.use_system_debuginfo:
            self.extra_conf_flags.append ('--with-separate-debug-dir=/usr/lib/debug')

        self.addStep (self.ConfigureClass (self.extra_conf_flags + architecture_triplet))

        if not self.extra_make_flags:
            self.extra_make_flags = []
        self.addStep (self.CompileClass (self.extra_make_flags))

        if not self.extra_make_check_flags:
            self.extra_make_check_flags = []
        if not self.test_env:
            self.test_env = {}

        if not self.no_test_parallel:
            self.extra_make_check_flags.append (WithProperties ("-j%s", 'jobs'))
            self.extra_make_check_flags.append ('FORCE_PARALLEL=1')

        self.addStep (self.TestClass (self.extra_make_check_flags, self.test_env))

        self.addStep (GdbCatSumfileCommand (workdir = WithProperties ('%s/build/gdb/testsuite',
                                                                      'builddir'),
                                            description = 'analyze test results'))



class RunTestGDBPlain_c64t64 (BuildAndTestGDBFactory):
    pass

class RunTestGDBPlain_c32t32 (BuildAndTestGDBFactory):
    extra_conf_flags = [ 'CFLAGS=-m32' ]
    extra_make_check_flags = [ 'RUNTESTFLAGS=--target_board unix/-m32' ]

class RunTestGDBm32_c64t32 (BuildAndTestGDBFactory):
    extra_make_check_flags = [ 'RUNTESTFLAGS=--target_board unix/-m32' ]

class RunTestGDBNativeGDBServer_c64t64 (BuildAndTestGDBFactory):
    extra_make_check_flags = [ 'RUNTESTFLAGS=--target_board native-gdbserver' ]

class RunTestGDBNativeGDBServer_c64t32 (BuildAndTestGDBFactory):
    extra_make_check_flags = [ 'RUNTESTFLAGS=--target_board native-gdbserver/-m32' ]

class RunTestGDBNativeExtendedGDBServer_c64t64 (BuildAndTestGDBFactory):
    extra_make_check_flags = [ 'RUNTESTFLAGS=--target_board native-extended-gdbserver' ]

class RunTestGDBNativeExtendedGDBServer_c64t32 (BuildAndTestGDBFactory):
    extra_make_check_flags = [ 'RUNTESTFLAGS=--target_board native-extended-gdbserver/-m32' ]

class RunTestGDBIndexBuild (BuildAndTestGDBFactory):
    extra_make_check_flags = [ WithProperties ('CC_FOR_TARGET=/bin/sh %s/binutils-gdb/gdb/contrib/cc-with-tweaks.sh -i gcc', 'builddir'),
                               WithProperties ('CXX_FOR_TARGET=/bin/sh %s/binutils-gdb/gdb/contrib/cc-with-tweaks.sh -i g++', 'builddir') ]

master_filter = ChangeFilter (branch = [ 'master' ])

def load_config (c):
    config = load (open ("lib/config.json"))
    passwd = load (open ("lib/passwords.json"))

    random.seed ()
    c['slaves'] = [BuildSlave (slave['name'], passwd[slave['name']],
                               max_builds = 1,
                               properties = { 'jobs' : slave['jobs'],
                                              'randomWait' : "%d" % random.randrange (1, 30) })
                   for slave in config['slaves']]

    c['schedulers'] = []
    for s in config['schedulers']:
        if "change_filter" in s:
            s['change_filter'] = globals ()[s['change_filter']]
        kls = globals ()[s.pop ('type')]
        s = dict (map (lambda key_value_pair : (str (key_value_pair[0]),
                                                key_value_pair[1]),
                       s.items ()))
        c['schedulers'].append (kls (**s))

    c['builders'] = []
    for b in config['builders']:
        if 'arch_triplet' in b:
            arch_triplet = [ b.pop ('arch_triplet') ]
        else:
            arch_triplet = []
        btype = b.pop ('type')
        factory = globals ()[ "RunTestGDB%s" % btype ]
        b['factory'] = factory (arch_triplet)
        c['builders'].append (b)