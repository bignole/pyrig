import six
import logging

from maya import cmds

import pyrig.core as pr
import pyrig.node

LOG = logging.getLogger(__name__)

class Container(pyrig.node.Node):
    """"""

    def __init__(self, *args, **kwargs):
        """"""
        super(Container, self).__init__(*args, **kwargs)

    # Properties ---
    @property
    def current(self):
        current = cmds.container(q=True, current=True)
        return True if current == self.node else False
    
    @current.setter
    def current(self, val):
        cmds.container(self.node, e=True, current=val)

    @property
    def members(self):
        return [pr.get(n) for n in cmds.container(self.node, q=True, nodeList=True)]
    
    @members.setter
    def members(self, val):
        if isinstance(val, six.string_types):
            val = [val]
        cmds.container(self.node, edit=True, addNode=val)
        diff = set(self.members).difference(val)
        cmds.container(self.node, edit=True, removeNode=diff)

    # Methods - overide
    def delete(self):
        """"""
        cmds.container(self.node, edit=True, removeContainer=True)

class DagContainer(Container, pyrig.transform.Transform):
    """"""

    def __init__(self, *args, **kwargs):
        """"""
        super(Container, self).__init__(*args, **kwargs)