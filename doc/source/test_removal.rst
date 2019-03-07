.. _test-removal:

Tempest Test Removal Procedure
==============================

Historically, Tempest was the only way of doing functional testing and
integration testing in OpenStack. This was mostly only an artifact of Tempest
being the only proven pattern for doing this, not an artifact of a design
decision. However, moving forward, as functional testing is being spun up in
each individual project, we really only want Tempest to be the integration test
suite it was intended to be: testing the high-level interactions between
projects through REST API requests. In this model, there are probably existing
tests that aren't the best fit living in Tempest. However, since Tempest is
largely still the only gating test suite in this space we can't carelessly rip
out everything from the tree. This document outlines the procedure which was
developed to ensure we minimize the risk for removing something of value from
the Tempest tree.

This procedure might seem overly conservative and slow-paced, but this is by
design to try to ensure we don't remove something that is actually providing
value. Having potential duplication between testing is not a big deal
especially compared to the alternative of removing something which is actually
providing value and is actively catching bugs, or blocking incorrect patches
from landing.

Proposing a test removal
------------------------

3 prong rule for removal
^^^^^^^^^^^^^^^^^^^^^^^^

In the proposal etherpad we'll be looking for answers to 3 questions:

#. The tests proposed for removal must have equiv. coverage in a different
   project's test suite (whether this is another gating test project, or an in
   tree functional test suite). For API tests preferably the other project will
   have a similar source of friction in place to prevent breaking API changes
   so that we don't regress and let breaking API changes slip through the
   gate.
#. The test proposed for removal has a failure rate <  0.50% in the gate over
   the past release (the value and interval will likely be adjusted in the
   future)

   .. _`prong #3`:
#. There must not be an external user/consumer of Tempest
   that depends on the test proposed for removal

The answers to 1 and 2 are easy to verify. For 1 just provide a link to the new
test location. If you are linking to the Tempest removal patch please also put
a Depends-On in the commit message for the commit which moved the test into
another repo.

For prong 2 you can use OpenStack-Health:

