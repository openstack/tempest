============================
Tempest Field Guide Overview
============================

Tempest is designed to be useful for a large number of different
environments. This includes being useful for gating commits to
OpenStack core projects, being used to validate OpenStack cloud
implementations for both correctness, as well as a burn in tool for
OpenStack clouds.

As such Tempest tests come in many flavors, each with their own rules
and guidelines. Below is the overview of the Tempest repository structure
to make this clear.

.. code-block:: console

   tempest/
      api/ - API tests
      scenario/ - complex scenario tests
      tests/ - unit tests for Tempest internals

Each of these directories contains different types of tests. What
belongs in each directory, the rules and examples for good tests, are
documented in a README.rst file in the directory.

:ref:`api_field_guide`
----------------------

API tests are validation tests for the OpenStack API. They should not
use the existing Python clients for OpenStack, but should instead use
the Tempest implementations of clients. Having raw clients let us
pass invalid JSON to the APIs and see the results, something we could
not get with the native clients.

When it makes sense, API testing should be moved closer to the
projects themselves, possibly as functional tests in their unit test
frameworks.


:ref:`scenario_field_guide`
---------------------------

Scenario tests are complex "through path" tests for OpenStack
functionality. They are typically a series of steps where complicated
state requiring multiple services is set up exercised, and torn down.

Scenario tests should not use the existing Python clients for OpenStack,
but should instead use the Tempest implementations of clients.


:ref:`unit_tests_field_guide`
-----------------------------

Unit tests are the self checks for Tempest. They provide functional
verification and regression checking for the internal components of Tempest.
They should be used to just verify that the individual pieces of Tempest are
working as expected.
