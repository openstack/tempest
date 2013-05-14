Tempest Guide to Whitebox tests
========


What are these tests?
--------

When you hit the OpenStack API, this causes internal state changes in
the system. This might be database transitions, vm modifications,
other deep state changes which aren't really accessible from the
OpenStack API. These side effects are sometimes important to
validate.

White box testing is an approach there. In white box testing you are
given database access to the environment, and can verify internal
record changes after an API call.

This is an optional part of testing, and requires extra setup, but can
be useful for validating Tempest internals.


Why are these tests in tempest?
--------

Especially when it comes to something like VM state changing, which is
a coordination of numerous running daemons, and a functioning VM, it's
very difficult to get a realistic test like this in unit tests.


Scope of these tests
--------

White box tests should be limitted to tests where black box testing
(using the OpenStack API to verify results) isn't sufficient.

As these poke at internals of OpenStack, it should also be realized
that these tests are very tightly coupled to current implementation of
OpenStack. They will need to be maintained agressively to keep up with
internals changes in OpenStack projects.


Example of a good test
--------

Pushing VMs through a series of state transitions, and ensuring along
the way the database state transitions match what's expected.
