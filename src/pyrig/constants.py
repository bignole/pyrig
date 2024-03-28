
class MayaType(object):
    """"""
    dagNode = "dagNode"
    transform = "transform"
    joint = "joint"

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

    @staticmethod
    def maya_api_type(val):
        """"""
        ro_remap = {
            0: "kXYZ",
            1: "kYZX",
            2: "kZXY",
            3: "kXZY",
            4: "kYXZ",
            5: "kZYX",
            "xyz": "kXYZ",
            "yzx": "kYZX",
            "zxy": "kZXY",
            "xzy": "kXZY",
            "yxz": "kYXZ",
            "zyx": "kZYX",
        }
        return ro_remap[val]