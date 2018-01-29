# Python class that calls script on the Master to do GCC Regression Analysis

import os
from buildbot.plugins import util, steps

class GCCRegressionAnalysis(steps.MasterShellCommand):
    """This simple step just calls a script in master that deals
    with the gory details of determining if a regression was
    detected or not."""
    name = 'Analyse test results'
    description = 'Analysing test results'
    descriptionDone = 'Analysed test results'

    def __init__(self, datadir, **kwargs):
        """Simply initialize MasterShellCommand with the arguments to call the script."""
        super().__init__(command=None, **kwargs)
        self.command = [os.path.expanduser('~/gcc-buildbot/scripts/regression-analysis.py'),
                        "--data-dir", util.Interpolate("%(kw:datadir)s", datadir=datadir),
                        "--builder", util.Property('buildername'),
                        "--branch", util.Property('branch'),
                        util.Property('got_revision')]
