.. _third_party_field_guide:

Tempest Field Guide to Third Party API tests
============================================


What are these tests?
---------------------

Third party tests are tests for non native OpenStack APIs that are
part of OpenStack projects. If we ship an API, we're really required
to ensure that it's working.

An example is that Nova Compute currently has EC2 API support in tree,
which should be tested as part of normal process.


Why are these tests in tempest?
-------------------------------

If we ship an API in an OpenStack component, there should be tests in
tempest to exercise it in some way.


Scope of these tests
--------------------

Third party API testing should be limited to the functional testing of
third party API compliance. Complex scenarios should be avoided, and
instead exercised with the OpenStack API, unless the third party API
can't be tested without those scenarios.

Whenever possible third party API testing should use a client as close
to the third party API as possible. The point of these tests is API
validation.
