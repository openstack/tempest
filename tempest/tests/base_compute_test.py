from tempest import exceptions
from tempest import openstack
from tempest.common.utils.data_utils import rand_name
import unittest2 as unittest


class BaseComputeTest(unittest.TestCase):

    os = openstack.Manager()
    servers_client = os.servers_client
    flavors_client = os.flavors_client
    images_client = os.images_client
    extensions_client = os.extensions_client
    floating_ips_client = os.floating_ips_client
    keypairs_client = os.keypairs_client
    floating_ips_client = os.floating_ips_client
    security_groups_client = os.security_groups_client
    limits_client = os.limits_client
    config = os.config
    build_interval = config.compute.build_interval
    build_timeout = config.compute.build_timeout
    ssh_user = config.compute.ssh_user
    servers = []

    # Validate reference data exists
    # If not, attempt to auto-configure
    try:
        image_ref = config.compute.image_ref
        image_ref_alt = config.compute.image_ref_alt
        images_client.get_image(image_ref)
        images_client.get_image(image_ref_alt)
    except:
        # Make a reasonable attempt to get usable images
        params = {'status': 'ACTIVE'}
        _, images = images_client.list_images_with_detail(params)
        if len(images) is 0:
            message = "No usable image exists. Upload an image to Glance."
            raise exceptions.InvalidConfiguration(message=message)
        if len(images) is 1:
            image_ref = images[0]['id']
            image_ref_alt = images[0]['id']
        else:
            # Try to determine if this is a devstack environment.
            # If so, some of the images are not usable

            # For now, the useable image in devstack has this property
            usable = [i for i in images if 'ramdisk_id' in i['metadata']]
            if len(usable) > 0:
                # We've found at least one image we can use
                image_ref = usable[0]['id']
                image_ref_alt = usable[0]['id']
            else:
                # We've done our due dillegence, take the first two images
                image_ref = images[0]['id']
                image_ref_alt = images[1]['id']

    try:
        flavor_ref = config.compute.flavor_ref
        flavor_ref_alt = config.compute.flavor_ref_alt
        flavors_client.get_flavor_details(flavor_ref)
        flavors_client.get_flavor_details(flavor_ref_alt)
    except:
        # Reload both with new values
        # Sort so the smallest flavors are used. This is for efficiency.
        _, flavors = flavors_client.list_flavors_with_detail()
        flavors = sorted(flavors, key=lambda k: k['ram'])

        if len(flavors) is 0:
            message = "No flavors exists. Add flavors via the admin API."
            raise exceptions.InvalidConfiguration(message=message)
        if len(flavors) is 1:
            flavor_ref = flavors[0]['id']
            flavor_ref_alt = flavors[0]['id']
        else:
            flavor_ref = flavors[0]['id']
            # Make sure the second flavor does not have the same RAM
            for i in range(1, len(flavors)):
                if flavors[i] == flavors[-1]:
                    # We've tried. Take the last flavor
                    flavor_ref_alt = flavors[i]['id']
                else:
                    if flavors[i]['ram'] > flavors[0]['ram']:
                        flavor_ref_alt = flavors[i]['id']
                        break

    def create_server(self, image_id=None):
        """Wrapper utility that returns a test server"""
        server_name = rand_name('test-vm-')
        flavor = self.flavor_ref
        if not image_id:
            image_id = self.image_ref

        resp, server = self.servers_client.create_server(
                                                server_name, image_id, flavor)
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')
        self.servers.append(server)
        return server
