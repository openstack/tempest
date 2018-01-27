Tempest Coding Guide
====================

- Step 1: Read the OpenStack Style Commandments
  https://docs.openstack.org/hacking/latest/
- Step 2: Read on

Tempest Specific Commandments
------------------------------

- [T102] Cannot import OpenStack python clients in tempest/api &
  tempest/scenario tests
- [T104] Scenario tests require a services decorator
- [T105] Tests cannot use setUpClass/tearDownClass
- [T106] vim configuration should not be kept in source files.
- [T107] Check that a service tag isn't in the module path
- [T108] Check no hyphen at the end of rand_name() argument
- [T109] Cannot use testtools.skip decorator; instead use
  decorators.skip_because from tempest.lib
- [T110] Check that service client names of GET should be consistent
- [T111] Check that service client names of DELETE should be consistent
- [T112] Check that tempest.lib should not import local tempest code
- [T113] Check that tests use data_utils.rand_uuid() instead of uuid.uuid4()
- [T114] Check that tempest.lib does not use tempest config
- [T115] Check that admin tests should exist under admin path
- [N322] Method's default argument shouldn't be mutable
- [T116] Unsupported 'message' Exception attribute in PY3

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

It is recommended to use testtools `matcher`_ for the more tricky assertions.
You can implement your own specific `matcher`_ as well.

.. _matcher: https://testtools.readthedocs.org/en/latest/for-test-authors.html#matchers

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
test method. You specify the services with the ``tempest.common.utils.services``
decorator. For example:

@utils.services('compute', 'image')

Valid service tag names are the same as the list of directories in tempest.api
that have tests.

For scenario tests having a service tag is required. For the API tests service
tags are only needed if the test method makes an API call (either directly or
indirectly through another service) that differs from the parent directory
name. For example, any test that make an API call to a service other than Nova
in ``tempest.api.compute`` would require a service tag for those services,
however they do not need to be tagged as ``compute``.

Test fixtures and resources
---------------------------
Test level resources should be cleaned-up after the test execution. Clean-up
is best scheduled using ``addCleanup`` which ensures that the resource cleanup
code is always invoked, and in reverse order with respect to the creation
order.

Test class level resources should be defined in the ``resource_setup`` method
of the test class, except for any credential obtained from the credentials
provider, which should be set-up in the ``setup_credentials`` method.
Cleanup is best scheduled using ``addClassResourceCleanup`` which ensures that
the cleanup code is always invoked, and in reverse order with respect to the
creation order.

In both cases - test level and class level cleanups - a wait loop should be
scheduled before the actual delete of resources with an asynchronous delete.

The test base class ``BaseTestCase`` defines Tempest framework for class level
fixtures. ``setUpClass`` and ``tearDownClass`` are defined here and cannot be
overwritten by subclasses (enforced via hacking rule T105).

Set-up is split in a series of steps (setup stages), which can be overwritten
by test classes. Set-up stages are:

- ``skip_checks``
- ``setup_credentials``
- ``setup_clients``
- ``resource_setup``

Tear-down is also split in a series of steps (teardown stages), which are
stacked for execution only if the corresponding setup stage had been
reached during the setup phase. Tear-down stages are:

- ``clear_credentials`` (defined in the base test class)
- ``resource_cleanup``

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
Error handling is an important aspect of API design and usage. Negative
tests are a way to ensure that an application can gracefully handle
invalid or unexpected input. However, as a black box integration test
suite, Tempest is not suitable for handling all negative test cases, as
the wide variety and complexity of negative tests can lead to long test
runs and knowledge of internal implementation details. The bulk of
negative testing should be handled with project function tests.
All negative tests should be based on `API-WG guideline`_ . Such negative
tests can block any changes from accurate failure code to invalid one.

.. _API-WG guideline: https://specs.openstack.org/openstack/api-wg/guidelines/http.html#failure-code-clarifications

If facing some gray area which is not clarified on the above guideline, propose
a new guideline to the API-WG. With a proposal to the API-WG we will be able to
build a consensus across all OpenStack projects and improve the quality and
consistency of all the APIs.

In addition, we have some guidelines for additional negative tests.

- About BadRequest(HTTP400) case: We can add a single negative tests of
  BadRequest for each resource and method(POST, PUT).
  Please don't implement more negative tests on the same combination of
  resource and method even if API request parameters are different from
  the existing test.
- About NotFound(HTTP404) case: We can add a single negative tests of
  NotFound for each resource and method(GET, PUT, DELETE, HEAD).
  Please don't implement more negative tests on the same combination
  of resource and method.

