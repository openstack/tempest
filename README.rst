::

OpenStack integration test suite
================================

This is a set of integration tests to be run against a live cluster.

Quickstart
----------

You're going to want to make your own config.ini file in the /etc/ directory,
it needs to point at your running cluster.

After that try commands such as::

  run_tests.sh --nova
  run_tests.sh --glance
  run_tests.sh --swift


Additional Info
---------------

There are additional README files in the various subdirectories of this project.
