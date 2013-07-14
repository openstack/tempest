::

Tempest - The OpenStack Integration Test Suite
==============================================

This is a set of integration tests to be run against a live OpenStack
cluster. Tempest has batteries of tests for OpenStack API validation,
Scenarios, and other specific tests useful in validating an OpenStack
deployment.


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

Tempest is not tied to any single test runner, but Nose been the most commonly
used tool. After setting up your configuration file, you can execute
the set of Tempest tests by using ``nosetests`` ::
    $> nosetests tempest

To run one single test  ::
    $> nosetests -sv tempest.api.compute.servers.test_server_actions.py:
       ServerActionsTestJSON.test_rebuild_nonexistent_server

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
