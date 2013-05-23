Tempest Field Guide
========

Tempest is designed to be useful for a large number of different
environments. This includes being useful for gating commits to
OpenStack core projects, being used to validate OpenStack cloud
implementations for both correctness, as well as a burn in tool for
OpenStack clouds.

As such Tempest tests come in many flavors, each with their own rules
and guidelines. Below is the proposed Havana restructuring for Tempest
to make this clear.

tempest/
   api/ - API tests
   cli/ - CLI tests
   scenario/ - complex scenario tests
   stress/ - stress tests
   thirdparty/ - 3rd party api tests
   whitebox/ - white box testing

Each of these directories contains different types of tests. What
belongs in each directory, the rules and examples for good tests, are
documented in a README.rst file in the directory.


api
------------

API tests are validation tests for the OpenStack API. They should not
use the existing python clients for OpenStack, but should instead use
the tempest implementations of clients. This allows us to test both
XML and JSON. Having raw clients also lets us pass invalid JSON and
XML to the APIs and see the results, something we could not get with
the native clients.

When it makes sense, API testing should be moved closer to the
projects themselves, possibly as functional tests in their unit test
frameworks.


cli
------------

CLI tests use the openstack CLI to interact with the OpenStack
cloud. CLI testing in unit tests is somewhat difficult because unlike
server testing, there is no access to server code to
instantiate. Tempest seems like a logical place for this, as it
prereqs having a running OpenStack cloud.


scenario
------------

Scenario tests are complex "through path" tests for OpenStack
functionality. They are typically a series of steps where complicated
state requiring multiple services is set up exercised, and torn down.

Scenario tests can and should use the OpenStack python clients.


stress
-----------

Stress tests are designed to stress an OpenStack environment by
running a high workload against it and seeing what breaks. Tools may
be provided to help detect breaks (stack traces in the logs).

TODO: old stress tests deleted, new_stress that david is working on
moves into here.


thirdparty
------------

Many openstack components include 3rdparty API support. It is
completely legitmate for Tempest to include tests of 3rdparty APIs,
but those should be kept seperate from the normal OpenStack
validation.


whitebox
----------

Whitebox tests are tests which require access to the database of the
target OpenStack machine to verify internal state after opperations
are made. White box tests are allowed to use the python clients.
