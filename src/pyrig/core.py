import logging

from maya import cmds

LOG = logging.getLogger(__name__)


def create(type_, name="", **kwargs):
    """"""
    # define a mapping table for node_types
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
    return cls(**kwargs)._extend_object()

def get(name):
    """"""
    import pyrig.node

    # Check existence.
    if name is None:
        return None

    retrived = cmds.ls(name)
    if len(retrived) == 0:
        msg = "'{}' does not exist in the graph.".format(name)
        LOG.debug(msg)
        return None
    if len(retrived) > 1:
        raise TypeError(
            "More than one object named '{}'.".format(name)
        )

    # make sure its not already a Node
    if isinstance(name, pyrig.node.Node):
        return name

    # check if it is a plug
    attr_name = None
    if "." in name:
        name, attr_name = name.split(".", 1)

    pyrig_node = pyrig.node.Node(name=name, create=False)
    pyrig_node._extend_object()

    if attr_name:
        return pyrig_node[attr_name]
    return pyrig_node

def create_attr(node, **kwargs):
    """"""
    obj = get(node)
    if not obj:
        raise TypeError("No object named '{}'.".format(node))
    return obj.add_attr(**kwargs)

class Types(object):
    """Datatypes class."""
    from pyrig.dataType import Mat44
    from pyrig.dataType import Vec3

class Cls(object):
    """Constants class."""
    from pyrig.constants import MayaType
    from pyrig.constants import Format
    from pyrig.constants import RotationFormalism
    from pyrig.constants import Unit
    from pyrig.constants import RotateOrder