import logging
import six
import json
from collections import UserDict

import maya.api.OpenMaya as om
from maya import cmds

import pyrig.core as pr
from pyrig.constants import Format
import pyrig.name

LOG = logging.getLogger(__name__)

FORCE_LOCK = False
FORCE_CONNECTION = True
CONNECT_LEAF = False

# TODO call in, call out

class Attribute(object):
    """"""

    def __init__(self, node_object, attr_name):
        """_summary_

        Parameters
        ----------
        node_object : pyrig.node.Node
            Attribute holder node.
        attr_name : str
            Attribute name.
        """
        self._node_object = node_object
        self._attr_name = pyrig.name.AttributName(attr_name)
        self._attr_name.node = node_object

    # Builtin Methods
    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.plug)

    def __str__(self):
        return self.plug

    def __rshift__(self, plug):
        """Enables Attribute >> Attribute"""
        return self.connect(plug, force_connection=True)
    
    def __ge__(self, plug):
        """Enables Attribute >= Attribute"""
        return self.insert(plug, force_connection=True)

    def __floordiv__(self, plug):
        """Enables Attribute // Attribute"""
        return self.disconnect(plug)
    
    def __getitem__(self, key):
        """Enables Attribute[str/int]"""
        if isinstance(key, six.string_types):
            return Attribute(self.node, "{}.{}".format(self.attr, key))
        elif isinstance(key, int):
            key = self.get_next_available_index() if key == -1 else key
            return Attribute(self.node, "{}[{}]".format(self.attr, key))

    # Properties
    @property
    def name(self):
        return self._attr_name

    @property
    def node(self):
        """"""
        return self._node_object

    @property
    def attr(self):
        """"""
        return str(self._attr_name)

    @property
    def plug(self):
        """"""
        return self._attr_name.plug
    
    @property
    def type(self):
        """"""
        try:
            return cmds.getAttr(self.plug, typ=True)
        except:
            return "unknown"

    @property
    def value(self):
        """"""
        return self.get_value()

    @value.setter
    def value(self, val):
        self.set_value(val)

    @property
    def default(self):
        """"""
        dv = self._attribute_query(listDefault=True)
        if not dv:
            if self.type == "matrix":
                dv = pr.Types.Mat44()
            elif self.type == "string":
                dv = ""
        if isinstance(dv, list):
            if len(dv) == 1:
                dv = dv[0]
        return dv

    @default.setter
    def default(self, val):
        cmds.addAttr(self.plug, e=True, dv=val)

    @property
    def lock(self):
        """"""
        return cmds.getAttr(self.plug, l=True)

    @lock.setter
    def lock(self, val):
        cmds.setAttr(self.plug, l=val)

    @property
    def keyable(self):
        """"""
        return cmds.getAttr(self.plug, k=True)

    @keyable.setter
    def keyable(self, val):
        if val is True:
            cmds.setAttr(self.plug, cb=True)
            cmds.setAttr(self.plug, k=True)
        elif val is False:
            cbox = self.visible
            cmds.setAttr(self.plug, k=False, cb=cbox)

    @property
    def visible(self):
        """"""
        return self.keyable or cmds.getAttr(self.plug, cb=True)

    @visible.setter
    def visible(self, val):
        if val is True:
            cmds.setAttr(self.plug, cb=not self.keyable, k=self.keyable)
        elif val is False:
            cmds.setAttr(self.plug, k=False, cb=False)

    @property
    def min(self):
        """"""
        if self._attribute_query(minExists=True):
            return self._attribute_query(min=True)
        return None

    @min.setter
    def min(self, val):
        cmds.addAttr(self.plug, e=True, min=val)

    @property
    def max(self):
        """"""
        if self._attribute_query(maxExists=True):
            return self._attribute_query(max=True)
        return None

    @max.setter
    def max(self, val):
        cmds.addAttr(self.plug, e=True, max=val)

    @property
    def input(self):
        """"""
        return self.get_input()
    
    @input.setter
    def input(self, plug):
        self.set_input(plug)

    @property
    def outputs(self):
        """"""
        return self.get_outputs()

    @property
    def enums(self):
        """"""
        enums = self._attribute_query(listEnum=True)
        if enums:
            enums = enums[0].split(":")
        return enums

    @property
    def parent(self):
        """"""
        if self.name.index is not None:
            return pr.get("{}.{}".format(self.node, self.name.unindexed()))

        parent_attr_name = self._attribute_query(listParent=True)
        if not parent_attr_name:
            return None
        
        return pr.get("{}.{}".format(self.node, parent_attr_name[0]))

    @property
    def children(self):
        """"""
        children = self._attribute_query(listChildren=True)
        if not children:
            return None
        children_attr = ["{}.{}".format(self.attr, child) for child in children]
        return [pr.get("{}.{}".format(self.node, child)) for child in children_attr]

    # Properties - multi-attr
    @property
    def valid_indices(self):
        """"""
        return cmds.getAttr(self.plug, multiIndices=True) or []
    
    @property
    def size(self):
        """"""
        return len(self.valid_indices)
    
    @property
    def valid_plugs(self):
        """"""
        return [self[i] for i in self.valid_indices]

    @property
    def next_available_plug(self):
        """"""
        multi_index = self.get_next_available_index()
        return self[multi_index]

    # Properties - info
    @property
    def properties(self):
        """Get all attribute properties as dict.

        :return: Cls(userDict) filled with attribute properties.
        :rtype: pyrig.attribute.AttributeProperties
        """
        return AttributeProperties.retrieve(self)

    # Methods
    def exists(self):
        """"""
        return self._attribute_query(unindexed=False, exists=True)
    
    def create(self, **kwargs):
        """"""
        if self.exists():
            LOG.warning("'{}' already exists.".format(self.plug))
            return

        properties = AttributeProperties(kwargs)

        flags = {}
        #properties = [p for p in dir(Attribute) if isinstance(getattr(Attribute, p), property)]
        for key, value in properties.copy().items():
            if hasattr(Attribute, key):
                flags[key] = value
                del properties[key]

        # rename if specified
        for arg in properties.copy():
            if arg in ["ln", "longName"]:
                self._attr_name = pyrig.name.AttributName(properties.pop(arg))

        # keyable if not specified
        if not any(key in properties for key in ["k", "keyable"]):
            properties["keyable"] = True

        cmds.addAttr(str(self.node), ln=self.attr, **properties)

        for name, value in flags.items():
            setattr(self, name, value)

        return self

    def set_value(self, value, format=None, **kwargs):
        """"""
        force_lock = kwargs.get("force_lock", FORCE_LOCK)

        if value is None:
            value = self.default

        if format:
            value = self._data_format(value, format)

        self._force_lock(store=force_lock)

        # openMaya cls
        if isinstance(value, (om.MMatrix, om.MVector)):
            value = list(value)
        elif isinstance(value, (om.MPoint)):
            value = list(value)[:-1]
        # Simple
        if isinstance(value, (int, float, bool)):
            cmds.setAttr(self.plug, value)
        # String
        elif isinstance(value, (str, six.text_type)):
            cmds.setAttr(self.plug, value, type="string")
        # Matrix_list/Float3
        elif isinstance(value, (list, tuple)):
            if len(value) == 16:  # matrix
                cmds.setAttr(self.plug, *value, type="matrix")
            if len(value) == 3:  # vector
                cmds.setAttr(self.plug, *value, type="float3")

        self._force_lock(restore=force_lock)
    
    def get_value(self, format=None):
        """"""
        value = cmds.getAttr(self.plug, silent=True)

        if format:
            value = self._data_format(value, format, loads=True)

        if isinstance(value, list):
            if len(value) == 1:
                # remove "list in list" (eg. node[translate].value)
                value = value[0]
            if len(value) == 16:
                # matrix class
                value = pr.Types.Mat44(value)

        return value
    
    def get_input(self):
        """"""
        input_ = cmds.listConnections(self.plug, s=True, d=False, p=True)
        return pr.get(input_[0]) if input_ else None
    
    def set_input(self, plug, **kwargs):
        """"""
        force_lock = kwargs.get("force_lock", FORCE_LOCK)
        force_connection = kwargs.get("force_co", FORCE_CONNECTION)
        connect_leaf = kwargs.get("chidren_co", CONNECT_LEAF)
        skip = kwargs.get("skip", [])

        if plug is None:
            self.disconnect(**kwargs)
            return
        
        if not isinstance(plug, Attribute):
            plug = pr.get(plug)
        
        if connect_leaf:
            if self.children:
                attr_to_skip = []
                for attr in [Attribute(self, attr) for attr in skip]:
                    if attr.exists():
                        attr_to_skip.append(attr.name.long)
                if not plug.children:
                    for destination_child in self.children:
                        if not destination_child in attr_to_skip:
                            destination_child.set_input(plug, **kwargs)
                    return
                else:
                    if len(self.children) == len(plug.children):
                        for destination_child, source_child in zip(
                            self.children, plug.children
                        ):
                            if not destination_child.attr in attr_to_skip:
                                destination_child.set_input(source_child, **kwargs)
                        return

        self._force_lock(store=force_lock)
        cmds.connectAttr(plug.plug, self.plug, f=force_connection)
        self._force_lock(restore=force_lock)

    def get_outputs(self):
        """"""
        outputs = cmds.listConnections(self.plug, s=False, d=True, p=True)
        return [pr.get(x) for x in outputs or []]

    def connect(self, plug, **kwargs):
        """"""
        if not isinstance(plug, Attribute):
            plug = pr.get(plug)
        plug.set_input(self, **kwargs)

    def disconnect(self, plug=None, **kwargs):
        """"""
        if plug:
            if not isinstance(plug, Attribute):
                plug = pr.get(plug)
            if cmds.isConnected(self.plug, str(plug)):
                plug.break_connections(input=True, output=False, **kwargs)
            return

        self.break_connections(input=True, output=False, **kwargs)

    def break_connections(self, input=False, output=True, **kwargs):
        """"""
        force_lock = kwargs.get("force_lock", FORCE_LOCK)
        if input is True:
            self._force_lock(store=force_lock)
            plugs = cmds.listConnections(self.plug, s=True, d=False, p=True)
            if plugs:
                cmds.disconnectAttr(plugs[0], self.plug)
            self._force_lock(restore=force_lock)

        if output is True:
            for out_plug in self.outputs:
                out_plug.break_connection(input=True, output=False, **kwargs)

    def insert(self, plug, **kwargs):
        """"""
        if not isinstance(plug, Attribute):
            plug = pr.get(plug)

        plug.shift(recursive=True, **kwargs)
        self.connect(plug, **kwargs)

    def shift(self, **kwargs):
        """"""
        if self.name.index is not None:
            valid_indices = self.parent.valid_indices
            self._move_to_next_index(valid_indices=valid_indices, **kwargs)

    def reset(self, **kwargs):
        """"""
        force_lock = kwargs.get("force_lock", FORCE_LOCK)

        if not force_lock and self.lock == True:
            return
        self.lock = False
        self.input = None
        self.value = None

    # Methods - multi-attr
    def is_multi(self):
        """"""
        try:
            self._attribute_query(unindexed=False, multi=True)
        except:
            return False

    def get_next_available_index(self):
        """"""
        for i, multi_index in enumerate(self.valid_indices):
            if i != multi_index:
                return i
        return len(self.valid_indices)

    # Internal Methods
    def _attribute_query(self, unindexed=True, **kwargs):
        """"""
        attr_name = self.name[-1].unindexed() if unindexed else str(self.name[-1])
        return cmds.attributeQuery(attr_name, node=str(self.node), **kwargs)

    def _force_lock(self, store=False, restore=False):
        """"""
        if store:
            self._locked = self.lock
            if self._locked:
                self.lock = False
        if restore:
            if self._locked:
                self.lock = True

    def _move_to_next_index(self, **kwargs):
        """Recursive."""
        valid_indices = kwargs.get("valid_indices", None)
        recursive = kwargs.get("recursive", True)

        next_index = self.name.index + 1
        next_plug = Attribute(
            self.node, "{}[{}]".format(
                self.name.unindexed(), next_index
            )
        )

        if next_index in valid_indices:
            if recursive:
                next_plug._move_to_next_index(**kwargs)

        next_plug.set_value(self.value, **kwargs)
        next_plug.set_input(self.input, **kwargs)
        next_plug.lock = self.lock
        
        self.reset(**kwargs)

    def _data_format(self, value, format, loads=False):
        """Supported format : json"""

        if format == Format.json:
            return json.loads(value) if loads else json.dumps(value)
        else:
            msg = (
                "'{}' is not supported data format.\n"
                "Supported format : 'json'"
            ).format(format)
            LOG.warning(msg)

