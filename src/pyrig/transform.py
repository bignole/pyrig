import logging
import six

import maya.api.OpenMaya as om
from maya import cmds

import pyrig.core as pr
import pyrig.maths.matrix
import pyrig.node

LOG = logging.getLogger(__name__)

class Transform(pyrig.node.DagNode):
    """"""
    EXTEND_TYPE = None

    def __init__(self, *args, **kwargs):
        """"""
        super(Transform, self).__init__(*args, **kwargs)

    # Properties
    @property
    def rotate_order(self):
        """"""
        return self["rotateOrder"].enums[self["rotateOrder"].value]

    @rotate_order.setter
    def rotate_order(self, value):
        if isinstance(value, six.string_types):
            value = self["rotateOrder"].enums.index(value)
        self["rotateOrder"].value = value

    @property
    def shape(self):
        """"""
        return self._get_shape() or None

    def _get_shape(self):
        """"""
        return [pr.get(each) for each in cmds.listRelatives(self, shapes=True)]

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

    # Methods
    def move_to(self, matrix):
        """Move to given matrix."""
        if isinstance(matrix, om.MMatrix):
            matrix = pyrig.maths.matrix.cleanup_matrix(matrix)
            matrix = list(matrix)
        cmds.xform(self.node, worldSpace=True, matrix=matrix)

    def snap_to(self, node, **kwargs):
        """Snap to given node."""
        cmds.matchTransform(self, node, **kwargs)

    def link_to(self, attribute, maintain_offset=False, skip=[]):
        """"""
        # Create decompose matrix.
        dcm = pr.create("decomposeMatrix", name=self.name.copy())
        dcm.name.append_type()

        if maintain_offset:
            # Construct name
            mmx_name = attribute.node.name.copy(append="linker")
            mmx = pr.create("multMatrix", name=mmx_name)
            mmx.name.append_type()
            # Compute offset
            parent_inverse = attribute.value.inverse()
            offset_matrix = self["matrix"].value * parent_inverse
            # Connect to multMatrix
            mmx["matrixIn"][0].value = offset_matrix
            attribute >> mmx["matrixIn"][1]
            mmx["matrixSum"] >> dcm["inputMatrix"]
        else:
            attribute >> dcm["inputMatrix"]

        for channel in ["translate", "rotate", "scale"]:
            if not channel in [self[_].name.long for _ in skip]:
                dcm[channel].connect(self[channel], connect_leaf=True, skip=skip)

    def offset_by(
        self, translate=(0, 0, 0), rotate=(0, 0, 0), scale=(1, 1, 1), worldSpace=False
    ):
        """Offset current node by given matrix."""
        translation = pr.Types.Vec3(translate)
        rotation = pr.Types.Vec3(rotate)
        scale = pr.Types.Vec3(scale)
        offset = pr.Types.Mat44(translation, rotation, scale)
        if worldSpace:
            self.move_to(offset * self["worldMatrix"].value)
        else:
            self.move_to(offset * self["worldMatrix"].value)

class Locator(Transform):
    """Create Locator objects."""

    def __init__(self, *args, **kwargs):
        """Class __init__."""
        kwargs.setdefault("node_type", "transform")
        super(Locator, self).__init__(*args, **kwargs)
        self._shape = self._create_shape()

    def _create_shape(self):
        """Create the shape node."""
        name = self.name.copy(shape=True)
        shape = pr.create("node", node_type="locator", name=name, parent=self.node)
        return shape


