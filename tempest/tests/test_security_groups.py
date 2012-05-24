from nose.plugins.attrib import attr
from tempest import openstack
from tempest import exceptions
from base_compute_test import BaseComputeTest
from tempest.common.utils.data_utils import rand_name
import time


class SecurityGroupsTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        cls.client = cls.security_groups_client

    @attr(type='positive')
    def test_security_groups_create_list_delete(self):
        """Positive test:Should return the list of Security Groups"""
        try:
            #Create 3 Security Groups
            security_group_list = list()
            for i in range(3):
                s_name = rand_name('securitygroup-')
                s_description = rand_name('description-')
                resp, securitygroup =\
                self.client.create_security_group(s_name, s_description)
                self.assertEqual(200, resp.status)
                security_group_list.append(securitygroup)
            #Fetch all Security Groups and verify the list
            #has all created Security Groups
            resp, fetched_list = self.client.list_security_groups()
            self.assertEqual(200, resp.status)
            #Now check if all the created Security Groups are in fetched list
            missing_sgs =\
            [sg for sg in security_group_list if sg not in fetched_list]
            self.assertFalse(missing_sgs,
                             "Failed to find Security Group %s in fetched list"
                             % ', '.join(m_group['name']
                                            for m_group in missing_sgs))
        finally:
            #Delete all the Security Groups created in this method
            for securitygroup in security_group_list:
                resp, _ =\
                self.client.delete_security_group(securitygroup['id'])
                self.assertEqual(202, resp.status)

    @attr(type='smoke')
    def test_security_group_create_delete(self):
        """Security Group should be created, verified and deleted"""
        try:
            s_name = rand_name('securitygroup-')
            s_description = rand_name('description-')
            resp, securitygroup = \
            self.client.create_security_group(s_name, s_description)
            self.assertEqual(200, resp.status)
            self.assertTrue('id' in securitygroup)
            securitygroup_id = securitygroup['id']
            self.assertFalse(securitygroup_id is None)
            self.assertTrue('name' in securitygroup)
            securitygroup_name = securitygroup['name']
            self.assertEqual(securitygroup_name, s_name,
                             "The created Security Group name is "
                             "not equal to the requested name")
        finally:
            #Delete Security Group created in this method
            resp, _ = self.client.delete_security_group(securitygroup['id'])
            self.assertEqual(202, resp.status)

    @attr(type='smoke')
    def test_security_group_create_get_delete(self):
        """Security Group should be created, fetched and deleted"""
        try:
            s_name = rand_name('securitygroup-')
            s_description = rand_name('description-')
            resp, securitygroup =\
            self.client.create_security_group(s_name, s_description)
            self.assertEqual(200, resp.status)
            #Now fetch the created Security Group by its 'id'
            resp, fetched_group =\
            self.client.get_security_group(securitygroup['id'])
            self.assertEqual(200, resp.status)
            self.assertEqual(securitygroup, fetched_group,
                             "The fetched Security Group is different "
                             "from the created Group")
        finally:
            #Delete the Security Group created in this method
            resp, _ = self.client.delete_security_group(securitygroup['id'])
            self.assertEqual(202, resp.status)

    @attr(type='negative')
    def test_security_group_get_nonexistant_group(self):
        """
        Negative test:Should not be able to GET the details
        of nonexistant Security Group
        """
        security_group_id = []
        resp, body = self.client.list_security_groups()
        for i in range(len(body)):
            security_group_id.append(body[i]['id'])
        #Creating a nonexistant Security Group id
        while True:
            non_exist_id = rand_name('999')
            if non_exist_id not in security_group_id:
                break
        try:
            resp, body = \
            self.client.get_security_group(non_exist_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to GET the details from a '
                      'nonexistant Security Group')

    @attr(type='negative')
    def test_security_group_create_with_invalid_group_name(self):
        """
        Negative test: Security Group should not be created with group name as
        an empty string/with white spaces/chars more than 255
        """
        s_description = rand_name('description-')
        #Create Security Group with empty string as group name
        try:
            resp, _ = self.client.create_security_group("", s_description)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Security Group should not be created '
                      'with EMPTY Name')
        #Create Security Group with white space in group name
        try:
            resp, _ = self.client.create_security_group(" ", s_description)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Security Group should not be created '
                      'with WHITE SPACE in Name')
        #Create Security Group with group name longer than 255 chars
        s_name = 'securitygroup-'.ljust(260, '0')
        try:
            resp, _ = self.client.create_security_group(s_name, s_description)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Security Group should not be created '
                      'with more than 255 chars in Name')

    @attr(type='negative')
    def test_security_group_create_with_invalid_group_description(self):
        """
        Negative test:Security Group should not be created with description as
        an empty string/with white spaces/chars more than 255
        """
        s_name = rand_name('securitygroup-')
        #Create Security Group with empty string as description
        try:
            resp, _ = self.client.create_security_group(s_name, "")
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Security Group should not be created '
                      'with EMPTY Description')
        #Create Security Group with white space in description
        try:
            resp, _ = self.client.create_security_group(s_name, " ")
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Security Group should not be created '
                      'with WHITE SPACE in Description')
        #Create Security Group with group description longer than 255 chars
        s_description = 'description-'.ljust(260, '0')
        try:
            resp, _ = self.client.create_security_group(s_name, s_description)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Security Group should not be created '
                      'with more than 255 chars in Description')

    @attr(type='negative')
    def test_security_group_create_with_duplicate_name(self):
        """
        Negative test:Security Group with duplicate name should not
        be created
        """
        try:
            s_name = rand_name('securitygroup-')
            s_description = rand_name('description-')
            resp, security_group =\
            self.client.create_security_group(s_name, s_description)
            self.assertEqual(200, resp.status)
            #Now try the Security Group with the same 'Name'
            try:
                resp, _ =\
                self.client.create_security_group(s_name, s_description)
            except exceptions.BadRequest:
                pass
            else:
                self.fail('Security Group should not be created '
                          'with duplicate Group Name')
        finally:
            #Delete the Security Group created in this method
            resp, _ = self.client.delete_security_group(security_group['id'])
            self.assertEqual(202, resp.status)

    @attr(type='negative')
    def test_delete_nonexistant_security_group(self):
        """
        Negative test:Deletion of a nonexistant Security Group should Fail
        """
        security_group_id = []
        resp, body = self.client.list_security_groups()
        for i in range(len(body)):
            security_group_id.append(body[i]['id'])
        #Creating Non Existant Security Group
        while True:
            non_exist_id = rand_name('999')
            if non_exist_id not in security_group_id:
                break
        try:
            resp, body = self.client.delete_security_group(non_exist_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to delete a nonexistant '
                      'Security Group')

    @attr(type='negative')
    def test_delete_security_group_without_passing_id(self):
        """
        Negative test:Deletion of a Security Group with out passing ID
        should Fail
        """
        try:
            resp, body = self.client.delete_security_group('')
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to delete a Security Group'
                        'with out passing ID')
