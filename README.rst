Tempest - The OpenStack Integration Test Suite
==============================================

.. image:: https://img.shields.io/pypi/v/tempest.svg
    :target: https://pypi.python.org/pypi/tempest/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/tempest.svg
    :target: https://pypi.python.org/pypi/tempest/
    :alt: Downloads

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
  or libraries.
- Tempest should not touch private or implementation specific
  interfaces. This means not directly going to the database, not
  directly hitting the hypervisors, not testing extensions not
  included in the OpenStack base. If there are some features of
  OpenStack that are not verifiable through standard interfaces, this
  should be considered a possible enhancement.
- Tempest strives for complete coverage of the OpenStack API and
  common scenarios that demonstrate a working cloud.
- Tempest drives load in an OpenStack cloud. By including a broad
  array of API and scenario tests Tempest can be reused in whole or in
  parts as load generation for an OpenStack cloud.
- Tempest should attempt to clean up after itself, whenever possible
  we should tear down resources when done.
- Tempest should be self-testing.

Quickstart
----------

To run Tempest, you first need to create a configuration file that will tell
Tempest where to find the various OpenStack services and other testing behavior
switches. Where the configuration file lives and how you interact with it
depends on how you'll be running Tempest. There are 2 methods of using Tempest.
The first, which is a newer and recommended workflow treats Tempest as a system
installed program. The second older method is to run Tempest assuming your
working dir is the actually Tempest source repo, and there are a number of
assumptions related to that. For this section we'll only cover the newer method
as it is simpler, and quicker to work with.

#. You first need to install Tempest. This is done with pip after you check out
   the Tempest repo::

    $ git clone http://git.openstack.org/openstack/tempest
    $ pip install tempest/

   This can be done within a venv, but the assumption for this guide is that
   the Tempest cli entry point will be in your shell's PATH.

#. Installing Tempest will create a /etc/tempest dir which will contain the
   sample config file packaged with Tempest. The contents of /etc/tempest will
   be copied to all local working dirs, so if there is any common configuration
   you'd like to be shared between anyone setting up local Tempest working dirs
   it's recommended that you copy or rename tempest.conf.sample to tempest.conf
   and make those changes to that file in /etc/tempest

#. Setup a local working Tempest dir. This is done by using the tempest init
   command::

    $ tempest init cloud-01

   works the same as::

    $ mkdir cloud-01 && cd cloud-01 && tempest init

   This will create a new directory for running a single Tempest configuration.
   If you'd like to run Tempest against multiple OpenStack deployments the idea
   is that you'll create a new working directory for each to maintain separate
   configuration files and local artifact storage for each.

#. Then cd into the newly created working dir and also modify the local
   config files located in the etc/ subdir created by the ``tempest init``
   command. Tempest is expecting a tempest.conf file in etc/ so if only a
   sample exists you must rename or copy it to tempest.conf before making
   any changes to it otherwise Tempest will not know how to load it.

#. Once the configuration is done you're now ready to run Tempest. This can
   be done with testr directly or any `testr`_ based test runner, like
   `ostestr`_. For example, from the working dir running::

     $ ostestr --regex '(?!.*\[.*\bslow\b.*\])(^tempest\.(api|scenario))'

   will run the same set of tests as the default gate jobs.

.. _testr: https://testrepository.readthedocs.org/en/latest/MANUAL.html
.. _ostestr: http://docs.openstack.org/developer/os-testr/

Library
-------
Tempest exposes a library interface. This interface is a stable interface and
should be backwards compatible (including backwards compatibility with the
old tempest-lib package, with the exception of the import). If you plan to
directly consume tempest in your project you should only import code from the
tempest library interface, other pieces of tempest do not have the same
stable interface and there are no guarantees on the Python API unless otherwise
stated.

For more details refer to the library documentation here: :ref:`library`

Release Versioning
------------------
Tempest's released versions are broken into 2 sets of information. Depending on
how you intend to consume tempest you might need

The version is a set of 3 numbers:

X.Y.Z

While this is almost `semver`_ like, the way versioning is handled is slightly
different:

X is used to represent the supported OpenStack releases for tempest tests
in-tree, and to signify major feature changes to tempest. It's a monotonically
increasing integer where each version either indicates a new supported OpenStack
release, the drop of support for an OpenStack release (which will coincide with
the upstream stable branch going EOL), or a major feature lands (or is removed)
from tempest.

Y.Z is used to represent library interface changes. This is treated the same
way as minor and patch versions from `semver`_ but only for the library
interface. When Y is incremented we've added functionality to the library
interface and when Z is incremented it's a bug fix release for the library.
Also note that both Y and Z are reset to 0 at each increment of X.

.. _semver: http://semver.org/

Configuration
-------------

Detailed configuration of Tempest is beyond the scope of this
document see :ref:`tempest-configuration` for more details on configuring
Tempest. The etc/tempest.conf.sample attempts to be a self-documenting version
of the configuration.

You can generate a new sample tempest.conf file, run the following
command from the top level of the Tempest directory:

  tox -egenconfig

The most important pieces that are needed are the user ids, openstack
endpoint, and basic flavors and images needed to run tests.

Unit Tests
----------

Tempest also has a set of unit tests which test the Tempest code itself. These
tests can be run by specifying the test discovery path::

    $> OS_TEST_PATH=./tempest/tests testr run --parallel

By setting OS_TEST_PATH to ./tempest/tests it specifies that test discover
should only be run on the unit test directory. The default value of OS_TEST_PATH
is OS_TEST_PATH=./tempest/test_discover which will only run test discover on the
Tempest suite.

Alternatively, you can use the run_tests.sh script which will create a venv and
run the unit tests. There are also the py27 and py34 tox jobs which will run
the unit tests with the corresponding version of python.

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

Python 3.4
----------

Starting during the Liberty release development cycle work began on enabling
Tempest to run under both Python 2.7 and Python 3.4. Tempest strives to fully
support running with Python 3.4. A gating unit test job was added to also run
Tempest's unit tests under Python 3.4. This means that the Tempest code at
least imports under Python 3.4 and things that have unit test coverage will
work on Python 3.4. However, because large parts of Tempest are self-verifying
there might be uncaught issues running on Python 3.4. So until there is a gating
job which does a full Tempest run using Python 3.4 there isn't any guarantee
that running Tempest under Python 3.4 is bug free.

Legacy run method
-----------------

The legacy method of running Tempest is to just treat the Tempest source code
as a python unittest repository and run directly from the source repo. When
running in this way you still start with a Tempest config file and the steps
are basically the same except that it expects you know where the Tempest code
lives on your system and requires a bit more manual interaction to get Tempest
running. For example, when running Tempest this way things like a lock file
directory do not get generated automatically and the burden is on the user to
create and configure that.

To start you need to create a configuration file. The easiest way to create a
configuration file is to generate a sample in the ``etc/`` directory ::

    $> cd $TEMPEST_ROOT_DIR
    $> oslo-config-generator --config-file \
        etc/config-generator.tempest.conf \
        --output-file etc/tempest.conf

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
