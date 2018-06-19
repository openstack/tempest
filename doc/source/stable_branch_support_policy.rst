Stable Branch Support Policy
============================

Since the `Extended Maintenance policy`_ for stable branches was adopted
OpenStack projects will keep stable branches around after a "stable" or
"maintained" period for a phase of indeterminate length called "Extended
Maintenance". Prior to this resolution Tempest supported all stable branches
which were supported upstream. This policy does not scale under the new model
as Tempest would be responsible for gating proposed changes against an ever
increasing number of branches. Therefore due to resource constraints, Tempest
will only provide support for branches in the "Maintained" phase from the
documented `Support Phases`_. When a branch moves from the *Maintained* to the
*Extended Maintenance* phase, Tempest will tag the removal of support for that
branch as it has in the past when a branch goes end of life.

The expectation for *Extended Maintenance* phase branches is that they will continue
running Tempest during that phase of support. Since the REST APIs are stable
interfaces across release boundaries, branches in these phases should run
Tempest from master as long as possible. But, because we won't be actively
testing branches in these phases, it's possible that we'll introduce changes to
Tempest on master which will break support on *Extended Maintenance* phase
branches. When this happens the expectation for those branches is to either
switch to running Tempest from a tag with support for the branch, or blacklist
a newly introduced test (if that is the cause of the issue). Tempest will not
be creating stable branches to support *Extended Maintenance* phase branches, as
the burden is on the *Extended Maintenance* phase branche maintainers, not the Tempest
project, to support that branch.

.. _Extended Maintenance policy: https://governance.openstack.org/tc/resolutions/20180301-stable-branch-eol.html
.. _Support Phases: https://docs.openstack.org/project-team-guide/stable-branches.html#maintenance-phases
