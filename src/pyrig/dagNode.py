import logging
import six

from maya import cmds

import pyrig.core as pr
import pyrig.maths.matrix
import pyrig.node

LOG = logging.getLogger(__name__)


class DagNode(pyrig.node.Node):
    """"""

    def __init__(self, *args, **kwargs):
        """"""
        super(DagNode, self).__init__(*args, **kwargs)

    @property
    def rotate_order(self):
        """"""
        return self["rotateOrder"].enums[self["rotateOrder"].value]

    @rotate_order.setter
    def rotate_order(self, value):
        index = self["rotateOrder"].enums.index(value)
        self["rotateOrder"].value = index

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

    def move_to(self, matrix):
        """Move to given matrix."""
        matrix_list = matrix
        if isinstance(matrix, pr.Types.Mat44):
            matrix = pyrig.maths.matrix.cleanup_matrix(matrix)
            matrix_list = matrix.to_list()
        pr.pycmds("xform", self.node, worldSpace=True, matrix=matrix_list)

    def snap_to(self, node):
        """Snap to given node."""
        node = pr.get(node)
        matrix = pyrig.maths.matrix.cleanup_matrix(node.worldMatrix.value)
        self.move_to(matrix)

    def link_to(self, attribute, maintain_offset=False):
        """Link matrix attribute to node's TRS.

        Args:
            attribute (Attribute): The pyrig Attribute class to drive the node
            maintain_offset (bool): Link the object whilst maintaining it's
                current position.
        """
        # Create decompose matrix.
        mdcp = pr.create("decomposeMatrix", name=self.name.copy())
        mdcp.name.append_type()

        if maintain_offset:
            # Construct name
            mult_name = attribute.node.name.copy(append="linker")
            mult_matrix = pr.create("LoomTransform", name=mult_name)
            mult_matrix.name.append_type()
            # Matrix Maths.
            inverse_parent = attribute.value.inverse()
            offset_matrix = inverse_parent * self.worldMatrix.value
            translate, rotate, scale = offset_matrix.decompose()
            # Connect to stack.
            attribute >> mult_matrix.attr("parent")
            mult_matrix.translate.value = translate
            mult_matrix.rotate.value = rotate
            mult_matrix.scale.value = scale
            mult_matrix.world_space >> mdcp.inputMatrix
        else:
            attribute >> mdcp.inputMatrix

        for xyz in "XYZ":
            mdcp.attr("outputTranslate" + xyz) >> self.attr("translate" + xyz)
            mdcp.attr("outputRotate" + xyz) >> self.attr("rotate" + xyz)
            mdcp.attr("outputScale" + xyz) >> self.attr("scale" + xyz)

    def offset_by(
        self, translate=(0, 0, 0), rotate=(0, 0, 0), scale=(1, 1, 1)
    ):
        """Offset current node by given matrix."""
        translation = pr.Types.Vec3(translate)
        rotation = pr.Types.Vec3(rotate)
        scale = pr.Types.Vec3(scale)
        offset = pr.Types.Mat44(translation, rotation, scale)
        self.move_to(self.worldMatrix.value * offset)

class Locator(DagNode):
    """Create Locator objects."""

    def __init__(self, *args, **kwargs):
        """Class __init__."""
        super(Locator, self).__init__(*args, **kwargs)
        self._shape = self._create_shape()

    def _create_shape(self):
        """Create the shape node."""
        name = self.name.copy(shape=True)
        shape = pr.create("node", node_type="locator", name=name, parent=self)
        return shape
