# Copyright 2012 IBM Corp.
# All Rights Reserved.
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

import collections

XMLNS_11 = "http://docs.openstack.org/compute/api/v1.1"
XMLNS_V3 = "http://docs.openstack.org/compute/api/v1.1"

NEUTRON_NAMESPACES = {
    'binding': "http://docs.openstack.org/ext/binding/api/v1.0",
    'router': "http://docs.openstack.org/ext/neutron/router/api/v1.0",
    'provider': 'http://docs.openstack.org/ext/provider/api/v1.0',
}


# NOTE(danms): This is just a silly implementation to help make generating
# XML faster for prototyping. Could be replaced with proper etree gorp
# if desired
class Element(object):
    def __init__(self, element_name, *args, **kwargs):
        self.element_name = element_name
        self._attrs = kwargs
        self._elements = list(args)

    def add_attr(self, name, value):
        self._attrs[name] = value

    def append(self, element):
        self._elements.append(element)

    def __str__(self):
        args = " ".join(['%s="%s"' %
                        (k, v if v is not None else "")
                        for k, v in self._attrs.items()])
        string = '<%s %s' % (self.element_name, args)
        if not self._elements:
            string += '/>'
            return string

        string += '>'

        for element in self._elements:
            string += str(element)

        string += '</%s>' % self.element_name

        return string

    def __getitem__(self, name):
        for element in self._elements:
            if element.element_name == name:
                return element
        raise KeyError("No such element `%s'" % name)

    def __getattr__(self, name):
        if name in self._attrs:
            return self._attrs[name]
        return object.__getattr__(self, name)

    def attributes(self):
        return self._attrs.items()

    def children(self):
        return self._elements


class Document(Element):
    def __init__(self, *args, **kwargs):
        if 'version' not in kwargs:
            kwargs['version'] = '1.0'
        if 'encoding' not in kwargs:
            kwargs['encoding'] = 'UTF-8'
        Element.__init__(self, '?xml', *args, **kwargs)

    def __str__(self):
        args = " ".join(['%s="%s"' %
                        (k, v if v is not None else "")
                        for k, v in self._attrs.items()])
        string = '<?xml %s?>\n' % args
        for element in self._elements:
            string += str(element)
        return string


class Text(Element):
    def __init__(self, content=""):
        Element.__init__(self, None)
        self.__content = content

    def __str__(self):
        return self.__content


def parse_array(node, plurals=None):
    array = []
    for child in node.getchildren():
        array.append(xml_to_json(child,
                     plurals))
    return array


def xml_to_json(node, plurals=None):
    """This does a really braindead conversion of an XML tree to
    something that looks like a json dump. In cases where the XML
    and json structures are the same, then this "just works". In
    others, it requires a little hand-editing of the result.
    """
    json = {}
    bool_flag = False
    int_flag = False
    long_flag = False
    for attr in node.keys():
        if not attr.startswith("xmlns"):
            json[attr] = node.get(attr)
            if json[attr] == 'bool':
                bool_flag = True
            elif json[attr] == 'int':
                int_flag = True
            elif json[attr] == 'long':
                long_flag = True
    if not node.getchildren():
        if bool_flag:
            return node.text == 'True'
        elif int_flag:
            return int(node.text)
        elif long_flag:
            return long(node.text)
        else:
            return node.text or json
    for child in node.getchildren():
        tag = child.tag
        if tag.startswith("{"):
            ns, tag = tag.split("}", 1)
            for key, uri in NEUTRON_NAMESPACES.iteritems():
                if uri == ns[1:]:
                    tag = key + ":" + tag
        if plurals is not None and tag in plurals:
                json[tag] = parse_array(child, plurals)
        elif tag == 'volume_attached':
            if 'os-extended-volumes:volumes_attached' not in json:
                json['os-extended-volumes:volumes_attached'] = []
            json['os-extended-volumes:volumes_attached'].append(xml_to_json(child, plurals))
        else:
            json[tag] = xml_to_json(child, plurals)
    return json


def deep_dict_to_xml(dest, source):
    """Populates the ``dest`` xml element with the ``source`` ``Mapping``
       elements, if the source Mapping's value is also a ``Mapping``
       they will be recursively added as a child elements.
       :param source: A python ``Mapping`` (dict)
       :param dest: XML child element will be added to the ``dest``
    """
    for element, content in source.iteritems():
        if isinstance(content, collections.Mapping):
            xml_element = Element(element)
            deep_dict_to_xml(xml_element, content)
            dest.append(xml_element)
        else:
            dest.append(Element(element, content))
