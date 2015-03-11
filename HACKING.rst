Tempest Coding Guide
====================

- Step 1: Read the OpenStack Style Commandments
  http://docs.openstack.org/developer/hacking/
- Step 2: Read on

Tempest Specific Commandments
------------------------------

- [T102] Cannot import OpenStack python clients in tempest/api &
         tempest/scenario tests
- [T104] Scenario tests require a services decorator
- [T105] Tests cannot use setUpClass/tearDownClass
- [T106] vim configuration should not be kept in source files.
- [T107] Check that a service tag isn't in the module path
- [N322] Method's default argument shouldn't be mutable

Test Data/Configuration
-----------------------
- Assume nothing about existing test data
- Tests should be self contained (provide their own data)
- Clean up test data at the completion of each test
- Use configuration files for values that will vary by environment


Exception Handling
------------------
According to the ``The Zen of Python`` the
``Errors should never pass silently.``
Tempest usually runs in special environment (jenkins gate jobs), in every
error or failure situation we should provide as much error related
information as possible, because we usually do not have the chance to
investigate the situation after the issue happened.

In every test case the abnormal situations must be very verbosely explained,
by the exception and the log.

In most cases the very first issue is the most important information.

Try to avoid using ``try`` blocks in the test cases, as both the ``except``
and ``finally`` blocks could replace the original exception,
when the additional operations leads to another exception.

Just letting an exception to propagate, is not a bad idea in a test case,
at all.

Try to avoid using any exception handling construct which can hide the errors
origin.

If you really need to use a ``try`` block, please ensure the original
exception at least logged.  When the exception is logged you usually need
to ``raise`` the same or a different exception anyway.

Use of ``self.addCleanup`` is often a good way to avoid having to catch
exceptions and still ensure resources are correctly cleaned up if the
test fails part way through.

Use the ``self.assert*`` methods provided by the unit test framework.
This signals the failures early on.

Avoid using the ``self.fail`` alone, its stack trace will signal
the ``self.fail`` line as the origin of the error.

Avoid constructing complex boolean expressions for assertion.
The ``self.assertTrue`` or ``self.assertFalse`` without a ``msg`` argument,
will just tell you the single boolean value, and you will not know anything
about the values used in the formula, the ``msg`` argument might be good enough
for providing more information.

Most other assert method can include more information by default.
For example ``self.assertIn`` can include the whole set.

It is recommended to use testtools matcher for the more tricky assertions.
`[doc] <http://testtools.readthedocs.org/en/latest/for-test-authors.html#matchers>`_

You can implement your own specific matcher as well.
`[doc] <http://testtools.readthedocs.org/en/latest/for-test-authors.html#writing-your-own-matchers>`_

If the test case fails you can see the related logs and the information
carried by the exception (exception class, backtrack and exception info).
This and the service logs are your only guide to finding the root cause of flaky
issues.

Test cases are independent
--------------------------
Every ``test_method`` must be callable individually and MUST NOT depends on,
any other ``test_method`` or ``test_method`` ordering.

Test cases MAY depend on commonly initialized resources/facilities, like
credentials management, testresources and so on. These facilities, MUST be able
to work even if just one ``test_method`` is selected for execution.

Service Tagging
---------------
Service tagging is used to specify which services are exercised by a particular
test method. You specify the services with the tempest.test.services decorator.
For example:

@services('compute', 'image')

Valid service tag names are the same as the list of directories in tempest.api
that have tests.

For scenario tests having a service tag is required. For the api tests service
tags are only needed if the test method makes an api call (either directly or
indirectly through another service) that differs from the parent directory
name. For example, any test that make an api call to a service other than nova
in tempest.api.compute would require a service tag for those services, however
they do not need to be tagged as compute.

Test fixtures and resources
---------------------------
Test level resources should be cleaned-up after the test execution. Clean-up
is best scheduled using `addCleanup` which ensures that the resource cleanup
code is always invoked, and in reverse order with respect to the creation
order.

Test class level resources should be defined in the `resource_setup` method of
the test class, except for any credential obtained from the credentials
provider, which should be set-up in the `setup_credentials` method.

The test base class `BaseTestCase` defines Tempest framework for class level
fixtures. `setUpClass` and `tearDownClass` are defined here and cannot be
overwritten by subclasses (enforced via hacking rule T105).

Set-up is split in a series of steps (setup stages), which can be overwritten
by test classes. Set-up stages are:
- `skip_checks`
- `setup_credentials`
- `setup_clients`
- `resource_setup`

Tear-down is also split in a series of steps (teardown stages), which are
stacked for execution only if the corresponding setup stage had been
reached during the setup phase. Tear-down stages are:
- `clear_isolated_creds` (defined in the base test class)
- `resource_cleanup`

Skipping Tests
--------------
Skipping tests should be based on configuration only. If that is not possible,
it is likely that either a configuration flag is missing, or the test should
fail rather than be skipped.
Using discovery for skipping tests is generally discouraged.

When running a test that requires a certain "feature" in the target
cloud, if that feature is missing we should fail, because either the test
configuration is invalid, or the cloud is broken and the expected "feature" is
not there even if the cloud was configured with it.

