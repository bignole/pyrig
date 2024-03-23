import logging

from maya import cmds

import pyrig.core as pr
import pyrig.transform

LOG = logging.getLogger(__name__)


class Joint(pyrig.transform.Transform):
    """"""

    def __init__(self, *args, **kwargs):
        """Class __init__."""
        cmds.select(clear=True)
        kwargs.setdefault("node_type", "joint")
        super(Joint, self).__init__(*args, **kwargs)

    def _set_dag_parent(self, value, relative=True):
        """Override the dag_parent setter to remove jointOrients."""
        # sets the parent
        if value:
            self._inverse_parent(value)

        # Move in the outliner/DAG.
        matrix = self["worldMatrix"].value
        super(Joint, self)._set_dag_parent(value, relative)
        if self.jointOrient.exists():
            self.jointOrient.value = 0, 0, 0
        self.move_to(matrix)

    def _inverse_parent(self, value):
        # Grab the inverse parent and feed it into the live child.
        input_attr = self.translate.input or self.translateX.input
        if not input_attr:
            return

        input_node = input_attr.node
        dcc_type = input_node.dcc_type
        if dcc_type == "decomposeMatrix":
            decompose_attr = input_node.inputMatrix
            traversed_connection = decompose_attr.get_input()
            if traversed_connection:
                name = [self.name, "DAGParent"]
                mult = pr.create("LoomMatrixStack", name=name)
                mult.name.append_type()
                inverse = pr.create("inverseMatrix", name=name)
                inverse.name.append_type()

                # Connections.
                pr.get(value).worldMatrix >> inverse.inputMatrix
                traversed_connection >> mult.attr("stack[0]")
                inverse.outputMatrix >> mult.attr("stack[1]")

                # Remove the previous decompose matrix.
                input_node.delete()

                # Relink the Joint.
                self.link_to(mult.output)

    def compensate_scale(self):
        """Reconnect the scaleCompensate attributes."""
        parent = self.dag_parent
        if not parent or parent.node_type != "joint":
            return
        parent["scale"].connect(self["inverseScale"], connect_leaf=True)
