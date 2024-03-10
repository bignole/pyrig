
class MayaType(object):
    """"""
    dagNode = "dagNode"
    transform = "transform"

class Format(object):
    """"""
    json = 0

class RotationFormalism(object):
    """"""
    euler = 0
    quaternion = 1

class Unit(object):
    """"""
    degree = 0
    radian = 1

class RotateOrder(object):
    """"""
    xyz = 0
    yzx = 1
    zxy = 2
    xzy = 3
    yxz = 4
    zyx = 5