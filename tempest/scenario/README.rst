.. _scenario_field_guide:

Tempest Field Guide to Scenario tests
=====================================


What are these tests?
---------------------

Scenario tests are "through path" tests of OpenStack
function. Complicated setups where one part might depend on completion
of a previous part. They ideally involve the integration between
multiple OpenStack services to exercise the touch points between them.

Any scenario test should have a real-life use case. An example would be:

 - "As operator I want to start with a blank environment":
    1. upload a glance image
    2. deploy a vm from it
    3. ssh to the guest
    4. create a snapshot of the vm


Why are these tests in tempest?
-------------------------------
This is one of tempests core purposes, testing the integration between
projects.


Scope of these tests
--------------------
Scenario tests should always use the Tempest implementation of the
OpenStack API, as we want to ensure that bugs aren't hidden by the
official clients.

Tests should be tagged with which services they exercise, as
determined by which client libraries are used directly by the test.


Example of a good test
----------------------
While we are looking for interaction of 2 or more services, be
specific in your interactions. A giant "this is my data center" smoke
test is hard to debug when it goes wrong.

A flow of interactions between glance and nova, like in the
introduction, is a good example. Especially if it involves a repeated
interaction when a resource is setup, modified, detached, and then
reused later again.
