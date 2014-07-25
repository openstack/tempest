Tempest - The OpenStack Integration Test Suite
==============================================

This is a set of integration tests to be run against a live OpenStack
cluster. Tempest has batteries of tests for OpenStack API validation,
Scenarios, and other specific tests useful in validating an OpenStack
deployment.

Design Principles
-----------------
Tempest Design Principles that we strive to live by.

- Tempest should be able to run against any OpenStack cloud, be it a
  one node devstack install, a 20 node lxc cloud, or a 1000 node kvm
  cloud.
- Tempest should be explicit in testing features. It is easy to auto
  discover features of a cloud incorrectly, and give people an
  incorrect assessment of their cloud. Explicit is always better.
- Tempest uses OpenStack public interfaces. Tests in Tempest should
  only touch public interfaces, API calls (native or 3rd party),
  public CLI or libraries.
- Tempest should not touch private or implementation specific
  interfaces. This means not directly going to the database, not
  directly hitting the hypervisors, not testing extensions not
  included in the OpenStack base. If there is some feature of
  OpenStack that is not verifiable through standard interfaces, this
  should be considered a possible enhancement.
- Tempest strives for complete coverage of the OpenStack API and
  common scenarios that demonstrate a working cloud.
- Tempest drives load in an OpenStack cloud. By including a broad
  array of API and scenario tests Tempest can be reused in whole or in
  parts as load generation for an OpenStack cloud.
- Tempest should attempt to clean up after itself, whenever possible
  we should tear down resources when done.
- Tempest should be self testing.

Quickstart
----------

To run Tempest, you first need to create a configuration file that
will tell Tempest where to find the various OpenStack services and
other testing behavior switches.

The easiest way to create a configuration file is to copy the sample
one in the ``etc/`` directory ::

    $> cd $TEMPEST_ROOT_DIR
    $> cp etc/tempest.conf.sample etc/tempest.conf

After that, open up the ``etc/tempest.conf`` file and edit the
configuration variables to match valid data in your environment.
This includes your Keystone endpoint, a valid user and credentials,
and reference data to be used in testing.

.. note::

    If you have a running devstack environment, tempest will be
    automatically configured and placed in ``/opt/stack/tempest``. It
    will have a configuration file already set up to work with your
    devstack installation.

Tempest is not tied to any single test runner, but testr is the most commonly
used tool. After setting up your configuration file, you can execute
the set of Tempest tests by using ``testr`` ::

    $> testr run --parallel

To run one single test  ::

    $> testr run --parallel tempest.api.compute.servers.test_servers_negative.ServersNegativeTestJSON.test_reboot_non_existent_server

Alternatively, you can use the run_tempest.sh script which will create a venv
and run the tests or use tox to do the same.

Configuration
-------------

Detailed configuration of tempest is beyond the scope of this
document. The etc/tempest.conf.sample attempts to be a self
documenting version of the configuration.

The sample config file is auto generated using the script:
tools/generate_sample.sh

The most important pieces that are needed are the user ids, openstack
endpoints, and basic flavors and images needed to run tests.

Common Issues
-------------

Tempest was originally designed to primarily run against a full OpenStack
deployment. Due to that focus, some issues may occur when running Tempest
against devstack.

Running Tempest, especially in parallel, against a devstack instance may
cause requests to be rate limited, which will cause unexpected failures.
Given the number of requests Tempest can make against a cluster, rate limiting
should be disabled for all test accounts.

Additionally, devstack only provides a single image which Nova can use.
For the moment, the best solution is to provide the same image uuid for
both image_ref and image_ref_alt. Tempest will skip tests as needed if it
detects that both images are the same.

Unit Tests
----------

Tempest also has a set of unit tests which test the tempest code itself. These
tests can be run by specifing the test discovery path::

    $> OS_TEST_PATH=./tempest/tests testr run --parallel

By setting OS_TEST_PATH to ./tempest/tests it specifies that test discover
should only be run on the unit test directory. The default value of OS_TEST_PATH
is OS_TEST_PATH=./tempest/test_discover which will only run test discover on the
tempest suite.

Alternatively, you can use the run_tests.sh script which will create a venv and
run the unit tests. There are also the py26, py27, or py33 tox jobs which will
run the unit tests with the corresponding version of python.

Python 2.6
----------

Tempest can be run with Python 2.6 however the unit tests and the gate
currently only run with Python 2.7, so there are no guarantees about the state
of tempest when running with Python 2.6. Additionally, to enable testr to work
with tempest using python 2.6 the discover module from the unittest-ext
project has to be patched to switch the unittest.TestSuite to use
unittest2.TestSuite instead. See:

https://code.google.com/p/unittest-ext/issues/detail?id=79

Branchless Tempest Considerations
---------------------------------

Starting with the OpenStack Icehouse release Tempest no longer has any stable
branches. This is to better ensure API consistency between releases because
the API behavior should not change between releases. This means that the stable
branches are also gated by the Tempest master branch, which also means that
proposed commits to Tempest must work against both the master and all the
currently supported stable branches of the projects. As such there are a few
special considerations that have to be accounted for when pushing new changes
to tempest.

1. New Tests for new features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When adding tests for new features that were not in previous releases of the
projects the new test has to be properly skipped with a feature flag. Whether
this is just as simple as using the @test.requires_ext() decorator to check
if the required extension (or discoverable optional API) is enabled or adding
a new config option to the appropriate section. If there isn't a method of
selecting the new **feature** from the config file then there won't be a
mechanism to disable the test with older stable releases and the new test won't
be able to merge.

2. Bug fix on core project needing Tempest changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When trying to land a bug fix which changes a tested API you'll have to use the
following procedure::

    - Propose change to the project, get a +2 on the change even with failing
    - Propose skip on Tempest which will only be approved after the
      corresponding change in the project has a +2 on change
    - Land project change in master and all open stable branches (if required)
    - Land changed test in Tempest

Otherwise the bug fix won't be able to land in the project.

3. New Tests for existing features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a test is being added for a feature that exists in all the current releases
of the projects then the only concern is that the API behavior is the same
across all the versions of the project being tested. If the behavior is not
consistent the test will not be able to merge.

API Stability
-------------

For new tests being added to Tempest the assumption is that the API being
tested is considered stable and adheres to the OpenStack API stability
guidelines. If an API is still considered experimental or in development then
it should not be tested by Tempest until it is considered stable.