Using OpenStack-Health
""""""""""""""""""""""

Go to: http://status.openstack.org/openstack-health and then navigate to a per
test page for six months. You'll end up with a page that will graph the success
and failure rates on the bottom graph. For example, something like `this URL`_.

.. _this URL: http://status.openstack.org/openstack-health/#/test/tempest.scenario.test_volume_boot_pattern.TestVolumeBootPatternV2.test_volume_boot_pattern?groupKey=project&resolutionKey=day&duration=P6M

The Old Way using subunit2sql directly
""""""""""""""""""""""""""""""""""""""

``SELECT * from tests where test_id like "%test_id%";``
(where ``$test_id`` is the full test_id, but truncated to the class because of
``setUpClass`` or ``tearDownClass`` failures)

You can access the infra mysql subunit2sql db w/ read-only permissions with:

* hostname: logstash.openstack.org
* username: query
* password: query
* db_name: subunit2sql

For example if you were trying to remove the test with the id:
``tempest.api.compute.admin.test_flavors_negative.FlavorsAdminNegativeTestJSON.test_get_flavor_details_for_deleted_flavor``
you would run the following:

#. run the command: ``mysql -u query -p -h logstash.openstack.org subunit2sql``
   to connect to the subunit2sql db
#. run the query:

   .. code-block:: console

       MySQL [subunit2sql]> select * from tests where test_id like \
       "tempest.api.compute.admin.test_flavors_negative.FlavorsAdminNegativeTestJSON%";

   which will return a table of all the tests in the class (but it will also
   catch failures in ``setUpClass`` and ``tearDownClass``)
#. paste the output table with numbers and the mysql command you ran to
   generate it into the etherpad.

Eventually, a CLI interface will be created to make that a bit more friendly.
Also a dashboard is in the works so we don't need to manually run the command.

The intent of the 2nd prong is to verify that moving the test into a project
specific testing is preventing bugs (assuming the Tempest tests were catching
issues) from bubbling up a layer into Tempest jobs. If we're seeing failure
rates above a certain threshold in the gate checks that means the functional
testing isn't really being effective in catching that bug (and therefore
blocking it from landing) and having the testing run in Tempest still has
value.

However, for the 3rd prong verification is a bit more subjective. The original
intent of this prong was mostly for refstack/defcore and also for things that
running on the stable branches. We don't want to remove any tests if that
would break our API consistency checking between releases, or something that
defcore/refstack is depending on being in Tempest. It's worth pointing out
that if a test is used in `defcore`_ as part of `interop`_ testing then it will
probably have continuing value being in Tempest as part of the
integration/integrated tests in general. This is one area where some overlap
is expected between testing in projects and Tempest, which is not a bad thing.

.. _defcore: https://wiki.openstack.org/wiki/Governance/InteropWG
.. _interop: https://www.openstack.org/brand/interop

Discussing the 3rd prong
""""""""""""""""""""""""

There are 2 approaches to addressing the 3rd prong. Either it can be raised
during a QA meeting during the Tempest discussion. Please put it on the agenda
well ahead of the scheduled meeting. Since the meeting time will be well known
ahead of time anyone who depends on the tests will have ample time beforehand
to outline any concerns on the before the meeting. To give ample time for
people to respond to removal proposals please add things to the agenda by the
Monday before the meeting.

The other option is to raise the removal on the openstack-discuss mailing list.
(for example see: http://lists.openstack.org/pipermail/openstack-dev/2016-February/086218.html
or http://lists.openstack.org/pipermail/openstack-discuss/2019-March/003574.html )
This will raise the issue to the wider community and attract at least the same
(most likely more) attention than discussing it during the irc meeting. The
only downside is that it might take more time to get a response, given the
nature of ML.

Exceptions to this procedure
----------------------------

For the most part, all Tempest test removals have to go through this procedure
there are a couple of exceptions though:

#. The class of testing has been decided to be outside the scope of Tempest.
#. A revert for a patch which added a broken test, or testing which didn't
   actually run in the gate (basically any revert for something which
   shouldn't have been added)
#. Tests that would become out of scope as a consequence of an API change,
   as described in `API Compatibility`_.
   Such tests cannot live in Tempest because of the branchless nature of
   Tempest. Such tests must still honor `prong #3`_.

For the first exception type, the only types of testing in the tree which have been
declared out of scope at this point are:

* The CLI tests (which should be completely removed at this point)
* Neutron Adv. Services testing (which should be completely removed at this
  point)
* XML API Tests (which should be completely removed at this point)
* EC2 API/boto tests (which should be completely removed at this point)

For tests that fit into this category, the only criteria for removal is that
there is equivalent testing elsewhere.

Tempest Scope
^^^^^^^^^^^^^

Starting in the liberty cycle Tempest, has defined a set of projects which
are defined as in scope for direct testing in Tempest. As of today that list
is:

* Keystone
* Nova
* Glance
* Cinder
* Neutron
* Swift

Anything that lives in Tempest which doesn't test one of these projects can be
removed assuming there is equivalent testing elsewhere. Preferably using the
`tempest plugin mechanism`_
to maintain continuity after migrating the tests out of Tempest.

.. _tempest plugin mechanism: https://docs.openstack.org/tempest/latest/plugin.html

API Compatibility
"""""""""""""""""

If an API introduces a non-discoverable, backward-incompatible change, and
such a change is not backported to all versions supported by Tempest, tests for
that API cannot live in Tempest anymore.
This is because tests would not be able to know or control which API response
to expect, and thus would not be able to enforce a specific behavior.

If a test exists in Tempest that would meet these criteria as a consequence of a
change, the test must be removed according to the procedure discussed in
this document. The API change should not be merged until all conditions
required for test removal can be met.
