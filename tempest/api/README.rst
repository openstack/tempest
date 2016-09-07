.. _api_field_guide:

Tempest Field Guide to API tests
================================


What are these tests?
---------------------

One of Tempest's prime function is to ensure that your OpenStack cloud
works with the OpenStack API as documented. The current largest
portion of Tempest code is devoted to test cases that do exactly this.

It's also important to test not only the expected positive path on
APIs, but also to provide them with invalid data to ensure they fail
in expected and documented ways. Over the course of the OpenStack
project Tempest has discovered many fundamental bugs by doing just
this.

In order for some APIs to return meaningful results, there must be
enough data in the system. This means these tests might start by
spinning up a server, image, etc, then operating on it.


Why are these tests in tempest?
-------------------------------

This is one of the core missions for the Tempest project, and where it
started. Many people use this bit of function in Tempest to ensure
their clouds haven't broken the OpenStack API.

It could be argued that some of the negative testing could be done
back in the projects themselves, and we might evolve there over time,
but currently in the OpenStack gate this is a fundamentally important
place to keep things.


Scope of these tests
--------------------

API tests should always use the Tempest implementation of the
OpenStack API, as we want to ensure that bugs aren't hidden by the
official clients.

They should test specific API calls, and can build up complex state if
it's needed for the API call to be meaningful.

They should send not only good data, but bad data at the API and look
for error codes.

They should all be able to be run on their own, not depending on the
state created by a previous test.
