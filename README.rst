::

Tempest - The OpenStack Integration Test Suite
==============================================

This is a set of integration tests to be run against a live cluster.

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

    If you have a running devstack environment, look at the
    environment variables in your ``devstack/localrc`` file.
    The ADMIN_PASSWORD variable should match the api_key value
    in the tempest.conf [nova] configuration section. In addition,
    you will need to get the UUID identifier of the image that
    devstack uploaded and set the image_ref value in the [environment]
    section in the tempest.conf to that image UUID.

    In addition, the ``<devstack-repo>/tools/configure_tempest.sh`` script can
    also be used to generate a tempest.conf based on your devstack's rc files.

Tempest is not tied to any single test runner, but Nose been the most commonly
used tool. After setting up your configuration file, you can execute
the set of Tempest tests by using ``nosetests`` ::

    $> nosetests tempest

Configuration
-------------

At present, there are three sections to be configured: nova, environment,
and image. The nova section includes information about your Keystone endpoint,
as well as valid credentials for a user. It also contains logical timeouts
for certain actions. The environment section contains reference data to be
used when testing the Compute portion of OpenStack, as well as feature flags
for tests that may or may not work based on your hypervisor or current
environment. Lastly, the image section contains credentials and endpoints for
the Glance image service.

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
