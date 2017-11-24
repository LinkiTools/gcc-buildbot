# Adding a worker

This document explains how to add a new worker to the GCC Buildbot master.

## Dependencies

* Python 3 (tested with Python 3.6);
* Python virtualenv;

## Compile Farm Setup

The setup in a compile farm machine, due to lack of privileges (and
some times lack of python3) might look slightly different than a setup
on your own machine.

In the compile farm we use `pyenv` to install a Python3 release
(namely `3.6.2`) and take it from there. 

From your compile farm home directory:
```bash
~$ curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
```

Go ahead and follow the instructions by adding this (accurate at time
of writing) to your `.bash_profile`:
```bash
export PATH="/home/pmatos/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Then source it and update `pyenv`.
```bash
~$ source .bash_profile
~$ pyenv update
~$ pyenv install 3.6.2
~$ pyenv shell 3.6.2
```

From this point onwards we have a Python `3.6.2` installation
working. We can now create a directory for the buildbot worker, create
a virtual environment to install Python dependencies and edit the
buildbot information.

```bash
~$ mkdir gcc-bbworker
~$ cd gcc-bbworker
~/gcc-bbworker$ pyenv virtualenv gcc-bbworker-env
~/gcc-bbworker$ pyenv activate gcc-bbworker-env
~/gcc-bbworker$ pip install buildbot-worker==0.9.13
```

Choose a name and password for your buildbot. Lets say you chose the
name `cf-test-x86_64` and password `LDYtYpTisHIO`, then you would use
the following command line to create the worker:
```bash
~/gcc-bbworker$ buildbot-worker create-worker -r . gcc-buildbot.linki.tools cf-test-x86_64 LDYtYpTisHIO
```

Now edit `info/host` and `info/admin`. For reference for
`gcc20.fsffrance.org`, I used at creation time:
```bash
~/gcc-bbworker$ cat info/admin
Paulo Matos <pmatos@linki.tools>
~/gcc-bbworker$ cat info/host
Compile Farm gcc20, Intel Xeon CPU X5670 2.93Ghz. 2 CPU, 12 cores, 24 threads. RAM 24105 MB. Debian
```

At this point, you need to contact me as specified below to register
the worker on master. 

Once I confirm the registration of the worker, go ahead and start it.
```bash

```

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

## Registration of worker in master

Once you completed worker creation [send me an email](mailto:pmatos@linki.tools)
with the subject "New buildbot worker". In the body of the email
please give me the buildbot name and password you used to the create
the buildbot above.

For example:
```
New buildbot:
name: FOO
pass: FOOPASS
```