The above guidelines don't cover all cases and we will grow these guidelines
organically over time. Patches outside of the above guidelines are left up to
the reviewers' discretion and if we face some conflicts between reviewers, we
will expand the guideline based on our discussion and experience.

Test skips because of Known Bugs
--------------------------------
If a test is broken because of a bug it is appropriate to skip the test until
bug has been fixed. You should use the ``skip_because`` decorator so that
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
Dynamic credentials provides protection from most of the potential race
conditions between tests outside the same class. But there are still a few of
things to watch out for to try to avoid issues when running your tests in
parallel.

- Resources outside of a project scope still have the potential to conflict. This
  is a larger concern for the admin tests since most resources and actions that
  require admin privileges are outside of projects.

- Races between methods in the same class are not a problem because
  parallelization in Tempest is at the test class level, but if there is a json
  and xml version of the same test class there could still be a race between
  methods.

- The rand_name() function from tempest.lib.common.utils.data_utils should be
  used anywhere a resource is created with a name. Static naming should be
  avoided to prevent resource conflicts.

- If the execution of a set of tests is required to be serialized then locking
  can be used to perform this. See usage of ``LockFixture`` for examples of
  using locking.

Sample Configuration File
-------------------------
The sample config file is autogenerated using a script. If any changes are made
to the config variables in tempest/config.py then the sample config file must be
regenerated. This can be done running::

  tox -e genconfig

Unit Tests
----------
Unit tests are a separate class of tests in Tempest. They verify Tempest
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
docstrings to explain what is being tested. In API tests for a new API a class
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

Test Identification with Idempotent ID
--------------------------------------

Every function that provides a test must have an ``idempotent_id`` decorator
that is a unique ``uuid-4`` instance. This ID is used to complement the fully
qualified test name and track test functionality through refactoring. The
format of the metadata looks like::

    @decorators.idempotent_id('585e934c-448e-43c4-acbf-d06a9b899997')
    def test_list_servers_with_detail(self):
        # The created server should be in the detailed list of all servers
        ...

Tempest.lib includes a ``check-uuid`` tool that will test for the existence
and uniqueness of idempotent_id metadata for every test. If you have
Tempest installed you run the tool against Tempest by calling from the
Tempest repo::

    check-uuid

It can be invoked against any test suite by passing a package name::

    check-uuid --package <package_name>

Tests without an ``idempotent_id`` can be automatically fixed by running
the command with the ``--fix`` flag, which will modify the source package
by inserting randomly generated uuids for every test that does not have
one::

    check-uuid --fix

The ``check-uuid`` tool is used as part of the Tempest gate job
to ensure that all tests have an ``idempotent_id`` decorator.

Branchless Tempest Considerations
---------------------------------

Starting with the OpenStack Icehouse release Tempest no longer has any stable
branches. This is to better ensure API consistency between releases because
the API behavior should not change between releases. This means that the stable
branches are also gated by the Tempest master branch, which also means that
proposed commits to Tempest must work against both the master and all the
currently supported stable branches of the projects. As such there are a few
special considerations that have to be accounted for when pushing new changes
to Tempest.

1. New Tests for new features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When adding tests for new features that were not in previous releases of the
projects the new test has to be properly skipped with a feature flag. Whether
this is just as simple as using the @utils.requires_ext() decorator to
check if the required extension (or discoverable optional API) is enabled or
adding a new config option to the appropriate section. If there isn't a method
of selecting the new **feature** from the config file then there won't be a
mechanism to disable the test with older stable releases and the new test won't
be able to merge.

2. Bug fix on core project needing Tempest changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When trying to land a bug fix which changes a tested API you'll have to use the
following procedure::

    1. Propose change to the project, get a +2 on the change even with failing
    2. Propose skip on Tempest which will only be approved after the
      corresponding change in the project has a +2 on change
    3. Land project change in master and all open stable branches (if required)
    4. Land changed test in Tempest

Otherwise the bug fix won't be able to land in the project.

Handily, `Zuul's cross-repository dependencies
<https://docs.openstack.org/infra/zuul/user/gating.html#cross-project-dependencies>`_.
can be leveraged to do without step 2 and to have steps 3 and 4 happen
"atomically". To do that, make the patch written in step 1 to depend (refer to
Zuul's documentation above) on the patch written in step 4. The commit message
for the Tempest change should have a link to the Gerrit review that justifies
that change.

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
