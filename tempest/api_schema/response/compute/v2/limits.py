# Copyright 2014 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

get_limit = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'limits': {
                'type': 'object',
                'properties': {
                    'absolute': {
                        'type': 'object',
                        'properties': {
                            'maxTotalRAMSize': {'type': 'integer'},
                            'totalCoresUsed': {'type': 'integer'},
                            'maxTotalInstances': {'type': 'integer'},
                            'maxTotalFloatingIps': {'type': 'integer'},
                            'totalSecurityGroupsUsed': {'type': 'integer'},
                            'maxTotalCores': {'type': 'integer'},
                            'totalFloatingIpsUsed': {'type': 'integer'},
                            'maxSecurityGroups': {'type': 'integer'},
                            'maxServerMeta': {'type': 'integer'},
                            'maxPersonality': {'type': 'integer'},
                            'maxImageMeta': {'type': 'integer'},
                            'maxPersonalitySize': {'type': 'integer'},
                            'maxSecurityGroupRules': {'type': 'integer'},
                            'maxTotalKeypairs': {'type': 'integer'},
                            'totalRAMUsed': {'type': 'integer'},
                            'totalInstancesUsed': {'type': 'integer'},
                            'maxServerGroupMembers': {'type': 'integer'},
                            'maxServerGroups': {'type': 'integer'},
                            'totalServerGroupsUsed': {'type': 'integer'}
                        },
                        # NOTE(gmann): maxServerGroupMembers,  maxServerGroups
                        # and totalServerGroupsUsed are API extension,
                        # and some environments return a response without these
                        # attributes.So they are not 'required'.
                        'required': ['maxImageMeta',
                                     'maxPersonality',
                                     'maxPersonalitySize',
                                     'maxSecurityGroupRules',
                                     'maxSecurityGroups',
                                     'maxServerMeta',
                                     'maxTotalCores',
                                     'maxTotalFloatingIps',
                                     'maxTotalInstances',
                                     'maxTotalKeypairs',
                                     'maxTotalRAMSize',
                                     'totalCoresUsed',
                                     'totalFloatingIpsUsed',
                                     'totalInstancesUsed',
                                     'totalRAMUsed',
                                     'totalSecurityGroupsUsed']
                    },
                    'rate': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'limit': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'next-available':
                                                {'type': 'string'},
                                            'remaining':
                                                {'type': 'integer'},
                                            'unit':
                                                {'type': 'string'},
                                            'value':
                                                {'type': 'integer'},
                                            'verb':
                                                {'type': 'string'}
                                        }
                                    }
                                },
                                'regex': {'type': 'string'},
                                'uri': {'type': 'string'}
                            }
                        }
                    }
                },
                'required': ['absolute', 'rate']
            }
        },
        'required': ['limits']
    }
}
