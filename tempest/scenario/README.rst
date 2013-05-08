Tempest Guide to Scenario tests
========


What are these tests?
--------

Scenario tests are "through path" tests of OpenStack
function. Complicated setups where one part might depend on completion
of a previous part. They ideally involve the integration between
multiple OpenStack services to exercise the touch points between them.

An example would be: start with a blank environment, upload a glance
image, deploy a vm from it, ssh to the guest, make changes, capture
that vm's image back into glance as a snapshot, and launch a second vm
from that snapshot.


Why are these tests in tempest?
--------
This is one of tempests core purposes, testing the integration between
projects.


Scope of these tests
--------
Scenario tests should always test at least 2 services in
interaction. They should use the official python client libraries for
OpenStack, as they provide a more realistic approach in how people
will interact with the services.

TODO: once we have service tags, tests should be tagged with which
services they exercise.


Example of a good test
--------
While we are looking for interaction of 2 or more services, be
specific in your interactions. A giant "this is my data center" smoke
test is hard to debug when it goes wrong.

A flow of interactions between glance and nova, like in the
introduction, is a good example. Especially if it involves a repeated
interaction when a resource is setup, modified, detached, and then
reused later again.
