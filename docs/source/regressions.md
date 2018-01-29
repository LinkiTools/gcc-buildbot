# Regression Testing

One of the major issues with testing GCC is determining what is and
what is not a regression. GCC testsuite does not pass all the tests,
all the time, therefore a simple check for 0 failures does not work.

I have started a thread on this topic in the [mailing
list](https://gcc.gnu.org/ml/gcc/2017-10/msg00068.html) with lots of
interesting input. I shall try, to the best of my abilities, summarize
what was said and how the current version of buildbot is doing it.

## Buildbot regression

For the sake of the buildbot GCC test run we assume a regression is
any change in the test results that should:

1. mark the test run as failed (coloured red in the UI);
2. trigger notifications;

This is, at the moment, independent from any other regression
definition used by release maintainers that might, for example,
trigger the block of a release.

## Problems with regression checks

