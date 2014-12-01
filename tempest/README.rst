============================
Tempest Field Guide Overview
============================

Tempest is designed to be useful for a large number of different
environments. This includes being useful for gating commits to
OpenStack core projects, being used to validate OpenStack cloud
implementations for both correctness, as well as a burn in tool for
OpenStack clouds.

As such Tempest tests come in many flavors, each with their own rules
and guidelines. Below is the proposed Havana restructuring for Tempest
to make this clear.

| tempest/
|    api/ - API tests
|    cli/ - CLI tests
|    scenario/ - complex scenario tests
|    stress/ - stress tests
|    thirdparty/ - 3rd party api tests

Each of these directories contains different types of tests. What
belongs in each directory, the rules and examples for good tests, are
documented in a README.rst file in the directory.

:ref:`api_field_guide`
----------------------

API tests are validation tests for the OpenStack API. They should not
use the existing python clients for OpenStack, but should instead use
the tempest implementations of clients. This allows us to test both
XML and JSON. Having raw clients also lets us pass invalid JSON and
XML to the APIs and see the results, something we could not get with
the native clients.

When it makes sense, API testing should be moved closer to the
projects themselves, possibly as functional tests in their unit test
frameworks.


:ref:`cli_field_guide`
----------------------

CLI tests use the openstack CLI to interact with the OpenStack
cloud. CLI testing in unit tests is somewhat difficult because unlike
server testing, there is no access to server code to
instantiate. Tempest seems like a logical place for this, as it
prereqs having a running OpenStack cloud.


:ref:`scenario_field_guide`
---------------------------

Scenario tests are complex "through path" tests for OpenStack
functionality. They are typically a series of steps where complicated
state requiring multiple services is set up exercised, and torn down.

Scenario tests should not use the existing python clients for OpenStack,
but should instead use the tempest implementations of clients.


:ref:`stress_field_guide`
-------------------------

Stress tests are designed to stress an OpenStack environment by running a high
workload against it and seeing what breaks. The stress test framework runs
several test jobs in parallel and can run any existing test in Tempest as a
stress job.

:ref:`third_party_field_guide`
-----------------------------

Many openstack components include 3rdparty API support. It is
completely legitimate for Tempest to include tests of 3rdparty APIs,
but those should be kept separate from the normal OpenStack
validation.

:ref:`unit_tests_field_guide`
-----------------------------

Unit tests are the self checks for Tempest. They provide functional
verification and regression checking for the internal components of tempest.
They should be used to just verify that the individual pieces of tempest are
working as expected.
