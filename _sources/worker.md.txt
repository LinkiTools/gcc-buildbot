# Adding a worker

This document explains how to add a new worker to the GCC Buildbot master.

## Dependencies

* Python 3 (tested with Python 3.6);
* Python virtualenv;

## Setup

We are first going to create a directory, download some python
packages into a virtual environment and then create and start our
buildbot.

The initial procedure looks like this (with output hidden):
```bash
$ mkdir gcc-bbworker
$ cd gcc-bbworker
$ python -m venv bbw-venv
$ source bbw-venv/bin/activate
$ pip install buildbot-worker
```

If all was successful up until here you need now a few details:

* worker name - choose one which is different from the ones already in
  use (please see existing workers in
  the [master UI](http://gcc-buildbot.linki.tools/#/workers).);
* worker password - generate something random (you'll need to send
  this to me in plain text);

Now create the buildbot worker proper from the same directory you were
in with the active virtualenv created above.
```bash
$ buildbot-worker create-worker -r . http://gcc-buildbot.linki.tools
FOO FOOPASS
```

In the example I used `FOO` as the worker's name and `FOOPASS` as the
worker's password. At this point edit `info/admin` and `info/host`
with useful information --- this will be shown in the master's user
interface. 

Once you have done this, [send me an email](mailto:pmatos@linki.tools)
with the subject "New buildbot worker". In the body of the email
please give me the buildbot name and password you used to the create
the buildbot above.

For example:
```
New buildbot:
name: FOO
pass: FOOPASS
```


