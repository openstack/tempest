Requirements Upper Constraint for Tempest
=========================================

Tempest is branchless and supported stable branches use Tempest
master and all EM stable branches use old compatible Tempest version
for their testing. This means the OpenStack installed upper-constraints
might not be compatible with Tempest used for stable branch testing.
For example, if Tempest master is used for testing the stable/stein
then stable/stein constraint might not be compatible with Tempest master so
we need to use master upper-constraints there. That is why we use virtual
env for Tempest installation and running tests so that we can control Tempest
required constraint from system wide installed constraints.

Devstack takes care of using the master upper-constraints when Tempest master
is used. But when old Tempest is used then devstack alone cannot handle the
compatible constraints because Tempest in-tree tox.ini also set the
upper-constraints which are master constraints so if devstack set the different
constraints than what we have in tox.ini we end up re-creation of venv which
flush all previously installed tempest plugins in that venv. More details are
on `this ML thread <http://lists.openstack.org/pipermail/openstack-discuss/2020-April/014388.html>`_

To solve that problem we have two ways:

#. Set UPPER_CONSTRAINTS_FILE to compatible constraint path
   This option is not easy as it requires to set this env var everywhere
   Tempest tox env is used like in devstack, grenade, projects side, zuulv3 roles etc.

#. Pin upper-constraints in tox.ini
   If we can pin the upper-constraints in tox.ini on every release with the branch
   constraint at the time of release then we can solve it in an easy way because tox
   can use the compatible constraint at the time of venv creation itself. But this can
   again mismatch with the devstack set constraint so we need to follow the below process
   to make it work.

How to pin upper-constraints in tox.ini
---------------------------------------

This has to be done exactly before we cut the Tempest new major version bump
release for the cycle.

Step1: Add the pin constraint proposal in `QA office hour <https://wiki.openstack.org/wiki/Meetings/QATeamMeeting#Agenda_for_next_Office_hours>`_.
       Pin constraint proposal includes:

       - pin constraint patch. `Example patch 720578 <https://review.opendev.org/#/c/720578/>`_
       - revert of pin constraint patch. `Example patch 721724 <https://review.opendev.org/#/c/721724/>`_

Step2: Approve pin constraint and its revert patch together.
       During office hour we need to check that there are no open patches for
       Tempest release and accordingly we fast approve the 'pin constraint' and its
       revert patch during office hour itself. Remember 'pin constraint patch' has to be
       the last commit to include in Tempest release.

Step3: Use 'pin constraint patch' hash for the Tempest new release.
       By using the 'pin constraint patch' hash we make sure tox.ini in Tempest
       released tag has the compatible stable constraint not the master one.
       For Example `Tempest 24.0.0 <https://opendev.org/openstack/tempest/src/tag/24.0.0/tox.ini#L14>`_
