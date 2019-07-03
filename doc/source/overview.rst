Tempest - The OpenStack Integration Test Suite
==============================================

The documentation for Tempest is officially hosted at:
https://docs.openstack.org/tempest/latest/

This is a set of integration tests to be run against a live OpenStack
cluster. Tempest has batteries of tests for OpenStack API validation,
scenarios, and other specific tests useful in validating an OpenStack
deployment.

Team and repository tags
------------------------

.. image:: https://governance.openstack.org/tc/badges/tempest.svg
    :target: https://governance.openstack.org/tc/reference/tags/index.html

.. Change things from this point on

Design Principles
-----------------
Tempest Design Principles that we strive to live by.

- Tempest should be able to run against any OpenStack cloud, be it a
  one node DevStack install, a 20 node LXC cloud, or a 1000 node KVM
  cloud.
- Tempest should be explicit in testing features. It is easy to auto
  discover features of a cloud incorrectly, and give people an
  incorrect assessment of their cloud. Explicit is always better.
- Tempest uses OpenStack public interfaces. Tests in Tempest should
  only touch public OpenStack APIs.
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

    $ git clone https://opendev.org/openstack/tempest
    $ pip install tempest/

   This can be done within a venv, but the assumption for this guide is that
   the Tempest CLI entry point will be in your shell's PATH.

#. Installing Tempest may create a ``/etc/tempest dir``, however if one isn't
   created you can create one or use ``~/.tempest/etc`` or ``~/.config/tempest`` in
   place of ``/etc/tempest``. If none of these dirs are created Tempest will create
   ``~/.tempest/etc`` when it's needed. The contents of this dir will always
   automatically be copied to all ``etc/`` dirs in local workspaces as an initial
   setup step. So if there is any common configuration you'd like to be shared
   between local Tempest workspaces it's recommended that you pre-populate it
   before running ``tempest init``.

#. Setup a local Tempest workspace. This is done by using the tempest init
   command::

    $ tempest init cloud-01

   which also works the same as::

    $ mkdir cloud-01 && cd cloud-01 && tempest init

   This will create a new directory for running a single Tempest configuration.
   If you'd like to run Tempest against multiple OpenStack deployments the idea
   is that you'll create a new working directory for each to maintain separate
   configuration files and local artifact storage for each.

#. Then ``cd`` into the newly created working dir and also modify the local
   config files located in the ``etc/`` subdir created by the ``tempest init``
   command. Tempest is expecting a ``tempest.conf`` file in etc/ so if only a
   sample exists you must rename or copy it to tempest.conf before making
   any changes to it otherwise Tempest will not know how to load it. For
   details on configuring Tempest refer to the
   `Tempest Configuration <https://docs.openstack.org/tempest/latest/configuration.html#tempest-configuration>`_

#. Once the configuration is done you're now ready to run Tempest. This can
   be done using the `Tempest Run <https://docs.openstack.org/tempest/latest/run.html#tempest-run>`_
   command. This can be done by either
   running::

    $ tempest run

   from the Tempest workspace directory. Or you can use the ``--workspace``
   argument to run in the workspace you created regardless of your current
   working directory. For example::

    $ tempest run --workspace cloud-01

   There is also the option to use `stestr`_ directly. For example, from
   the workspace dir run::

    $ stestr run --black-regex '\[.*\bslow\b.*\]' '^tempest\.(api|scenario)'

   will run the same set of tests as the default gate jobs. Or you can
   use `unittest`_ compatible test runners such as `testr`_, `pytest`_ etc.

   Tox also contains several existing job configurations. For example::

    $ tox -e full

   which will run the same set of tests as the OpenStack gate. (it's exactly how
   the gate invokes Tempest) Or::

    $ tox -e smoke

   to run the tests tagged as smoke.

.. _unittest: https://docs.python.org/3/library/unittest.html
.. _testr: https://testrepository.readthedocs.org/en/latest/MANUAL.html
.. _stestr: https://stestr.readthedocs.org/en/latest/MANUAL.html
.. _pytest: https://docs.pytest.org/en/latest/

Library
-------
Tempest exposes a library interface. This interface is a stable interface and
should be backwards compatible (including backwards compatibility with the
old tempest-lib package, with the exception of the import). If you plan to
directly consume Tempest in your project you should only import code from the
Tempest library interface, other pieces of Tempest do not have the same
stable interface and there are no guarantees on the Python API unless otherwise
stated.

