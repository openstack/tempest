Keystone Scopes & Roles Support in Tempest
==========================================

OpenStack Keystone supports different scopes in token, refer to the
`Keystone doc <https://docs.openstack.org/keystone/latest/admin/tokens-overview.html#authorization-scopes>`_.
Along with the scopes, keystone supports default roles, one of which
is a reader role, for details refer to
`this keystone document <https://docs.openstack.org/keystone/latest/admin/service-api-protection.html>`_.

Tempest supports those scopes and roles credentials that can be used
to test APIs under different scope and roles.

Dynamic Credentials
-------------------

Dynamic credential supports all the below set of personas and allows
you to generate credentials tailored to a specific persona that you
can use in your test.

Domain scoped personas:
^^^^^^^^^^^^^^^^^^^^^^^^

  #. Domain Admin: This is supported and can be requested and used from
     the test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['domain_admin']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_d_admin_client = (
                     cls.os_domain_admin.availability_zone_client)

  #. Domain Member: This is supported and can be requested and used from
     the test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['domain_member']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_d_member_client = (
                     cls.os_domain_member.availability_zone_client)

  #. Domain Reader: This is supported and can be requested and used from
     the test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['domain_reader']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_d_reader_client = (
                     cls.os_domain_reader.availability_zone_client)

  #. Domain other roles: This is supported and can be requested and used from
     the test as below:

     You need to use the ``domain`` as the prefix in credentials type, and
     based on that, Tempest will create test users under 'domain' scope.

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = [['domain_my_role1', 'my_own_role1', 'admin']
                            ['domain_my_role2', 'my_own_role2']]

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_d_role1_client = (
                     cls.os_domain_my_role1.availability_zone_client)
                 cls.az_d_role2_client = (
                     cls.os_domain_my_role2.availability_zone_client)

System scoped personas:
^^^^^^^^^^^^^^^^^^^^^^^

  #. System Admin: This is supported and can be requested and used from the
     test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['system_admin']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_s_admin_client = (
                     cls.os_system_admin.availability_zone_client)

  #. System Member: This is supported and can be requested and used from the
     test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['system_member']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_s_member_client = (
                     cls.os_system_member.availability_zone_client)

  #. System Reader: This is supported and can be requested and used from
     the test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['system_reader']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_s_reader_client = (
                     cls.os_system_reader.availability_zone_client)

  #. System other roles: This is supported and can be requested and used from
     the test as below:

     You need to use the ``system`` as the prefix in credentials type, and
     based on that, Tempest will create test users under 'project' scope.

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = [['system_my_role1', 'my_own_role1', 'admin']
                            ['system_my_role2', 'my_own_role2']]

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_s_role1_client = (
                     cls.os_system_my_role1.availability_zone_client)
                 cls.az_s_role2_client = (
                     cls.os_system_my_role2.availability_zone_client)

Project scoped personas:
^^^^^^^^^^^^^^^^^^^^^^^^

  #. Project Admin: This is supported and can be requested and used from
     the test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['project_admin']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_p_admin_client = (
                     cls.os_project_admin.availability_zone_client)

  #. Project Member: This is supported and can be requested and used from
     the test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['project_member']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_p_member_client = (
                     cls.os_project_member.availability_zone_client)

  #. Project Reader: This is supported and can be requested and used from
     the test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['project_reader']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_p_reader_client = (
                     cls.os_project_reader.availability_zone_client)

     .. note::
         'primary', 'project_admin', 'project_member', and 'project_reader'
         credentials will be created under same project.

  #. Project alternate Admin: This is supported and can be requested and used from
     the test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['project_alt_admin']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_p_alt_admin_client = (
                     cls.os_project_alt_admin.availability_zone_client)

  #. Project alternate Member: This is supported and can be requested and used from
     the test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['project_alt_member']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_p_alt_member_client = (
                     cls.os_project_alt_member.availability_zone_client)

  #. Project alternate Reader: This is supported and can be requested and used from
     the test as below:

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = ['project_alt_reader']

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_p_alt_reader_client = (
                     cls.os_project_alt_reader.availability_zone_client)

     .. note::
         'alt', 'project_alt_admin', 'project_alt_member', and
         'project_alt_reader' credentials will be created under same project.

  #. Project other roles: This is supported and can be requested and used from
     the test as below:

     You need to use the ``project`` as the prefix in credentials type, and
     based on that, Tempest will create test users under 'project' scope.

     .. code-block:: python

         class TestDummy(base.DummyBaseTest):

             credentials = [['project_my_role1', 'my_own_role1', 'admin']
                            ['project_my_role2', 'my_own_role2']]

             @classmethod
             def setup_clients(cls):
                 super(TestDummy, cls).setup_clients()
                 cls.az_role1_client = (
                     cls.os_project_my_role1.availability_zone_client)
                 cls.az_role2_client = (
                     cls.os_project_my_role2.availability_zone_client)

  .. note::
      'admin' credenatials is considered and kept as legacy admin and
      will be created under new project. If any test want to test with
      admin role in projectA and non-admin/admin in projectB then test
      can request projectA admin using 'admin' or 'project_alt_admin'
      and non-admin in projectB using 'primary', 'project_member',
      or 'project_reader'/admin in projectB using 'project_admin'. Many
      existing tests using the 'admin' with new project to assert on the
      resource list so we are keeping 'admin' a kind of legacy admin.

Pre-Provisioned Credentials
---------------------------

Pre-Provisioned credentials support the below set of personas and can be
used in the test as shown above in the ``Dynamic Credentials`` Section.

* Domain Admin
* Domain Member
* Domain Reader
* System Admin
* System Member
* System Reader
* Project Admin
* Project Member
* Project Reader
