import logging

from maya import cmds

import pyrig.attribute
import pyrig.name

LOG = logging.getLogger(__name__)

USE_UUID = True


class Node(object):
    """"""

    def __init__(self, name=None, node_type=None, parent=None, create=True):
        """"""
        self._name = pyrig.name.validate_name(name, node_type)
        self._name.node = self
        self._node = name

        # create the node
        if create:
            kwargs = {}
            kwargs["name"] = str(self._name)
            if parent:
                kwargs["parent"] = parent
            self._node = cmds.createNode(node_type, skipSelect=True, **kwargs)
            self._name = pyrig.name.validate_name(self._node, node_type)
            self._name.node = self

        self._uuid = cmds.ls(self._node, uuid=True)[0]
        self._node_type = node_type

    # Builtin Methods
    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.node)
        
    def __str__(self):
        return self.node
    
    def __add__(self, val):
        """Enables Node + str"""
        return "{}{}".format(self.node, val)
    
    def __getitem__(self, key):
        """Enables Node[str]"""
        return self.attr(key)
    
    def attr(self, key):
        """"""
        return pyrig.attribute.Attribute(self, key)
        
    # Properties
    @property
    def name(self):
        """"""
        return self._name

    @name.setter
    def name(self, val):
        self._name = pyrig.name.validate_name(val, self.node_type)
        self._name.node = self
        cmds.rename(self.node, str(self._name))

    @property
    def node(self):
        """"""
        if USE_UUID:
            node = cmds.ls(self.uuid)
            return node[0] if node else self._node
        return self._node

    @property
    def uuid(self):
        """"""
        return self._uuid

    @property
    def node_type(self):
        """"""
        if not self._node_type:
            self._node_type = self.dcc_type
        return self._node_type

    @property
    def dcc_type(self):
        """"""
        try:
            return cmds.nodeType(self.node)
        except:
            return "unknown"

    @property
    def exists(self):
        """"""
        return cmds.objExists(self.node)

    # Methods
    def delete(self):
        """"""
        cmds.delete(self.node)

    def add_attr(self, attr="", **kwargs):
        """"""
        for arg in kwargs:
            if arg in ["ln", "longName"]:
                attr = kwargs.pop(arg)
        return self[attr].create(**kwargs)