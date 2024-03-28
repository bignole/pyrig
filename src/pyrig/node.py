import logging
import six

from maya import cmds

import pyrig.core as pr
import pyrig.attribute
import pyrig.name

LOG = logging.getLogger(__name__)

USE_UUID = True

class Node(object):
    """Base class for nodes."""

    def __init__(self, name=None, node_type=None, parent=None, create=True):
        """_summary_

        Parameters
        ----------
        name : str, optional
            Node name, used node_type if not specified,.
            by default None
        node_type : str, optional
            Node type used by create_mode, undefined while retrieving.
            by default None
        parent : str/pyrig.node.Node, optional
            Parent of the node for the create_mode, undefined while retrieving
            by default None.
        create : bool, optional
            Toggle create_mode/retrieved_mode.
            by default True
        """

        self._name = pyrig.name.validate_name(name, node_type)
        self._name.node = self
        self._node = str(self.name)
        self._node_type = node_type

        # create the node
        if create:
            kwargs = {}
            kwargs["name"] = str(self._name)
            if parent:
                kwargs["parent"] = str(parent)
            self._node = cmds.createNode(node_type, skipSelect=True, **kwargs)
            self._name = pyrig.name.validate_name(self._node, node_type)
            self._name.node = self

        self._uuid = cmds.ls(self._node, uuid=True)[0]
        self._inherited_dcc_types = cmds.nodeType(self._node, inherited=True)

    # Builtin Methods ---
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
        
    # Properties ---
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

    # Methods ---
    def delete(self):
        """"""
        cmds.delete(self.node)

    # Methods - attribute
    def add_attr(self, attr="", **kwargs):
        """"""
        properties = pyrig.attribute.AttributeProperties(kwargs)

        # rename if specified
        for key in properties.copy():
            if key in ["ln", "longName"]:
                attr = properties.pop(key)

        return self[attr].create(**properties)
    
    def add_separator(self, name=None):
        """Create a unique separator attribute."""
        separator_name = self.get_unique_attr_name("separator")
        self.add_attr(
            separator_name,
            niceName=" " * 15,
            attributeType="enum",
            enumName=name if name else "-" * 15,
            visible=True,
            lock=True,
        )
    
    def get_unique_attr_name(self, attr_name, idx=None):
        """"""
        result = "{}{}".format(attr_name, idx or "")
        idx = 0
        while self[result].exists():
            idx += 1
            result = "{}{}".format(attr_name, idx)
        return result

    def attributes_property(
        self, attributes, lock=False, keyable=True, visible=True
    ):
        """"""
        # Validate none input.
        if attributes is None:
            return

        # Validate string input.
        if isinstance(attributes, six.string_types):
            attributes = [attributes]

        # Go through and lock the attributes.
        for attr in attributes:
            self[attr].lock = lock
            self[attr].visible = visible
            self[attr].keyable = keyable

    def lock_attributes(self, attributes=None, lock=True):
        """"""
        # Validate none input.
        if attributes is None:
            return

        # Validate string input.
        if isinstance(attributes, six.string_types):
            attributes = [attributes]

        # Go through and lock the attributes.
        for attr in attributes:
            self[attr].lock = lock

    def hide_attributes(self, attributes=None, hide=True):
        """"""
        # Validate none input.
        if attributes is None:
            return

        # Validate string input.
        if isinstance(attributes, six.string_types):
            attributes = [attributes]

        # Go through and lock the attributes.
        for attr in attributes:
            self[attr].visible = not hide

    # Class Methods ---
    @classmethod
    def retrieve(cls, name):
        """Convert given string to Node object."""
        if not cmds.objExists(name):
            msg = "Could not retrieve '{}'. It does not exist in the scene.".format(name)
            LOG.warning(msg)
            return None
        return cls(name=name, create=False)

class DagNode(Node):
    """"""

    def __init__(self, *args, **kwargs):
        """"""
        super(DagNode, self).__init__(*args, **kwargs)

    @property
    def parent(self):
        """"""
        parent = (cmds.listRelatives(self.node, parent=True) or [None])[0]
        return pr.get(parent)

    @parent.setter
    def parent(self, value):
        self._set_parent(value)

    def _set_parent(self, value, relative=False):
        """"""
        if value is None:
            cmds.parent(self, world=True, relative=relative)
        if not value:
            return
        if isinstance(value, six.string_types) and not pr.get(value):
            raise TypeError("Parent node {} doesn't exists".format(value))

        value = pr.get(value)
        if value.dag_parent and value.dag_parent.node == self.node:
            raise TypeError("Cannot parent an object to one of its children")
        elif self.dag_parent and self.dag_parent.node == value.node:
            LOG.debug("{} is already a child of {}".format(self, value))
            return
        cmds.parent(self, value, relative=relative)
