import logging

import pyrig.core as pr
import pyrig.container

LOG = logging.getLogger(__name__)

class Control(pyrig.container.DagContainer):
    """"""

    def __init__(self, *args, **kwargs):
        """"""
        kwargs.setdefault("node_type", "dagContainer")
        super(Control, self).__init__(*args, **kwargs)

        if kwargs.get("create"):
            # create default attributes

            # create network
            self._create_network()

            # Set Properties
            self["inheritTransform"].value = False

            # Configure Existing Attributes.
            self["visibility"].keyable = False
            self["visibility"].visible = False
            self["rotateOrder"].visible = True

    def _create_network(self):
        """"""
        mmx = pr.create("multMatrix", name=self.name.copy())
        mmx["matrixSum"] >> self["offsetParentMatrix"]
        self.members += [mmx]

    def canceled_transform(self):
        """"""
        mmx = pr.create("multMatrix", name=self.name.copy())
        self["offsetParentMatrix"].input >> mmx["matrixIn"][1]
        self["inverseMatrix"] >> mmx["matrixIn"][0]
        mmx["matrixSum"] >> self["offsetParentMatrix"]
        self.members += [mmx]