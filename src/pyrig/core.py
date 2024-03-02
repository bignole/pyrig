import logging

from maya import cmds

LOG = logging.getLogger(__name__)


def create(node_type, name="", **kwargs):
    """"""
    # define a mapping table for node_types
    import pyrig.node
    import pyrig.name

    node_type_remap = {}

    # create kwargs
    kwargs["name"] = pyrig.name.validate_name(name, node_type)
    cls = node_type_remap.get(node_type, pyrig.node.Node)
    if node_type not in node_type_remap:
        kwargs["node_type"] = node_type

    return cls(**kwargs)

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

    if attr_name:
        return pyrig_node[attr_name]
    return pyrig_node

def create_attr(node, **kwargs):
    """"""
    obj = get(node)
    if not obj:
        raise TypeError("No object named '{}'.".format(node))
    return obj.add_attr(**kwargs)