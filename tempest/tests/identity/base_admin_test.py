import unittest2 as unittest
import nose
import tempest.config
from tempest import openstack
from tempest.common.utils.data_utils import rand_name


class BaseAdminTest(unittest.TestCase):
    """Base class for Identity Admin Tests"""

    @classmethod
    def setUpClass(cls):
        cls.config = tempest.config.TempestConfig()
        cls.admin_username = cls.config.compute_admin.username
        cls.admin_password = cls.config.compute_admin.password
        cls.admin_tenant = cls.config.compute_admin.tenant_name

        if not(cls.admin_username and cls.admin_password and cls.admin_tenant):
            raise nose.SkipTest("Missing Admin credentials in configuration")

        cls.admin_os = openstack.AdminManager()
        cls.client = cls.admin_os.admin_client
        cls.token_client = cls.admin_os.token_client

        if not cls.client.has_admin_extensions():
            raise nose.SkipTest("Admin extensions disabled")

        cls.os = openstack.Manager()
        cls.non_admin_client = cls.os.admin_client
        cls.data = DataGenerator(cls.client)

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown_all()

    def disable_user(self, user_name):
        user = self.get_user_by_name(user_name)
        self.client.enable_disable_user(user['id'], False)

    def disable_tenant(self, tenant_name):
        tenant = self.get_tenant_by_name(tenant_name)
        self.client.update_tenant(tenant['id'], tenant['description'], False)

    def get_user_by_name(self, name):
        _, users = self.client.get_users()
        user = [u for u in users if u['name'] == name]
        if len(user) > 0:
            return user[0]

    def get_tenant_by_name(self, name):
        _, tenants = self.client.get_tenants()
        tenant = [t for t in tenants if t['name'] == name]
        if len(tenant) > 0:
            return tenant[0]

    def get_role_by_name(self, name):
        _, roles = self.client.get_roles()
        role = [r for r in roles if r['name'] == name]
        if len(role) > 0:
            return role[0]


class DataGenerator(object):

        def __init__(self, client):
            self.client = client
            self.users = []
            self.tenants = []
            self.roles = []
            self.role_name = None

        def setup_test_user(self):
            """Set up a test user"""
            self.setup_test_tenant()
            self.test_user = rand_name('test_user_')
            self.test_password = rand_name('pass_')
            self.test_email = self.test_user + '@testmail.tm'
            resp, self.user = self.client.create_user(self.test_user,
                                                    self.test_password,
                                                    self.tenant['id'],
                                                    self.test_email)
            self.users.append(self.user)

        def setup_test_tenant(self):
            """Set up a test tenant"""
            self.test_tenant = rand_name('test_tenant_')
            self.test_description = rand_name('desc_')
            resp, self.tenant = self.client.create_tenant(
                                                        name=self.test_tenant,
                                             description=self.test_description)
            self.tenants.append(self.tenant)

        def setup_test_role(self):
            """Set up a test role"""
            self.role_name = rand_name('role')
            resp, role = self.client.create_role(self.role_name)
            self.roles.append(role)

        def teardown_all(self):
            for user in self.users:
                self.client.delete_user(user['id'])
            for tenant in self.tenants:
                self.client.delete_tenant(tenant['id'])
            for role in self.roles:
                self.client.delete_role(role['id'])
