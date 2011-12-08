::

Tempest - The OpenStack Integration Test Suite
==============================================

This is a set of integration tests to be run against a live cluster.

Quickstart
----------

To run Tempest, you first need to create a configuration file that
will tell Tempest where to find the various OpenStack services and
other testing behaviour switches.

The easiest way to create a configuration file is to copy the sample
one in the ``etc/`` directory ::

    $> cd $TEMPEST_ROOT_DIR
    $> cp etc/tempest.conf.sample etc/tempest.conf

After that, open up the ``etc/tempest.conf`` file and edit the
variables to fit your test environment.

.. note::

    If you have a running devstack environment, look at the
    environment variables in your ``devstack/localrc`` file.
    The ADMIN_PASSWORD variable should match the api_key value
    in the tempest.conf [nova] configuration section. In addition,
    you will need to get the UUID identifier of the image that
    devstack uploaded and set the image_ref value in the [environment]
    section in the tempest.conf to that image UUID.

After setting up your configuration file, you can execute the set of
Tempest tests by using ``nosetests`` ::

    $> nosetests tempest
