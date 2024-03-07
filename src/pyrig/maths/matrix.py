import logging
import math

import maya.api.OpenMaya as om

import pyrig.core as pr

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

def compose(
    translate=(0, 0, 0),
    rotate=(0, 0, 0),
    scale=(1, 1, 1),
    angle_unit="degree",
    rotate_order="xyz"
):
    """"""
    tMat = om.MTransformationMatrix()

    if not isinstance(translate, om.MVector):
        translate = om.MVector(translate)
    tMat.setTranslation(translate, om.MSpace.kWorld)

    if angle_unit == "degree":
        rotate = (math.radians(_) for _ in rotate)
    tMat.setRotation(rotate)

    tMat.setScale(scale)

    return tMat.asMatrix()
