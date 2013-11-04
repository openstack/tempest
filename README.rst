Tempest - The OpenStack Integration Test Suite
==============================================

This is a set of integration tests to be run against a live OpenStack
cluster. Tempest has batteries of tests for OpenStack API validation,
Scenarios, and other specific tests useful in validating an OpenStack
deployment.

Design Principles
----------
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

    $> testr run --parallel tempest

To run one single test  ::

    $> testr run --parallel tempest.api.compute.servers.test_server_actions.ServerActionsTestJSON.test_rebuild_nonexistent_server

Alternatively, you can use the run_tests.sh script which will create a venv
and run the tests or use tox to do the same.

Configuration
-------------

Detailed configuration of tempest is beyond the scope of this
document. The etc/tempest.conf.sample attempts to be a self
documenting version of the configuration.

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
