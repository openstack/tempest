from tempest.common.rest_client import RestClient
import json


class SecurityGroupsClient(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(SecurityGroupsClient, self).__init__(config, username, password,
                                           auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def list_security_groups(self, params=None):
        """List all security groups for a user"""

        url = 'os-security-groups'
        if params is not None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url += '?' + ' '.join(param_list)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['security_groups']

    def get_security_group(self, security_group_id):
        """Get the details of a Security Group"""
        url = "os-security-groups/%s" % str(security_group_id)
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['security_group']

    def create_security_group(self, name, description):
        """
        Creates a new security group.
        name (Required): Name of security group.
        description (Required): Description of security group.
        """
        post_body = {
            'name': name,
            'description': description,
        }
        post_body = json.dumps({'security_group': post_body})
        resp, body = self.post('os-security-groups',
                                        post_body, self.headers)
        body = json.loads(body)
        return resp, body['security_group']

    def delete_security_group(self, security_group_id):
        """Deletes the provided Security Group"""
        return self.delete('os-security-groups/%s'
                                   % str(security_group_id))

    def create_security_group_rule(self, parent_group_id, ip_proto, from_port,
                                      to_port, **kwargs):
        """
        Creating a new security group rules.
        parent_group_id :ID of Security group
        ip_protocol : ip_proto (icmp, tcp, udp).
        from_port: Port at start of range.
        to_port  : Port at end of range.
        Following optional keyword arguments are accepted:
        cidr     : CIDR for address range.
        group_id : ID of the Source group
        """
        post_body = {
            'parent_group_id': parent_group_id,
            'ip_protocol': ip_proto,
            'from_port': from_port,
            'to_port': to_port,
            'cidr': kwargs.get('cidr'),
            'group_id': kwargs.get('group_id'),
        }
        post_body = json.dumps({'security_group_rule': post_body})
        url = 'os-security-group-rules'
        resp, body = self.post(url, post_body, self.headers)
        body = json.loads(body)
        return resp, body['security_group_rule']

    def delete_security_group_rule(self, group_rule_id):
        """Deletes the provided Security Group rule"""
        return self.delete('os-security-group-rules/%s'
                                      % str(group_rule_id))
