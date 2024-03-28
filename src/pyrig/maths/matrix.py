import logging
import math

import maya.api.OpenMaya as om

import pyrig.core as pr
from pyrig.constants import Unit, RotateOrder

LOG = logging.getLogger(__name__)

def cleanup_matrix(matrix, precision=4):
    """Fix the matrix scale precision issue."""
    if not isinstance(matrix, pr.Types.Mat44):
        return matrix

    scale = pr.Types.Vec3(1.0, 1.0, 1.0)
    if scale == matrix.decompose()[2]:
        return matrix

    if all([round(x, precision) == 1.0 for x in matrix.decompose()[2]]):
        translation, rotation, _ = matrix.decompose()
        matrix = pr.Types.Mat44(translation, rotation, scale)

    return matrix

def compose(translate, rotate, scale, shear, **kwargs):
    """"""
    angle_unit = kwargs.get("angle_unit", Unit.degree)
    rotate_order = kwargs.get("rotate_order", RotateOrder.xyz)

    tMat = om.MTransformationMatrix()
    if not isinstance(translate, om.MVector):
        translate = om.MVector(translate)
    tMat.setTranslation(translate, om.MSpace.kWorld)

    if len(rotate) == 4:  # RotationFormalism.quaternion
        mRotate = om.MQuaternion(rotate)
    elif len(rotate) == 3:  # RotationFormalism.euler
        if angle_unit == Unit.degree:
            # convert to radian
            rotate = [math.radians(_) for _ in rotate]
        # set rotate order
        kRotationOrder = getattr(
            om.MEulerRotation,
            RotateOrder.maya_api_type(rotate_order),
        )
        mRotate = om.MEulerRotation(rotate, kRotationOrder)
    tMat.setRotation(mRotate)

    tMat.setScale(scale, om.MSpace.kWorld)

    return pr.Types.Mat44(tMat.asMatrix())
