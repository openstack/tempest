.. _cli_field_guide:

Tempest Field Guide to CLI tests
================================


What are these tests?
---------------------
The cli tests test the various OpenStack command line interface tools
to ensure that they minimally function. The current scope is read only
operations on a cloud that are hard to test via unit tests.


Why are these tests in tempest?
-------------------------------
These tests exist here because it is extremely difficult to build a
functional enough environment in the python-\*client unit tests to
provide this kind of testing. Because we already put up a cloud in the
gate with devstack + tempest it was decided it was better to have
these as a side tree in tempest instead of another QA effort which
would split review time.


Scope of these tests
--------------------
This should stay limited to the scope of testing the cli. Functional
testing of the cloud should be elsewhere, this is about exercising the
cli code.


Example of a good test
----------------------
Tests should be isolated to a single command in one of the python
clients.

Tests should not modify the cloud.

If a test is validating the cli for bad data, it should do it with
assertRaises.

A reasonable example of an existing test is as follows::

    def test_admin_list(self):
        self.nova('list')
        self.nova('list', params='--all-tenants 1')
        self.nova('list', params='--all-tenants 0')
        self.assertRaises(subprocess.CalledProcessError,
                          self.nova,
                          'list',
                          params='--all-tenants bad')
