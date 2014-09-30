Reviewing Tempest Code
======================

To start read the `OpenStack Common Review Checklist
<https://wiki.openstack.org/wiki/ReviewChecklist#Common_Review_Checklist>`_


Ensuring code is executed
-------------------------

For any new or change to a test it has to be verified in the gate. This means
that the first thing to check with any change is that a gate job actually runs
it. Tests which aren't executed either because of configuration or skips should
not be accepted.


Unit Tests
----------

For any change that adds new functionality to either common functionality or an
out-of-band tool unit tests are required. This is to ensure we don't introduce
future regressions and to test conditions which we may not hit in the gate runs.
Tests, and service clients aren't required to have unit tests since they should
be self verifying by running them in the gate.


API Stability
-------------
Tests should only be added for a published stable APIs. If a patch contains
tests for an API which hasn't been marked as stable or for an API that which
doesn't conform to the `API stability guidelines
<https://wiki.openstack.org/wiki/Governance/Approved/APIStability>`_ then it
should not be approved.


Reject Copy and Paste Test Code
------------------------
When creating new tests that are similar to existing tests it is tempting to
simply copy the code and make a few modifications. This increases code size and
the maintenance burden. Such changes should not be approved if it is easy to
abstract the duplicated code into a function or method.


Being explicit
--------------
When tests are being added that depend on a configurable feature or extension,
polling the API to discover that it is enabled should not be done. This will
just result in bugs being masked because the test can be skipped automatically.
Instead the config file should be used to determine whether a test should be
skipped or not. Do not approve changes that depend on an API call to determine
whether to skip or not.


Test Documentation
------------------
When a new test is being added refer to the :ref:`TestDocumentation` section in
hacking to see if the requirements are being met. With the exception of a class
level docstring linking to the API ref doc in the API tests and a docstring for
scenario tests this is up to the reviewers discretion whether a docstring is
required or not.


When to approve
---------------
 * Every patch needs two +2s before being approved.
 * Its ok to hold off on an approval until a subject matter expert reviews it
 * If a patch has already been approved but requires a trivial rebase to merge,
   you do not have to wait for a second +2, since the patch has already had
   two +2s.
