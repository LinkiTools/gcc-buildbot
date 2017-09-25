#  Buildbot script to run on the master.
# This script is used on the master to commit
# data from a build into influx using the command
# line.

# It receives a single file with line protocol data
# Commmits it into influx one by one.

# Usage:
# python commit-influx-data.py \
#        --db <influx-db>
#        <datafile>

import click
import plumbum
import sys

@click.command()
@click.option('--db', default='gcc_buildbot')
@click.argument('datafile')
def commit(db, datafile):
    if not os.path.exists(datafile):
        print('Whoops, data file does not exist: {}'
              .format(datafile))
        sys.exit(1)

    influx = plumbum.local('influx')
    with open(datafile) as data:
        for line in data:
            try:
                influx('-database', db
                       '-execute', 'INSERT {}'.format(line))
            except ProcessExecutionError:
                print('Influx failed executing: {}'
                      .format(line))
                sys.exit(1)

    sys.exit(0)

if __name__ == '__main__':
    commit()
