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
        self._parent_attribute = None

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
    def dag_parent(self):
        """"""
        parent = (cmds.listRelatives(self.node, parent=True) or [None])[0]
        return pr.get(parent)

    @dag_parent.setter
    def dag_parent(self, value):
        self._set_dag_parent(value)

    def _set_dag_parent(self, value, relative=False):
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

    @property
    def parent(self):
        """Get the DCC parent relationship attribute."""
        return self._parent_attribute

    @parent.setter
    def parent(self, value):
        return self._set_parent(value)

    def _set_parent(self, attribute):
        """Set the parent relationship in a private method to allow override.

        Args:
            attribute (pyrig.attribute.Attribute): Matrix attribute input.
        """
        # Set private variable.
        self._parent_attribute = attribute

        # Matrix maths relevant for parent relationship.
        parent_matrix = attribute.value
        child_matrix = self.worldMatrix.value
        offset_matrix = parent_matrix.inverse() * child_matrix

        # Stack to mult the matrices.
        stack_node = pr.create("LoomTransform", name=self.name.copy())
        stack_node.name.append_type()

        # Connect Matrices.
        attribute >> stack_node.parent
        translate, rotate, scale = offset_matrix.decompose()
        stack_node.translate.value = translate
        stack_node.rotate.value = rotate
        stack_node.scale.value = scale

        # Create Decompose and connect to the node.
        mdcp = pr.create("decomposeMatrix", name=self.name.copy())
        mdcp.name.append_type()

        stack_node.world_space >> mdcp.inputMatrix
        for xyz in "XYZ":
            mdcp.attr("outputTranslate" + xyz) >> self.attr("translate" + xyz)
            mdcp.attr("outputRotate" + xyz) >> self.attr("rotate" + xyz)
            mdcp.attr("outputScale" + xyz) >> self.attr("scale" + xyz)

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

    def get_unique_attr_name(self, attr_name, idx=None):
        """Make sure the given attribute name is unique.

        Args:
            attr_name (str): Name of the attribute to check.
            idx (int): Specify an ending index.

        Returns:
            str: The new (if applicable) name.
        """
        result = "{}{}".format(attr_name, idx or "")
        idx = 0
        while pr.pycmds("attributeQuery", result, node=self.node, exists=True):
            idx += 1
            result = "{}{}".format(attr_name, idx)
        return result

    def add_separator(self, nice_name="Separator"):
        """Create a unique separator attribute.

        Args:
            nice_name (str): Give a nice name to the attribute.
        """
        separator_name = self.get_unique_attr_name("separator")
        pr.pycmds(
            "addAttr",
            self.node,
            longName=separator_name,
            niceName=nice_name,
            attributeType="enum",
            enumName="--------------",
        )
        self.attr(separator_name).visible = True

    def attributes_property(
        self, attributes, lock=False, keyable=True, visible=True
    ):
        """Change attributes properties on the node.

        Args:
            attributes (list): List of attributes to lock or unlock.
            lock (bool): Lock when True, and unlock when False.
            keyable (bool): Set keyable when True, and non-keyable when False.
            visible (bool): Hide when True, and show when False.
        """
        # Validate string input.
        if isinstance(attributes, six.string_types):
            attributes = [attributes]

        # Validate none input.
        if attributes is None:
            LOG.warning("No attributes were selected to hide.")
            return

        # Go through and lock the attributes.
        for attr in attributes:
            self.attr(attr).locked = lock
            self.attr(attr).visible = visible
            self.attr(attr).keyable = keyable

    def lock_attributes(self, attributes=None, lock=True):
        """Lock multiple attributes on the node.

        Args:
            attributes (list): List of attributes to lock or unlock.
            lock (bool): Lock when True, and unlock when False.
        """
        # Validate string input.
        if isinstance(attributes, six.string_types):
            attributes = [attributes]

        # Validate none input.
        if attributes is None:
            LOG.warning("No attributes were selected to hide.")
            return

        # Go through and lock the attributes.
        for attr in attributes:
            self.attr(attr).locked = lock

    def hide_attributes(self, attributes=None, hide=True):
        """Hide multiple attributes on the node.

        Args:
            attributes (list): List of attributes to hide.
            hide (bool): Hide when True, and show when False.
        """
        # Validate string input.
        if isinstance(attributes, six.string_types):
            attributes = [attributes]

        # Validate none input.
        if attributes is None:
            LOG.warning("No attributes were selected to hide.")
            return

        # Go through and lock the attributes.
        for attr in attributes:
            self.attr(attr).visible = not hide


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
