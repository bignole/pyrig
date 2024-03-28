import math

import maya.api.OpenMaya as om

from pyrig.constants import RotationFormalism, Unit, RotateOrder

class Mat44(om.MMatrix):
    """"""
    def __init__(self, *args, **kwargs):
        """"""
        if len(args) >= 3:
            if all([isinstance(_, (tuple, list, om.MVector)) for _ in args]):
                args = self._compose(*args, **kwargs)
        if isinstance(args, om.MMatrix):
            args = [list(args)]

        super(Mat44, self).__init__(*args, **kwargs)

    # Builtin Methods ---
    def __repr__(self):
        return "dataType.{}{}".format(self.__class__.__name__, self)
    
    def __add__(self, obj):
        if isinstance(obj, Mat44):
            obj = obj._api_matrix
        return Mat44(self._api_matrix + obj)
    
    def __sub__(self, obj):
        if isinstance(obj, Mat44):
            obj = obj._api_matrix
        return Mat44(self._api_matrix - obj)
    
    def __mul__(self, obj):
        if isinstance(obj, Mat44):
            obj = obj._api_matrix
        return Mat44(self._api_matrix * obj)
    
    # Properties ---
    @property
    def translate(self):
        self.get_translate()
    
    @translate.setter
    def translate(self, val):
        self.set_translate(val)
    
    @property
    def rotate(self):
        return self.get_rotate()
    
    @rotate.setter
    def rotate(self, args):
        if isinstance(args[0], (tuple, list)):
            kwargs = {}
            if len(args) >= 2:
                kwargs["rotate_order"] = args[1]
            if len(args) >= 3:
                kwargs["angle_unit"] = args[2]
            self.set_rotate(val=args[0], **kwargs)
        else:
            self.set_rotate(val=args)
    
    @property
    def scale(self):
        return self.get_scale()
    
    @scale.setter
    def scale(self, val):
        self.set_scale(val)

    @property
    def shear(self):
        return self.get_shear()
    
    @shear.setter
    def shear(self, val):
        self.set_shear(val)

    # Methods ---
    def decompose(self, **kwargs):
        """"""
        translate = self.get_translate(*kwargs)
        rotate = self.get_rotate(**kwargs)
        scale = self.get_scale(**kwargs)
        shear = self.get_shear(**kwargs)

        return translate, rotate, scale, shear
    
    def pick(self, translate=False, rotate=False, scale=False, shear=False):
        """"""
        t, r, s, sh = self.decompose()
        if not translate:
            t = (0, 0, 0)
        if not rotate:
            r = (0, 0, 0)
        if not scale:
            s = (1, 1, 1)
        if not shear:
            sh = (0, 0, 0)
        return Mat44(t, r, s, sh)
    
    def get_translate(self, **kwargs):
        """"""
        mVector = self._api_tMat.translation(om.MSpace.kWorld)
        return list(mVector)

    def get_rotate(self, **kwargs):
        """"""
        rotation_formalism = kwargs.get("rotation", RotationFormalism.euler)
        angle_unit = kwargs.get("angle_unit", Unit.degree)
        rotate_order = kwargs.get("rotate_order", RotateOrder.xyz)

        # set rotate order
        kRotationOrder = getattr(
            om.MTransformationMatrix,
            RotateOrder.maya_api_type(rotate_order),
        )
        self._api_tMat.reorderRotation(kRotationOrder)

        # get rotation
        if rotation_formalism == RotationFormalism.quaternion:
            mQuat = self._api_tMat.rotation(om.MSpace.kWorld)
            rotate_ = list(mQuat)
        elif rotation_formalism == RotationFormalism.euler:
            mEuler = self._api_tMat.rotation()
            rotate_ = list(mEuler)
            if angle_unit == Unit.degree:
                rotate_ = [math.degrees(_) for _ in rotate_]

        return rotate_

    def get_scale(self, **kwargs):
        """"""
        return self._api_tMat.scale(om.MSpace.kWorld)
    
    def get_shear(self, **kwargs):
        """"""
        return self._api_tMat.shear(om.MSpace.kWorld)

    def set_translate(self, val, **kwargs):
        """"""
        _, rotate, scale, shear = self.decompose(**kwargs)
        self.__init__(val, rotate, scale, shear)

    def set_rotate(self, val, **kwargs):
        """"""
        translate, _, scale, shear = self.decompose(**kwargs)
        self.__init__(translate, val, scale, shear)

    def set_scale(self, val, **kwargs):
        """"""
        translate, rotate, _, shear = self.decompose(**kwargs)
        self.__init__(translate, rotate, val, shear)

    def set_shear(self, val, **kwargs):
        """"""
        translate, rotate, scale, _ = self.decompose(**kwargs)
        self.__init__(translate, rotate, scale, val)
    
    # Internal Methods ---
    @property
    def _api_matrix(self):
        return om.MMatrix(list(self))
    
    @property
    def _api_tMat(self):
        return om.MTransformationMatrix(self)

    @staticmethod
    def _compose(translate, rotate, scale, shear=(0, 0, 0), **kwargs):
        """"""
        api_tMat = om.MTransformationMatrix()

        # translate
        if not isinstance(translate, om.MVector):
            translate = om.MVector(translate)
        api_tMat.setTranslation(translate, om.MSpace.kWorld)

        rotate_order = kwargs.get("rotate_order", RotateOrder.xyz)
        angle_unit = kwargs.get("angle_unit", Unit.degree)

        # rotate
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
        api_tMat.setRotation(mRotate)

        # scale
        api_tMat.setScale(scale, om.MSpace.kWorld)
        # shear
        api_tMat.setShear(shear, om.MSpace.kWorld)

        return api_tMat.asMatrix()

class Vec3(om.MVector):
    """"""
    def __init__(self, *args, **kwargs):
        """"""
        super(Vec3, self).__init__(*args, **kwargs)

    # Builtin Methods ---
    def __repr__(self):
        return "dataType.{}{}".format(self.__class__.__name__, self)