Negative Tests
--------------
Newly added negative tests should use the negative test framework. First step
is to create an interface description in a python file under
`tempest/api_schema/request/`. These descriptions consists of two important
sections for the test (one of those is mandatory):

 - A resource (part of the URL of the request): Resources needed for a test
 must be created in `setUpClass` and registered with `set_resource` e.g.:
 `cls.set_resource("server", server['id'])`

 - A json schema: defines properties for a request.

After that a test class must be added to automatically generate test scenarios
out of the given interface description::

    load_tests = test.NegativeAutoTest.load_tests

    @test.SimpleNegativeAutoTest
    class SampleTestNegativeTestJSON(<your base class>, test.NegativeAutoTest):
        _service = 'compute'
        _schema = <your schema file>

The class decorator `SimpleNegativeAutoTest` will automatically generate test
cases out of the given schema in the attribute `_schema`.

All negative tests should be added into a separate negative test file.
If such a file doesn't exist for the particular resource being tested a new
test file should be added.

Test skips because of Known Bugs
--------------------------------

If a test is broken because of a bug it is appropriate to skip the test until
bug has been fixed. You should use the skip_because decorator so that
Tempest's skip tracking tool can watch the bug status.

Example::

  @skip_because(bug="980688")
  def test_this_and_that(self):
    ...

Guidelines
----------
- Do not submit changesets with only testcases which are skipped as
  they will not be merged.
- Consistently check the status code of responses in testcases. The
  earlier a problem is detected the easier it is to debug, especially
  where there is complicated setup required.

Parallel Test Execution
-----------------------
Tempest by default runs its tests in parallel this creates the possibility for
interesting interactions between tests which can cause unexpected failures.
Tenant isolation provides protection from most of the potential race conditions
between tests outside the same class. But there are still a few of things to
watch out for to try to avoid issues when running your tests in parallel.

- Resources outside of a tenant scope still have the potential to conflict. This
  is a larger concern for the admin tests since most resources and actions that
  require admin privileges are outside of tenants.

- Races between methods in the same class are not a problem because
  parallelization in tempest is at the test class level, but if there is a json
  and xml version of the same test class there could still be a race between
  methods.

- The rand_name() function from tempest.common.utils.data_utils should be used
  anywhere a resource is created with a name. Static naming should be avoided
  to prevent resource conflicts.

- If the execution of a set of tests is required to be serialized then locking
  can be used to perform this. See AggregatesAdminTest in
  tempest.api.compute.admin for an example of using locking.

Stress Tests in Tempest
-----------------------
Any tempest test case can be flagged as a stress test. With this flag it will
be automatically discovery and used in the stress test runs. The stress test
framework itself is a facility to spawn and control worker processes in order
to find race conditions (see ``tempest/stress/`` for more information). Please
note that these stress tests can't be used for benchmarking purposes since they
don't measure any performance characteristics.

Example::

  @stresstest(class_setup_per='process')
  def test_this_and_that(self):
    ...

This will flag the test ``test_this_and_that`` as a stress test. The parameter
``class_setup_per`` gives control when the setUpClass function should be called.

Good candidates for stress tests are:

- Scenario tests
- API tests that have a wide focus

Sample Configuration File
-------------------------
The sample config file is autogenerated using a script. If any changes are made
to the config variables in tempest/config.py then the sample config file must be
regenerated. This can be done running::

  tox -egenconfig

Unit Tests
----------
Unit tests are a separate class of tests in tempest. They verify tempest
itself, and thus have a different set of guidelines around them:

1. They can not require anything running externally. All you should need to
   run the unit tests is the git tree, python and the dependencies installed.
   This includes running services, a config file, etc.

2. The unit tests cannot use setUpClass, instead fixtures and testresources
   should be used for shared state between tests.


.. _TestDocumentation:

Test Documentation
------------------
For tests being added we need to require inline documentation in the form of
docstings to explain what is being tested. In API tests for a new API a class
level docstring should be added to an API reference doc. If one doesn't exist
a TODO comment should be put indicating that the reference needs to be added.
For individual API test cases a method level docstring should be used to
explain the functionality being tested if the test name isn't descriptive
enough. For example::

    def test_get_role_by_id(self):
        """Get a role by its id."""

the docstring there is superfluous and shouldn't be added. but for a method
like::

    def test_volume_backup_create_get_detailed_list_restore_delete(self):
        pass

a docstring would be useful because while the test title is fairly descriptive
the operations being performed are complex enough that a bit more explanation
will help people figure out the intent of the test.

For scenario tests a class level docstring describing the steps in the scenario
is required. If there is more than one test case in the class individual
docstrings for the workflow in each test methods can be used instead. A good
example of this would be::

    class TestVolumeBootPattern(manager.ScenarioTest):
        """
        This test case attempts to reproduce the following steps:

         * Create in Cinder some bootable volume importing a Glance image
         * Boot an instance from the bootable volume
         * Write content to the volume
         * Delete an instance and Boot a new instance from the volume
         * Check written content in the instance
         * Create a volume snapshot while the instance is running
         * Boot an additional instance from the new snapshot based volume
         * Check written content in the instance booted from snapshot
        """

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
