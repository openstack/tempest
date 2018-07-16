.. _tempest_test_writing:

Tempest Test Writing Guide
##########################

This guide serves as a starting point for developers working on writing new
Tempest tests. At a high level, tests in Tempest are just tests that conform to
the standard python `unit test`_ framework. But there are several aspects of
that are unique to Tempest and its role as an integration test suite running
against a real cloud.

.. _unit test: https://docs.python.org/3.6/library/unittest.html

.. note:: This guide is for writing tests in the Tempest repository. While many
          parts of this guide are also applicable to Tempest plugins, not all
          the APIs mentioned are considered stable or recommended for use in
          plugins. Please refer to :ref:`tempest_plugin` for details about
          writing plugins


Adding a New TestCase
=====================

The base unit of testing in Tempest is the `TestCase`_ (also called the test
class). Each TestCase contains test methods which are the individual tests that
will be executed by the test runner. But, the TestCase is the smallest self
contained unit for tests from the Tempest perspective. It's also the level at
which Tempest is parallel safe. In other words, multiple TestCases can be
executed in parallel, but individual test methods in the same TestCase can not.
Also, all test methods within a TestCase are assumed to be executed serially. As
such you can use the test case to store variables that are shared between
methods.

.. _TestCase: https://docs.python.org/3.6/library/unittest.html#unittest.TestCase

In standard unittest the lifecycle of a TestCase can be described in the
following phases:

#. setUpClass
#. setUp
#. Test Execution
#. tearDown
#. doCleanups
#. tearDownClass

setUpClass
----------

The setUpClass phase is the first phase executed by the test runner and is used
to perform any setup required for all the test methods to be executed. In
Tempest this is a very important step and will automatically do the necessary
setup for interacting with the configured cloud.

To accomplish this you do **not** define a setUpClass function, instead there
are a number of predefined phases to setUpClass that are used. The phases are:

* skip_checks
* setup_credentials
* setup_clients
* resource_setup

