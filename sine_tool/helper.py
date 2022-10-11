from functools import wraps

import pymel.core as pm
from maya import cmds
import maya.OpenMaya as om
from pymel.core import datatypes


def one_undo(func):
    """Decorator - guarantee close chunk.

    type: (function) -> function

    """

    @wraps(func)
    def wrap(*args, **kwargs):
        # type: (*str, **str) -> None

        try:
            cmds.undoInfo(openChunk=True)
            return func(*args, **kwargs)

        except Exception as e:
            raise e

        finally:
            cmds.undoInfo(closeChunk=True)

    return wrap


def addNPO(objs=None, suffix="_npo", rename=False):
    """Add a transform node as a neutral pose

    Add a transform node as a parent and in the same pose of each of the
    selected objects. This way neutralize the local transfromation
    values.
    NPO stands for "neutral position" terminology from the all mighty
    Softimage ;)

    """
    npoList = []

    if not objs:
        objs = pm.selected()
    if not isinstance(objs, list):
        objs = [objs]
    for obj in objs:
        oParent = obj.getParent()
        oTra = pm.createNode("transform",
                             n=obj.name() + suffix,
                             p=oParent,
                             ss=True)
        oTra.setTransformation(obj.getMatrix())
        pm.parent(obj, oTra)
        npoList.append(oTra)
    if len(objs) == 1 and rename:
        npoList[0].rename(rename)
    return npoList


def addCurve(parent,
             name,
             points,
             close=False,
             degree=3,
             m=datatypes.Matrix()):
    """Create a NurbsCurve with a single subcurve.

    Arguments:
        parent (dagNode): Parent object.
        name (str): Name
        positions (list of float): points of the curve in a one dimension array
            [point0X, point0Y, point0Z, 1, point1X, point1Y, point1Z, 1, ...].
        close (bool): True to close the curve.
        degree (bool): 1 for linear curve, 3 for Cubic.
        m (matrix): Global transform.

    Returns:
        dagNode: The newly created curve.
    """
    if close:
        points.extend(points[:degree])
        knots = range(len(points) + degree - 1)
        node = pm.curve(n=name, d=degree, p=points, per=close, k=knots)
    else:
        node = pm.curve(n=name, d=degree, p=points)

    if m is not None:
        node.setTransformation(m)

    if parent is not None:
        parent.addChild(node)

    return node


@one_undo
def set_color(node, color):
    """Set the color in the Icons.

    Arguments:
        node(dagNode): The object
        color (int or list of float): The color in index base or RGB.


    """
    # on Maya version.
    # version = mgear.core.getMayaver()

    if isinstance(color, int):

        for shp in node.listRelatives(shapes=True):
            shp.setAttr("overrideEnabled", True)
            shp.setAttr("overrideColor", color)
    else:
        for shp in node.listRelatives(shapes=True):
            shp.overrideEnabled.set(1)
            shp.overrideRGBColors.set(1)
            shp.overrideColorRGB.set(color[0], color[1], color[2])


def getPointArrayWithOffset(point_pos, pos_offset=None, rot_offset=None):
    """Get Point array with offset

    Convert a list of vector to a List of float and add the position and
    rotation offset.

    Arguments:
        point_pos (list of vector): Point positions.
        pos_offset (vector):  The position offset of the curve from its
            center.
        rot_offset (vector): The rotation offset of the curve from its
            center. In radians.

    Returns:
        list of vector: the new point positions

    """
    points = []
    for v in point_pos:
        if rot_offset:
            mv = om.MVector(v.x, v.y, v.z)
            mv = mv.rotateBy(om.MEulerRotation(rot_offset.x,
                                               rot_offset.y,
                                               rot_offset.z,
                                               om.MEulerRotation.kXYZ))
            v = datatypes.Vector(mv.x, mv.y, mv.z)
        if pos_offset:
            v = v + pos_offset

        points.append(v)

    return points


def create(parent=None,
           name="icon",
           m=datatypes.Matrix(),
           color=[0, 0, 0],
           icon="cube",
           **kwargs):
    """Icon master function

    **Create icon master function.**
    This function centralize all the icons creation
    Returns:
        dagNode: The newly created icon.

    """
    if "w" not in kwargs.keys():
        kwargs["w"] = 1
    if "h" not in kwargs.keys():
        kwargs["h"] = 1
    if "d" not in kwargs.keys():
        kwargs["d"] = 1
    if "po" not in kwargs.keys():
        kwargs["po"] = None
    if "ro" not in kwargs.keys():
        kwargs["ro"] = None
    if "degree" not in kwargs.keys():
        kwargs["degree"] = 3

    if icon == "cube":
        ctl = cube(parent,
                   name,
                   kwargs["w"],
                   kwargs["h"],
                   kwargs["d"],
                   color,
                   m,
                   kwargs["po"],
                   kwargs["ro"])
    elif icon == "sphere":
        ctl = sphere(parent,
                     name,
                     kwargs["w"],
                     color,
                     m,
                     kwargs["po"],
                     kwargs["ro"],
                     kwargs["degree"])
    elif icon == "null":
        ctl = null(parent,
                   name,
                   kwargs["w"],
                   color,
                   m,
                   kwargs["po"],
                   kwargs["ro"])

    else:
        return pm.warning("invalid type of icon")

    return ctl


