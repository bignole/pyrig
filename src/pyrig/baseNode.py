from pyrig.constants import MayaType

class BaseNode(object):
    """"""

    EXTEND_TYPE = None
    _inherited_dcc_types = []

    def _extend_object(self):
        """"""
        import pyrig.node
        import pyrig.transform
        import pyrig.joint

        EXTEND_REMAP = {
            MayaType.dagNode: pyrig.node.DagNode,
            MayaType.transform: pyrig.transform.Transform,
            MayaType.joint: pyrig.joint.Joint
        }

        for _type in self.EXTEND_TYPE or []:
            if _type in self._inherited_dcc_types:
                self.__class__ = EXTEND_REMAP[_type]
                return self._extend_object()
        return self