which is executed in that order. Cleanup of resources provisioned during
the resource_setup must be scheduled right after provisioning using
the addClassResourceCleanup helper. The resource cleanups stacked this way
are executed in reverse order during tearDownClass, before the cleanup of
test credentials takes place. An example of a TestCase which defines all
of these would be::

  from tempest.common import waiters
  from tempest import config
  from tempest.lib.common.utils import test_utils
  from tempest import test

  CONF = config.CONF


  class TestExampleCase(test.BaseTestCase):

    @classmethod
    def skip_checks(cls):
        """This section is used to evaluate config early and skip all test
           methods based on these checks
        """
        super(TestExampleCase, cls).skip_checks()
        if not CONF.section.foo
            cls.skip('A helpful message')

    @classmethod
    def setup_credentials(cls):
        """This section is used to do any manual credential allocation and also
           in the case of dynamic credentials to override the default network
           resource creation/auto allocation
        """
        # This call is used to tell the credential allocator to not create any
        # network resources for this test case. It also enables selective
        # creation of other neutron resources. NOTE: it must go before the
        # super call
        cls.set_network_resources()
        super(TestExampleCase, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        """This section is used to setup client aliases from the manager object
           or to initialize any additional clients. Except in a few very
           specific situations you should not need to use this.
        """
        super(TestExampleCase, cls).setup_clients()
        cls.servers_client = cls.os_primary.servers_client

    @classmethod
    def resource_setup(cls):
        """This section is used to create any resources or objects which are
           going to be used and shared by **all** test methods in the
           TestCase. Note then anything created in this section must also be
           destroyed in the corresponding resource_cleanup() method (which will
           be run during tearDownClass())
        """
        super(TestExampleCase, cls).resource_setup()
        cls.shared_server = cls.servers_client.create_server(...)
        cls.addClassResourceCleanup(waiters.wait_for_server_termination,
                                    cls.servers_client,
                                    cls.shared_server['id'])
        cls.addClassResourceCleanup(
            test_utils.call_and_ignore_notfound_exc(
                cls.servers_client.delete_server,
                cls.shared_server['id']))

.. _credentials:

Allocating Credentials
''''''''''''''''''''''

Since Tempest tests are all about testing a running cloud, every test will need
credentials to be able to make API requests against the cloud. Since this is
critical to operation and, when running in parallel, easy to make a mistake,
the base TestCase class will automatically allocate a regular user for each
TestCase during the setup_credentials() phase. During this process it will also
initialize a client manager object using those credentials, which will be your
entry point into interacting with the cloud. For more details on how credentials
are allocated the :ref:`tempest_cred_provider_conf` section of the Tempest
Configuration Guide provides more details on the operation of this.

There are some cases when you need more than a single set of credentials, or
credentials with a more specialized set of roles. To accomplish this you have
to set a class variable ``credentials`` on the TestCase directly. For example::

    from tempest import test

    class TestExampleAdmin(test.BaseTestCase):

        credentials = ['primary', 'admin']

    @classmethod
    def skip_checks(cls):
    ...

In this example the ``TestExampleAdmin`` TestCase will allocate 2 sets of
credentials, one regular user and one admin user. The corresponding manager
objects will be set as class variables ``cls.os_primary`` and ``cls.os_admin``
respectively. You can also allocate a second user by putting **'alt'** in the
list too. A set of alt credentials are the same as primary but can be used
for tests cases that need a second user/project.

You can also specify credentials with specific roles assigned. This is useful
for cases where there are specific RBAC requirements hard coded into an API.
The canonical example of this are swift tests which often want to test swift's
concepts of operator and reseller_admin. An actual example from Tempest on how
to do this is::

    class PublicObjectTest(base.BaseObjectTest):

        credentials = [['operator', CONF.object_storage.operator_role],
                       ['operator_alt', CONF.object_storage.operator_role]]

        @classmethod
        def setup_credentials(cls):
            super(PublicObjectTest, cls).setup_credentials()
            ...

In this case the manager objects will be set to ``cls.os_roles_operator`` and
``cls.os_roles_operator_alt`` respectively.


There is no limit to how many credentials you can allocate in this manner,
however in almost every case you should **not** need more than 3 sets of
credentials per test case.

To figure out the mapping of manager objects set on the TestCase and the
requested credentials you can reference:

+-------------------+---------------------+
| Credentials Entry | Manager Variable    |
+===================+=====================+
| primary           | cls.os_primary      |
+-------------------+---------------------+
| admin             | cls.os_admin        |
+-------------------+---------------------+
| alt               | cls.os_alt          |
+-------------------+---------------------+
| [$label, $role]   | cls.os_roles_$label |
+-------------------+---------------------+

By default cls.os_primary is available since it is allocated in the base Tempest test
class (located in tempest/test.py). If your TestCase inherits from a different
direct parent class (it'll still inherit from the BaseTestCase, just not
directly) be sure to check if that class overrides allocated credentials.

Dealing with Network Allocation
'''''''''''''''''''''''''''''''

When Neutron is enabled and a testing requires networking this isn't normally
automatically setup when a tenant is created. Since Tempest needs isolated
tenants to function properly it also needs to handle network allocation. By
default the base test class will allocate a network, subnet, and router
automatically (this depends on the configured credential provider, for more
details see: :ref:`tempest_conf_network_allocation`). However, there are
situations where you do no need all of these resources allocated (or your
TestCase inherits from a class that overrides the default in tempest/test.py).
There is a class level mechanism to override this allocation and specify which
resources you need. To do this you need to call `cls.set_network_resources()`
in the `setup_credentials()` method before the `super()`. For example::

  from tempest import test


  class TestExampleCase(test.BaseTestCase):

  @classmethod
  def setup_credentials(cls):
      cls.set_network_resources(network=True, subnet=True, router=False)
      super(TestExampleCase, cls).setup_credentials()

There are 2 quirks with the usage here. First for the set_network_resources
function to work properly it **must be called before super()**. This is so
that children classes' settings are always used instead of a parent classes'.
The other quirk here is that if you do not want to allocate any network
resources for your test class simply call `set_network_resources()` without
any arguments. For example::

  from tempest import test


  class TestExampleCase(test.BaseTestCase):

  @classmethod
  def setup_credentials(cls):
      cls.set_network_resources()
      super(TestExampleCase, cls).setup_credentials()

This will not allocate any networking resources. This is because by default all
the arguments default to False.

It's also worth pointing out that it is common for base test classes for
different services (and scenario tests) to override this setting. When
inheriting from classes other than the base TestCase in tempest/test.py it is
worth checking the immediate parent for what is set to determine if your
class needs to override that setting.

Interacting with Credentials and Clients
========================================

Once you have your basic TestCase setup you'll want to start writing tests. To
do that you need to interact with an OpenStack deployment. This section will
cover how credentials and clients are used inside of Tempest tests.


Manager Objects
---------------

The primary interface with which you interact with both credentials and
API clients is the client manager object. These objects are created
automatically by the base test class as part of credential setup (for more
details see the previous :ref:`credentials` section). Each manager object is
initialized with a set of credentials and has each client object already setup
to use that set of credentials for making all the API requests. Each client is
accessible as a top level attribute on the manager object. So to start making
API requests you just access the client's method for making that call and the
credentials are already setup for you. For example if you wanted to make an API
call to create a server in Nova::

  from tempest import test


  class TestExampleCase(test.BaseTestCase):
    def test_example_create_server(self):
      self.os_primary.servers_client.create_server(...)

is all you need to do. As described previously, in the above example the
``self.os_primary`` is created automatically because the base test class sets the
``credentials`` attribute to allocate a primary credential set and initializes
the client manager as ``self.os_primary``. This same access pattern can be used
for all of the clients in Tempest.

Credentials Objects
-------------------

In certain cases you need direct access to the credentials (the most common
use case would be an API request that takes a user or project id in the request
body). If you're in a situation where you need to access this you'll need to
access the ``credentials`` object which is allocated from the configured
credential provider in the base test class. This is accessible from the manager
object via the manager's ``credentials`` attribute. For example::

  from tempest import test


  class TestExampleCase(test.BaseTestCase):
    def test_example_create_server(self):
      credentials = self.os_primary.credentials

The credentials object provides access to all of the credential information you
would need to make API requests. For example, building off the previous
example::

  from tempest import test


  class TestExampleCase(test.BaseTestCase):
    def test_example_create_server(self):
      credentials = self.os_primary.credentials
      username = credentials.username
      user_id = credentials.user_id
      password = credentials.password
      tenant_id = credentials.tenant_id