For more details refer to the `library documentation
<https://docs.openstack.org/tempest/latest/library.html#library>`_

Release Versioning
------------------
`Tempest Release Notes <https://docs.openstack.org/releasenotes/tempest>`_
shows what changes have been released on each version.

Tempest's released versions are broken into 2 sets of information. Depending on
how you intend to consume Tempest you might need

The version is a set of 3 numbers:

X.Y.Z

While this is almost `semver`_ like, the way versioning is handled is slightly
different:

X is used to represent the supported OpenStack releases for Tempest tests
in-tree, and to signify major feature changes to Tempest. It's a monotonically
increasing integer where each version either indicates a new supported OpenStack
release, the drop of support for an OpenStack release (which will coincide with
the upstream stable branch going EOL), or a major feature lands (or is removed)
from Tempest.

Y.Z is used to represent library interface changes. This is treated the same
way as minor and patch versions from `semver`_ but only for the library
interface. When Y is incremented we've added functionality to the library
interface and when Z is incremented it's a bug fix release for the library.
Also note that both Y and Z are reset to 0 at each increment of X.

.. _semver: https://semver.org/

Configuration
-------------

Detailed configuration of Tempest is beyond the scope of this
document, see `Tempest Configuration Documentation
<https://docs.openstack.org/tempest/latest/configuration.html#tempest-configuration>`_
for more details on configuring Tempest.
The ``etc/tempest.conf.sample`` attempts to be a self-documenting
version of the configuration.

You can generate a new sample tempest.conf file, run the following
command from the top level of the Tempest directory::

    $ tox -e genconfig

The most important pieces that are needed are the user ids, OpenStack
endpoints, and basic flavors and images needed to run tests.

Unit Tests
----------

Tempest also has a set of unit tests which test the Tempest code itself. These
tests can be run by specifying the test discovery path::

    $ stestr --test-path ./tempest/tests run

By setting ``--test-path`` option to ./tempest/tests it specifies that test discover
should only be run on the unit test directory. The default value of ``test_path``
is ``test_path=./tempest/test_discover`` which will only run test discover on the
Tempest suite.

Alternatively, there are the py27 and py36 tox jobs which will run the unit
tests with the corresponding version of python.

One common activity is to just run a single test, you can do this with tox
simply by specifying to just run py27 or py36 tests against a single test::

    $ tox -e py36 -- -n tempest.tests.test_microversions.TestMicroversionsTestsClass.test_config_version_none_23

Or all tests in the test_microversions.py file::

    $ tox -e py36 -- -n tempest.tests.test_microversions

You may also use regular expressions to run any matching tests::

    $ tox -e py36 -- test_microversions

Additionally, when running a single test, or test-file, the ``-n/--no-discover``
argument is no longer required, however it may perform faster if included.

For more information on these options and details about stestr, please see the
`stestr documentation <https://stestr.readthedocs.io/en/latest/MANUAL.html>`_.

Python 3.x
----------

Starting during the Pike cycle Tempest has a gating CI job that runs Tempest
with Python 3. Any Tempest release after 15.0.0 should fully support running
under Python 3 as well as Python 2.7.

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

    $ cd $TEMPEST_ROOT_DIR
    $ oslo-config-generator --config-file \
        tempest/cmd/config-generator.tempest.conf \
        --output-file etc/tempest.conf

After that, open up the ``etc/tempest.conf`` file and edit the
configuration variables to match valid data in your environment.
This includes your Keystone endpoint, a valid user and credentials,
and reference data to be used in testing.

.. note::

    If you have a running DevStack environment, Tempest will be
    automatically configured and placed in ``/opt/stack/tempest``. It
    will have a configuration file already set up to work with your
    DevStack installation.

Tempest is not tied to any single test runner, but `testr`_ is the most commonly
used tool. Also, the nosetests test runner is **not** recommended to run Tempest.

After setting up your configuration file, you can execute the set of Tempest
tests by using ``testr`` ::

    $ testr run --parallel

To run one single test serially ::

    $ testr run tempest.api.compute.servers.test_servers_negative.ServersNegativeTestJSON.test_reboot_non_existent_server