class AttributeProperties(UserDict):
    """"""
    def __init__(self, *args, **kwargs):
        """"""
        super(AttributeProperties, self).__init__(*args, **kwargs)

    # Builtin Methods ---
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.data)
    
    # Methods ---
    def delete_names(self):
        """"""
        for key in ["longName", "niceName", "shortName"]:
            if key in self.data:
                del self.data[key]
    
    # Class Methods ---
    @classmethod
    def retrieve(cls, attr):
        """"""
        attr_name = str(attr)
        if not isinstance(attr, Attribute):
            attr = pr.get(attr)
        if not attr:
            msg = "Could not retrieve '{}'. It does not exist in the scene.".format(attr_name)
            LOG.warning(msg)
            return None

        data = {}
        # names
        for key in ["long", "nice", "short"]:
            val = getattr(attr.name, key)
            if val is not None:
                data["{}Name".format(key)] = val

        # state
        data["hidden"] = attr._attribute_query(hidden=True)
        data["keyable"] = attr.keyable
        data["lock"] = attr.lock

        # multi
        if attr.is_multi():
            data["multi"] = True

        # dataType/attributeType
        attribute_type = attr.type
        if attribute_type in ["string", "matrix"]:
            data["dataType"] = attribute_type
        else:
            data["attributeType"] = attribute_type

        # value parameters
        if attribute_type in ["long", "double", "bool"]:
            data["defaultValue"] = attr.default
            for key in ["max", "min"]:
                val = getattr(attr, key)
                if val is not None:
                    data["{}Value".format(key)] = val

        if attribute_type in ['enum']:
            data['enumName'] = attr.enums

        # hierarchy
        parent = attr.parent
        if parent is not None:
            data['parent'] = parent

        return cls(data)
