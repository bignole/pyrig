import math

import maya.api.OpenMaya as om

from pyrig.constants import RotationFormalism, Unit, RotateOrder

class Mat44(om.MMatrix):
    """"""
    def __init__(self, *args, **kwargs):
        """"""
        if len(args) == 3:
            if all([isinstance(_, (tuple, list, om.MVector)) for _ in args]):
                args = [list(self._compose(args))]

        super(Mat44, self).__init__(*args, **kwargs)

    def _compose(self, *args, **kwargs):
        """"""
        angle_unit = kwargs.get("angle_unit", Unit.degree)
        rotate_order = kwargs.get("rotate_order", RotateOrder.xyz)

        if not isinstance(args[0], om.MVector):
            translate = om.MVector(translate)
        tMat.setTranslation(translate, om.MSpace.kWorld)

        tMat = om.MTransformationMatrix()
        tMat.reorderRotation(rotate_order)

        return tMat.asMatrix()


    def decompose(self, **kwargs):
        """"""
        rotation_formalism = kwargs.get("rotation", RotationFormalism.euler)
        angle_unit = kwargs.get("angle_unit", Unit.degree)
        rotate_order = kwargs.get("rotate_order", RotateOrder.xyz)

        # build transformationMatrix
        tMat = om.MTransformationMatrix(self)
        tMat.reorderRotation(rotate_order)
    
        # get translation
        mVector = tMat.translation(om.MSpace.kWorld)
        translate_ = list(mVector)

        # get rotation
        if rotation_formalism == RotationFormalism.quaternion:
            mQuat = tMat.rotation(om.MSpace.kWorld)
            rotate_ = list(mQuat)
        elif rotation_formalism == RotationFormalism.euler:
            mEuler = tMat.rotation()
            rotate_ = list(mEuler)
            if angle_unit == Unit.radian:
                rotate_ = [math.degrees(_) for _ in rotate_]

        # get scale
        scale_ = tMat.scale(om.MSpace.kWorld)
    
        return Vec3(translate_), Vec3(rotate_), Vec3(scale_)

class Vec3(om.MVector):
    """"""
    def __init__(self, *args, **kwargs):
        """"""
        super(Vec3, self).__init__(*args, **kwargs)