def cube(parent=None,
         name="cube",
         width=1,
         height=1,
         depth=1,
         color=[0, 0, 0],
         m=datatypes.Matrix(),
         pos_offset=None,
         rot_offset=None):
    """Create a curve with a CUBE shape.

    Arguments:
        parent (dagNode): The parent object of the newly created curve.
        name (str): Name of the curve.
        width (float): Width of the shape.
        height (float): Height of the shape.
        depth (float): Depth of the shape.
        color (int or list of float): The color in index base or RGB.
        m (matrix): The global transformation of the curve.
        pos_offset (vector): The xyz position offset of the curve
            from its center.
        rot_offset (vector): The xyz rotation offset of the curve
            from its center. xyz in radians

    Returns:
        dagNode: The newly created icon.
    """
    lenX = width * 0.5
    lenY = height * 0.5
    lenZ = depth * 0.5

    # p is positive, N is negative
    ppp = datatypes.Vector(lenX, lenY, lenZ)
    ppN = datatypes.Vector(lenX, lenY, lenZ * -1)
    pNp = datatypes.Vector(lenX, lenY * -1, lenZ)
    Npp = datatypes.Vector(lenX * -1, lenY, lenZ)
    pNN = datatypes.Vector(lenX, lenY * -1, lenZ * -1)
    NNp = datatypes.Vector(lenX * -1, lenY * -1, lenZ)
    NpN = datatypes.Vector(lenX * -1, lenY, lenZ * -1)
    NNN = datatypes.Vector(lenX * -1, lenY * -1, lenZ * -1)

    v_array = [ppp, ppN, NpN, NNN, NNp, Npp, NpN, Npp, ppp, pNp, NNp, pNp, pNN,
               ppN, pNN, NNN]

    points = getPointArrayWithOffset(v_array,
                                     pos_offset,
                                     rot_offset)

    node = addCurve(parent, name, points, False, 1, m)

    set_color(node, color)

    return node


def sphere(parent=None,
           name="sphere",
           width=1,
           color=[0, 0, 0],
           m=datatypes.Matrix(),
           pos_offset=None,
           rot_offset=None,
           degree=3):
    """Create a curve with a SPHERE shape.

    Arguments:
        parent (dagNode): The parent object of the newly created curve.
        name (str): Name of the curve.
        width (float): Width of the shape.
        color (int or list of float): The color in index base or RGB.
        m (matrix): The global transformation of the curve.
        pos_offset (vector): The xyz position offset of the curve from
            its center.
        rot_offset (vector): The xyz rotation offset of the curve from
            its center. xyz in radians

    Returns:
        dagNode: The newly created icon.

    """
    dlen = width * .5

    v0 = datatypes.Vector(0, 0, -dlen * 1.108)
    v1 = datatypes.Vector(dlen * .78, 0, -dlen * .78)
    v2 = datatypes.Vector(dlen * 1.108, 0, 0)
    v3 = datatypes.Vector(dlen * .78, 0, dlen * .78)
    v4 = datatypes.Vector(0, 0, dlen * 1.108)
    v5 = datatypes.Vector(-dlen * .78, 0, dlen * .78)
    v6 = datatypes.Vector(-dlen * 1.108, 0, 0)
    v7 = datatypes.Vector(-dlen * .78, 0, -dlen * .78)

    ro = datatypes.Vector([1.5708, 0, 0])

    points = getPointArrayWithOffset(
        [v0, v1, v2, v3, v4, v5, v6, v7], pos_offset, rot_offset)
    node = addCurve(parent, name, points, True, degree, m)

    if rot_offset:
        rot_offset += ro
    else:
        rot_offset = ro
    points = getPointArrayWithOffset(
        [v0, v1, v2, v3, v4, v5, v6, v7], pos_offset, rot_offset)
    crv_0 = addCurve(parent, node + "_0crv", points, True, degree, m)

    ro = datatypes.Vector([1.5708, 0, 1.5708])
    if rot_offset:
        rot_offset += ro
    else:
        rot_offset = ro
    points = getPointArrayWithOffset(
        [v0, v1, v2, v3, v4, v5, v6, v7], pos_offset, rot_offset + ro + ro)

    crv_1 = addCurve(parent, node + "_1crv", points, True, degree, m)

    for crv in [crv_0, crv_1]:
        for shp in crv.listRelatives(shapes=True):
            node.addChild(shp, add=True, shape=True)
        pm.delete(crv)

    set_color(node, color)

    return node


def null(parent=None,
         name="null",
         width=1,
         color=[0, 0, 0],
         m=datatypes.Matrix(),
         pos_offset=None,
         rot_offset=None):
    """Create a curve with a NULL shape.

    Arguments:
        parent (dagNode): The parent object of the newly created curve.
        name (str): Name of the curve.
        width (float): Width of the shape.
        color (int or list of float): The color in index base or RGB.
        m (matrix): The global transformation of the curve.
        pos_offset (vector): The xyz position offset of the curve from
            its center.
        rot_offset (vector): The xyz rotation offset of the curve from
            its center. xyz in radians

    Returns:
        dagNode: The newly created icon.

    """
    dlen = width * .5

    v0 = datatypes.Vector(dlen, 0, 0)
    v1 = datatypes.Vector(-dlen, 0, 0)
    v2 = datatypes.Vector(0, dlen, 0)
    v3 = datatypes.Vector(0, -dlen, 0)
    v4 = datatypes.Vector(0, 0, dlen)
    v5 = datatypes.Vector(0, 0, -dlen)

    points = getPointArrayWithOffset([v0, v1], pos_offset, rot_offset)
    node = addCurve(parent, name, points, False, 1, m)

    points = getPointArrayWithOffset([v2, v3], pos_offset, rot_offset)
    crv_0 = addCurve(parent, name, points, False, 1, m)

    points = getPointArrayWithOffset([v4, v5], pos_offset, rot_offset)
    crv_1 = addCurve(parent, name, points, False, 1, m)

    for crv in [crv_0, crv_1]:
        for shp in crv.listRelatives(shapes=True):
            node.addChild(shp, add=True, shape=True)
        pm.delete(crv)

    set_color(node, color)

    return node
