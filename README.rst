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

    If you have a running devstack environment, Tempest will be
    automatically configured and placed in ``/opt/stack/tempest``. It
    will have a configuration file already set up to work with your
    devstack installation.

Tempest is not tied to any single test runner, but `testr`_ is the most commonly
used tool. Also, the nosetests test runner is **not** recommended to run Tempest.

After setting up your configuration file, you can execute the set of Tempest
tests by using ``testr`` ::

    $> testr run --parallel

.. _testr: http://testrepository.readthedocs.org/en/latest/MANUAL.html

To run one single test serially ::

    $> testr run tempest.api.compute.servers.test_servers_negative.ServersNegativeTestJSON.test_reboot_non_existent_server

Alternatively, you can use the run_tempest.sh script which will create a venv
and run the tests or use tox to do the same. Tox also contains several existing
job configurations. For example::

   $> tox -efull

which will run the same set of tests as the OpenStack gate. (it's exactly how
the gate invokes Tempest) Or::

  $> tox -esmoke

to run the tests tagged as smoke.


Configuration
-------------

Detailed configuration of Tempest is beyond the scope of this
document see :ref:`tempest-configuration` for more details on configuring
Tempest. The etc/tempest.conf.sample attempts to be a self documenting version
of the configuration.

You can generate a new sample tempest.conf file, run the following
command from the top level of the Tempest directory:

  tox -egenconfig

The most important pieces that are needed are the user ids, openstack
endpoint, and basic flavors and images needed to run tests.

Unit Tests
----------

Tempest also has a set of unit tests which test the Tempest code itself. These
tests can be run by specifing the test discovery path::

    $> OS_TEST_PATH=./tempest/tests testr run --parallel

By setting OS_TEST_PATH to ./tempest/tests it specifies that test discover
should only be run on the unit test directory. The default value of OS_TEST_PATH
is OS_TEST_PATH=./tempest/test_discover which will only run test discover on the
Tempest suite.

Alternatively, you can use the run_tests.sh script which will create a venv and
run the unit tests. There are also the py26, py27, or py33 tox jobs which will
run the unit tests with the corresponding version of python.

Python 2.6
----------

Starting in the kilo release the OpenStack services dropped all support for
python 2.6. This change has been mirrored in Tempest, starting after the
tempest-2 tag. This means that proposed changes to Tempest which only fix
python 2.6 compatibility will be rejected, and moving forward more features not
present in python 2.6 will be used. If you're running your OpenStack services
on an earlier release with python 2.6 you can easily run Tempest against it
from a remote system running python 2.7. (or deploy a cloud guest in your cloud
that has python 2.7)
