Tempest and Plugins compatible version policy
=============================================

Tempest and its plugins are responsible for the integrated
testing of OpenStack. These tools have two use cases:

#. Testing upstream code at gate
#. Testing Production Cloud

Upstream code is tested by the master version of branchless Tempest & plugins
for all supported stable branches in `Maintained phase`_.

Production Cloud can be tested by using the compatible version or using
master version. It depends on the testing strategy of cloud. To provide
the compatible version of Tempest and its Plugins per OpenStack release,
we started the coordinated release of all plugins and Tempest per OpenStack
release.
These versions are the first set of versions from Tempest and its Plugins to
officially start the support of a particular OpenStack release. For example:
OpenStack Train release first compatible versions `Tempest plugins version`_.

Because of branchless nature of Tempest and its plugins, first version
released during OpenStack release is not the last version to support that
OpenStack release. This means the next (or master) versions can also be used
for upstream testing as well as in production testing.

Since the `Extended Maintenance policy`_ for stable branch, Tempest
started releasing the ``end of support`` version once stable release
is moved to EM state, which used to happen on EOL of stable release. This is
the last compatible version of Tempest for the OpenStack release moved to EM.

Because of branchless nature as explained above, we have a range of versions
which can be considered a compatible version for particular OpenStack release.
How we should release those versions is mentioned in the below table.

 +-----------------------------+-----------------+------------------------------------+
 | First compatible version -> | OpenStack 'XYZ' | <- Last compatible version         |
 +=============================+=================+====================================+
 |This is the latest version   |                 |This is the version released        |
 |released when OpenStack      |                 |when OpenStack 'XYZ' is moved to    |
 |'XYZ' is released.           |                 |EM state. Hash used for this should |
 |Example:                     |                 |be the hash from master at the time |
 |`Tempest plugins version`_   |                 |of branch is EM not the one used for|
 |                             |                 |First compatible version            |
 +-----------------------------+-----------------+------------------------------------+

Tempest & the Plugins should follow the above mentioned policy for the
``First compatible version`` and the ``Last compatible version.``
so that we provide the right set of compatible versions to Upstream as well as to
Production Cloud testing.

.. _Maintained phase: https://docs.openstack.org/project-team-guide/stable-branches.html#maintained
.. _Extended Maintenance policy: https://governance.openstack.org/tc/resolutions/20180301-stable-branch-eol.html
.. _Tempest plugins version: https://releases.openstack.org/train/#tempest-plugins
