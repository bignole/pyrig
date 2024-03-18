import logging
import math

import maya.api.OpenMaya as om

import pyrig.core as pr
from pyrig.constants import RotationFormalism, Unit, RotateOrder

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

def compose(translate, rotate, scale, **kwargs):
    """"""
    angle_unit = kwargs.get("angle_unit", Unit.degree)
    rotate_order = kwargs.get("rotate_order", RotateOrder.xyz)

    tMat = om.MTransformationMatrix()
    if not isinstance(translate, om.MVector):
        translate = om.MVector(translate)
    tMat.setTranslation(translate, om.MSpace.kWorld)

    if len(rotate) == 4:  # RotationFormalism.quaternion
        tMat.setRotationQuaternion(rotate)
    elif len(rotate) == 3:  # RotationFormalism.euler
        if angle_unit == Unit.degree:
            rotate = [math.radians(_) for _ in rotate]
        tMat.setRotation(rotate, rotate_order)

    tMat.setScale(scale)

    return pr.Types.Mat44(tMat.asMatrix())
