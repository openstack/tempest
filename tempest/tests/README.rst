.. _unit_tests_field_guide:

Tempest Field Guide to Unit tests
=================================

What are these tests?
---------------------

Unit tests are the self checks for Tempest. They provide functional
verification and regression checking for the internal components of Tempest.
They should be used to just verify that the individual pieces of Tempest are
working as expected. They should not require an external service to be running
and should be able to run solely from the Tempest tree.

Why are these tests in Tempest?
-------------------------------
These tests exist to make sure that the mechanisms that we use inside of
Tempest are valid and remain functional. They are only here for self
validation of Tempest.


Scope of these tests
--------------------
Unit tests should not require an external service to be running or any extra
configuration to run. Any state that is required for a test should either be
mocked out or created in a temporary test directory. (see test_wrappers.py for
an example of using a temporary test directory)
