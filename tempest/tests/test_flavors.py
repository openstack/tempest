from nose.plugins.attrib import attr
from tempest import exceptions
from base_compute_test import BaseComputeTest


class FlavorsTest(BaseComputeTest):
    _multiprocess_shared_ = True

    @classmethod
    def setUpClass(cls):
        cls.client = cls.flavors_client

    @attr(type='smoke')
    def test_list_flavors(self):
        """List of all flavors should contain the expected flavor"""
        resp, flavors = self.client.list_flavors()
        resp, flavor = self.client.get_flavor_details(self.flavor_ref)
        flavor_min_detail = {'id': flavor['id'], 'links': flavor['links'],
                             'name': flavor['name']}
        self.assertTrue(flavor_min_detail in flavors)

    @attr(type='smoke')
    def test_list_flavors_with_detail(self):
        """Detailed list of all flavors should contain the expected flavor"""
        resp, flavors = self.client.list_flavors_with_detail()
        resp, flavor = self.client.get_flavor_details(self.flavor_ref)
        self.assertTrue(flavor in flavors)

    @attr(type='smoke')
    def test_get_flavor(self):
        """The expected flavor details should be returned"""
        resp, flavor = self.client.get_flavor_details(self.flavor_ref)
        self.assertEqual(self.flavor_ref, str(flavor['id']))

    @attr(type='negative')
    def test_get_non_existant_flavor(self):
        """flavor details are not returned for non existant flavors"""
        self.assertRaises(exceptions.NotFound, self.client.get_flavor_details,
                          999)

    @attr(type='positive', bug='lp912922')
    def test_list_flavors_limit_results(self):
        """Only the expected number of flavors should be returned"""
        params = {'limit': 1}
        resp, flavors = self.client.list_flavors(params)
        self.assertEqual(1, len(flavors))

    @attr(type='positive', bug='lp912922')
    def test_list_flavors_detailed_limit_results(self):
        """Only the expected number of flavors (detailed) should be returned"""
        params = {'limit': 1}
        resp, flavors = self.client.list_flavors_with_detail(params)
        self.assertEqual(1, len(flavors))

    @attr(type='positive')
    def test_list_flavors_using_marker(self):
        """The list of flavors should start from the provided marker"""
        resp, flavors = self.client.list_flavors()
        flavor_id = flavors[0]['id']

        params = {'marker': flavor_id}
        resp, flavors = self.client.list_flavors(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]),
                        'The list of flavors did not start after the marker.')

    @attr(type='positive')
    def test_list_flavors_detailed_using_marker(self):
        """The list of flavors should start from the provided marker"""
        resp, flavors = self.client.list_flavors_with_detail()
        flavor_id = flavors[0]['id']

        params = {'marker': flavor_id}
        resp, flavors = self.client.list_flavors_with_detail(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]),
                        'The list of flavors did not start after the marker.')

    @attr(type='positive')
    def test_list_flavors_detailed_filter_by_min_disk(self):
        """The detailed list of flavors should be filtered by disk space"""
        resp, flavors = self.client.list_flavors_with_detail()
        flavors = sorted(flavors, key=lambda k: k['disk'])
        flavor_id = flavors[0]['id']

        params = {'minDisk': flavors[1]['disk']}
        resp, flavors = self.client.list_flavors_with_detail(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))

    @attr(type='positive')
    def test_list_flavors_detailed_filter_by_min_ram(self):
        """The detailed list of flavors should be filtered by RAM"""
        resp, flavors = self.client.list_flavors_with_detail()
        flavors = sorted(flavors, key=lambda k: k['ram'])
        flavor_id = flavors[0]['id']

        params = {'minRam': flavors[1]['ram']}
        resp, flavors = self.client.list_flavors_with_detail(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))

    @attr(type='positive')
    def test_list_flavors_filter_by_min_disk(self):
        """The list of flavors should be filtered by disk space"""
        resp, flavors = self.client.list_flavors_with_detail()
        flavors = sorted(flavors, key=lambda k: k['disk'])
        flavor_id = flavors[0]['id']

        params = {'minDisk': flavors[1]['disk']}
        resp, flavors = self.client.list_flavors(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))

    @attr(type='positive')
    def test_list_flavors_filter_by_min_ram(self):
        """The list of flavors should be filtered by RAM"""
        resp, flavors = self.client.list_flavors_with_detail()
        flavors = sorted(flavors, key=lambda k: k['ram'])
        flavor_id = flavors[0]['id']

        params = {'minRam': flavors[1]['ram']}
        resp, flavors = self.client.list_flavors(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))

    @attr(type='negative')
    def test_get_flavor_details_for_invalid_flavor_id(self):
        """Ensure 404 returned for non-existant flavor ID"""

        self.assertRaises(exceptions.NotFound, self.client.get_flavor_details,
                        9999)
