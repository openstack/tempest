# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 IBM
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

from lxml import etree

XMLNS_11 = "http://docs.openstack.org/compute/api/v1.1"


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
        args = " ".join(['%s="%s"' % (k, v) for k, v in self._attrs.items()])
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
        args = " ".join(['%s="%s"' % (k, v) for k, v in self._attrs.items()])
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


def xml_to_json(node):
    """This does a really braindead conversion of an XML tree to
    something that looks like a json dump. In cases where the XML
    and json structures are the same, then this "just works". In
    others, it requires a little hand-editing of the result."""
    json = {}
    for attr in node.keys():
        json[attr] = node.get(attr)
    if not node.getchildren():
        return node.text or json
    for child in node.getchildren():
        tag = child.tag
        if tag.startswith("{"):
            ns, tag = tag.split("}", 1)
        json[tag] = xml_to_json(child)
    return json
