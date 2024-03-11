from pyrig.constants import MayaType

class BaseNode(object):
    """"""

    EXTEND_TYPE = None
    _inherited_dcc_types = []

    def _extend_object(self):
        """"""
        import pyrig.node
        import pyrig.transform

        EXTEND_REMAP = {
            MayaType.dagNode: pyrig.node.DagNode,
            MayaType.transform: pyrig.transform.Transform,
        }

        if not self.EXTEND_TYPE:
            return
        for _type in self.EXTEND_TYPE:
            if _type in self._inherited_dcc_types:
                self.__class__ = EXTEND_REMAP[_type]
                return self._extend_object()
