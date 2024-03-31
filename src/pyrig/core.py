import logging

from maya import cmds

from pyrig.constants import *

LOG = logging.getLogger(__name__)


def create(type_, name="", **kwargs):
    """"""
    # define a mapping table for node_types
    import pyrig.name
    import pyrig.node
    import pyrig.transform
    import pyrig.joint

    node_type_remap = {
        "node": pyrig.node.Node,
        "helper": pyrig.transform.Helper,
        "joint": pyrig.joint.Joint
    }

    # create kwargs
    kwargs["name"] = pyrig.name.validate_name(name, type_)
    cls = node_type_remap.get(type_, pyrig.node.Node)

    if type_ not in node_type_remap:
        kwargs["node_type"] = type_
        inherited_types = cmds.nodeType(type_, isTypeName=True, inherited=True)
        cls = _find_cls_from_types(inherited_types)

    return cls(**kwargs)


def get(name):
    """"""
    import pyrig.node

    if name is None:
        return None
    
    # make sure its not already a Node
    if isinstance(name, pyrig.node.Node):
        return name

    # Check existence.
    retrived = cmds.ls(name)
    if len(retrived) == 0:
        msg = "'{}' does not exist in the graph.".format(name)
        LOG.debug(msg)
        return None
    if len(retrived) > 1:
        raise TypeError(
            "More than one object named '{}'.".format(name)
        )

    # check if it is a plug
    attr_name = None
    if "." in name:
        name, attr_name = name.split(".", 1)

    # determine proper class
    inherited_types = cmds.nodeType(name, inherited=True)
    cls = _find_cls_from_types(inherited_types)
    pyrig_node = cls.retrieve(name)

    if attr_name:
        return pyrig_node[attr_name]
    return pyrig_node


def create_attr(node, **kwargs):
    """"""
    obj = get(node)
    if not obj:
        raise TypeError("No object named '{}'.".format(node))
    return obj.add_attr(**kwargs)


def _find_cls_from_types(types):
    """"""
    import pyrig.node
    import pyrig.transform
    import pyrig.joint

    maya_type_remap = {
        MayaType.joint: pyrig.joint.Joint,
        MayaType.dagContainer: pyrig.container.DagContainer,
        MayaType.transform: pyrig.transform.Transform,
        MayaType.dagNode: pyrig.node.DagNode,
        MayaType.container: pyrig.container.Container,
    }

    for type_, cls in maya_type_remap.items():
        if type_ in types:
            return cls
    return pyrig.node.Node

class Types(object):
    """Datatypes class."""
    from pyrig.dataType import Mat44
    from pyrig.dataType import Vec3