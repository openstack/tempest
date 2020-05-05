Stable Branch Testing Policy
============================

Tempest and its plugins need to support the stable branches
as per :doc:`Stable Branch Support Policy </stable_branch_support_policy>`.

Because of branchless model of Tempest and plugins, all the supported
stable branches use the Tempest and plugins master version for their
testing. That is done in devstack by using the `master branch
<https://opendev.org/openstack/devstack/src/commit/c104afec7dd72edfd909847bee9c14eaf077a28b/stackrc#L314>`_
for the Tempest installation. To make sure the master version of Tempest or
plugins (for any changes or adding new tests) is compatible for all
the supported stable branches testing, Tempest and its plugins need to
add the stable branches job on the master gate. That way can test the stable
branches against master code and can avoid breaking supported branches
accidentally.

Example:

* `Stable jobs on Tempest master
  <https://opendev.org/openstack/tempest/src/commit/e8f1876aa6772077f85f380677b30251c2454505/.zuul.yaml#L646-L651>`_.

* `Stable job on neutron tempest plugins
  <https://opendev.org/openstack/neutron-tempest-plugin/src/commit/4bc1b00213cf660648cad1916fe6497ac29b2e78/.zuul.yaml#L1427-L1428>`_

Once any stable branch is moved to the `Extended Maintenance Phases`_
and devstack start using the Tempest older version for that stable
branch testing then we can remove that stable branch job from master
gate.

Example: https://review.opendev.org/#/c/722183/

.. _Extended Maintenance Phases: https://docs.openstack.org/project-team-guide/stable-branches.html#extended-maintenance
