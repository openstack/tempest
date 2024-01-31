.. _serial_tests_guide:

Tempest Field Guide to Serial tests
===================================


What are these tests?
---------------------

Tempest can run tests serially as well as in parallel, depending on the
configuration that is fully up to the user. However, sometimes you need to
make sure that tests are not interfering with each other via OpenStack
resources with the other tests running in parallel. Tempest creates separate
projects for each test class to separate project based resources between test
cases.

If your tests use resources outside of projects, e.g. host aggregates then
you might need to explicitly separate interfering test cases. If you only need
to separate a small set of test cases from each other then you can use the
``LockFixture``.

However, in some cases, a small set of tests needs to be run serially. For
example, some of the host aggregate and availability zone testing needs
compute nodes without any running nova server to be able to move compute hosts
between availability zones. But many tempest tests start one or more nova
servers.


Why are these tests in Tempest?
-------------------------------

This is one of Tempest's core purposes, testing the integration between
projects.


Scope of these tests
--------------------

The tests should always use the Tempest implementation of the OpenStack API,
as we want to ensure that bugs aren't hidden by the official clients.

Tests should be tagged with which services they exercise, as
determined by which client libraries are used directly by the test.


Example of a good test
----------------------

While we are looking for interaction of 2 or more services, be specific in
your interactions. A giant "this is my data center" smoke test is hard to
debug when it goes wrong.

The tests that need to be run serially need to be marked with the
``@serial`` class decorator. This will make sure that even if tempest is
configured to run the tests in parallel, these tests will always be executed
separately from the rest of the test cases.

Please note that due to test ordering optimization reasons test cases marked
for ``@serial`` execution need to be put under ``tempest/serial_tests``
directory. This will ensure that the serial tests will block the parallel tests
in the least amount of time.
