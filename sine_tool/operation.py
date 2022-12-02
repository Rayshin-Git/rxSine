import pymel.core as pm
from mgear.rigbits import connectWorldTransform
from pymel.core import datatypes
from pymel.core.datatypes import Point, Vector, Matrix
from mgear.core.applyop import gear_matrix_cns
from mgear.core.node import add_controller_tag

from .helper import addNPO, addJoint, create_ctl, addCnstJnt, \
    lock_attrs, create_group, get_average_distance_on_curve, \
    get_defaultMatrix, addParentJnt, getWalkTag


def alphabet_index(index):
    if index > 26 * 26:
        return pm.warning("number too big")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # noqa
    index_name = ""
    loop = alphabet[int(index / 26)] if int(index / 26) > 0 else ""
    index_name = loop + alphabet[int(index % 26)]
    return index_name


# grp naming
MASTER_GRP_NAME = "Sine_Grp"
MASTER_CTRL_GRP_NAME = "Sine_MasterGrp"
ELEMENT_Grp = "Sine_{_name}"
FK_Grp = "Sine_{_name}_{_chain_index}_FK"
SIK_Grp = "Sine_{_name}_{_chain_index}_SIK"


class SplineIKSetup:
    """
    Spline IK constructions for single chain
    """

    def __init__(self, slaves, matrices, config, index, parent=None):
        """
        getting the attributes from parent SineSetup for generate the Spline IK setup
        """
        # attrs
        self.curve = None
        self.effector = None
        self.handle = None
        self.name = config["name"]
        self.ik_size = config["ik_size"]
        self.ik_count = config["ik_count"]
        self.color = config["color"]
        self.slaves = slaves
        self.matrices = matrices
        self.index = index
        self.parent = parent

        self.ik_grp = None
        self.jnt_ik = []

        self.ik_base_name = ELEMENT_Grp.format(_name=self.name) + "_"
        self.IK_chain_Grp_name = SIK_Grp.format(_name=self.name, _chain_index=alphabet_index(self.index))

        # steps
        self.create_base_joints()
        self.create_spline_IK()
        self.create_ctrls()
        self.connect_slave()
        # TODO : connect attrs on the curve to master controller

    def create_base_joints(self):
        _length = 0
        for i in range(len(self.slaves)):
            m = self.matrices[i] if i != len(self.slaves) - 1 else self.slaves[-1].getMatrix(ws=1)
            _parent = None if i == 0 else self.jnt_ik[i - 1]
            _chain_index = alphabet_index(self.index)
            _joint_index = "{:0>2d}".format(i) if len(self.slaves) <= 100 else "{:0>3d}".format(i)
            _jnt_name = self.ik_base_name + _chain_index + "_" + _joint_index + "_SIK_jnt"
            # general joints creation
            jnt = addJoint(parent=_parent,
                           name=_jnt_name,
                           m=m,
                           vis=False)
            pm.makeIdentity(jnt, a=1, t=0, r=1, s=0, n=0, pn=1)
            self.jnt_ik.append(jnt)

            # create groups during the process of the first joint creation
            if i == 0:
                base_name = self.ik_base_name + \
                            alphabet_index(self.index)
                setupGrp = addNPO(jnt, rename=self.IK_chain_Grp_name + "_Setup")[0]
                self.ik_grp = addNPO(setupGrp, rename=self.IK_chain_Grp_name)[0]
                if not pm.objExists(base_name):
                    elementGrp = addNPO(self.ik_grp, rename=base_name)
                    pm.parent(elementGrp, self.parent)
                else:
                    elementGrp = pm.PyNode(base_name)
                    pm.parent(self.ik_grp, elementGrp)

            # if i != len(self.slaves) - 1:
            #     _length += (self.jnt_ik[i].getTranslation(ws=1) - self.jnt_ik[i - 1].getTranslation(ws=1)).length()

            """ backup
            # # add last joint tip
            # else:
            #     _length += (self.jnt_ik[i].getTranslation() - self.jnt_ik[i - 1].getTranslation()).length()
            #     last_joint = pm.PyNode(self.jnt_ik[-1])
            #     average_length = _length / (len(self.slaves) - 2.0)
            #     tip = pm.duplicate(last_joint, n=last_joint.name().replace(last_joint.namespace(), '') + '_TIP')[0]
            #     pm.parent(tip, last_joint)
            #     tip.setTranslation(last_joint.getTranslation(space='object') * average_length, space='object')
            #     tip.radius.set(last_joint.radius.get())
            #     self.jnt_ik.append(tip)
            """

    def create_spline_IK(self):
        start, end = self.jnt_ik[0], self.jnt_ik[-1]
        handle, effector, curve = pm.ikHandle(n=self.IK_chain_Grp_name + "_handle",
                                              sol="ikSplineSolver",
                                              sj=start, ee=end, ccv=True, scv=False)
        effector.rename(self.IK_chain_Grp_name + "_effector")
        curve.rename(self.IK_chain_Grp_name + "_curve")
        curve.v.set(0)
        handle.v.set(0)
        pm.parent(handle, curve.getParent())

        self.handle, self.effector, self.curve = handle, effector, curve

    def create_ctrls(self):
        ctl_positions = get_average_distance_on_curve(self.curve, self.ik_count)
        jnts = []
        for i in range(self.ik_count):
            # create grp for each position then controller & joints
            name = self.IK_chain_Grp_name + "_{}_".format(i)
            matrix = get_defaultMatrix(ctl_positions[i])
            grp = create_group(name=name + "CGrp", matrix=matrix, parent=self.ik_grp)
            ctl = create_ctl(parent=grp,
                             name=name + "Ctl",
                             m=matrix,
                             color=self.color,
                             icon="null",
                             w=self.ik_size
                             )
            jnt = addJoint(parent=ctl,
                           name=name + "CJnt",
                           m=matrix,
                           vis=False)
            jnts.append(jnt)
        pm.skinCluster(*jnts, self.curve, tsb=True, dr=2.0, n=self.curve.getShape().name() + "_skinCluster")

    def connect_slave(self):
        for ik, fk in zip(self.jnt_ik, self.slaves):
            # gear_matrix_cns(ik, fk)
            # connectWorldTransform(ik, fk)
            # pm.connectAttr(ik.rotate, fk.rotate)
            ik.rotate >> fk.rotate


#
class FKSetup:
    """
    Sine FK constructions for single chain
    """

    def __init__(self, slaves, matrices, config, index, parent=None):
        """
        getting the attributes from parent SineSetup for generate the Spline IK setup
        """
        # attrs
        self.name = config["name"]
        self.fk_size = config["fk_size"]
        self.color = config["color"]
        self.slaves = slaves
        self.matrices = matrices
        self.index = index
        self.parent = parent

        self.fk_grp = None
        self.ctls_grp = None
        self.jnt_offset = []
        self.jnt_fk = []
        self.ctls_fk = None

        self.fk_base_name = ELEMENT_Grp.format(_name=self.name) + "_"
        self.FK_chain_Grp_name = FK_Grp.format(_name=self.name, _chain_index=alphabet_index(self.index))

        # steps
        self.create_offset_joints()
        self.create_base_joints()
        self.create_ctrls()
        self.connect_slave()

    def create_offset_joints(self):
        elements = self.slaves
        _length = 0
        for i in range(len(elements)):
            m = self.matrices[i]
            _parent = None if i == 0 else self.jnt_offset[i - 1]
            _chain_index = alphabet_index(self.index)
            _joint_index = "{:0>2d}".format(i) if len(elements) <= 100 else "{:0>3d}".format(i)
            _jnt_name = self.fk_base_name + _chain_index + "_" + _joint_index + "_offset_jnt"
            # general joints creation
            jnt = addJoint(parent=_parent,
                           name=_jnt_name,
                           m=m,
                           vis=True)
            jnt.drawStyle.set(2)
            pm.makeIdentity(jnt, a=1, t=0, r=1, s=0, n=0, pn=1)
            self.jnt_offset.append(jnt)

            # create groups during the process of the first joint creation
            if i == 0:
                base_name = self.fk_base_name + \
                            alphabet_index(self.index)
                setupGrp = addNPO(jnt, rename=self.FK_chain_Grp_name + "_Setup")[0]
                self.fk_grp = addNPO(setupGrp, rename=self.FK_chain_Grp_name)[0]
                elementGrp = addNPO(self.fk_grp, rename=base_name)
                pm.parent(elementGrp, self.parent)

            if i != len(elements) - 1:
                _length += (self.jnt_offset[i].getTranslation(ws=1) - self.jnt_offset[i - 1].getTranslation(
                    ws=1)).length()

            # add last joint tip
            else:
                _length += (self.jnt_offset[i].getTranslation() - self.jnt_offset[i - 1].getTranslation()).length()
                last_joint = pm.PyNode(self.jnt_offset[-1])
                average_length = _length / (len(elements) - 2.0) if len(elements) >= 2 else _length
                tip = pm.duplicate(last_joint, n=last_joint.name().replace(last_joint.namespace(), '') + '_TIP')[0]
                pm.parent(tip, last_joint)
                tip.setTranslation(last_joint.getTranslation(space='object') * average_length, space='object')
                tip.radius.set(last_joint.radius.get())
                self.jnt_offset.append(tip)

    def create_base_joints(self):
        for jntOffset in self.jnt_offset:
            # general joints creation
            jnt = addParentJnt(parent=jntOffset,
                               name=jntOffset.shortName().replace("_offset_jnt", "_jnt"),
                               m=jntOffset.getMatrix(ws=1),
                               vis=True)
            # jnt.drawStyle.set(2)
            pm.makeIdentity(jnt, a=1, t=0, r=1, s=0, n=0, pn=1)
            self.jnt_fk.append(jnt)

    def create_ctrls(self):
        self.ctls_fk = []
        # check if the controller is on negate side.
        aim_V = (pm.PyNode(self.slaves[1]).getTranslation(ws=1) - pm.PyNode(self.slaves[0]).getTranslation(
            ws=1)).normal()
        x_axis = Vector(pm.PyNode(self.slaves[0]).getMatrix()[0][:-1]).normal()
        negate_check = aim_V != x_axis
        v = Vector(-1, 0, 0) if negate_check else Vector(1, 0, 0)
        for i in range(len(self.slaves)):
            # create controller
            name = self.FK_chain_Grp_name + "_{}_".format(i)
            matrix = self.matrices[i]
            pos_offset = self.jnt_fk[i + 1].getTranslation(ws=1) - self.jnt_fk[i].getTranslation(ws=1)
            length = pos_offset.length()
            ctl = create_ctl(parent=self.jnt_fk[i].getParent(),
                             name=name + "Ctl",
                             m=matrix,
                             color=self.color,
                             icon="cube",
                             w=length,
                             h=self.fk_size,
                             d=self.fk_size,
                             po=v * length / 2.0,
                             )
            pm.parent(self.jnt_fk[i], ctl)
            parent_tag = getWalkTag(pm.PyNode("Sine_{}_MCtl".format(self.name))) if i == 0 else getWalkTag(
                self.ctls_fk[i - 1])
            add_controller_tag(ctl, parent_tag)

            self.ctls_fk.append(ctl)

    def connect_slave(self):
        for fk, slave in zip(self.jnt_fk, self.slaves):
            fk.scale >> pm.PyNode(slave).scale
            pm.parentConstraint(fk, slave, mo=0, n=pm.PyNode(slave).name() + "_tempCns")


class SineSetup:
    def __init__(self, slaves, matrices, config):
        """
        init with the data passed in
        :param config->dict: {
            name->string,
            fk_size->float,
            ik_size->float,
            ik_count->int,
            use_index->bool|int,
            color:rgb 0~1 -> (float,float,float)}
        """
        # attrs
        self.fk_setups = []
        self.ik_setups = []
        self.element_grp = None
        self.master_grp = None
        self.master_ctl = None

        self.slaves = slaves
        self.matrices = matrices
        self.config = config

        # steps
        self.create_master()
        self.create_content()
        self.set_exp()

    def create_content(self):
        # # FK setup
        for index in self.slaves:
            fk_setup = FKSetup(slaves=self.slaves[index],
                               matrices=self.matrices[index],
                               config=self.config,
                               index=index,
                               parent=self.element_grp)
            self.fk_setups.append(fk_setup)
            # spline IK setup
            # for index in self.slaves:
            ik_setup = SplineIKSetup(slaves=fk_setup.jnt_offset,
                                     matrices=self.matrices[index],
                                     config=self.config,
                                     index=index,
                                     parent=self.element_grp)
            self.ik_setups.append(ik_setup)

    def create_master(self):
        size = 0.5 * self.config["ik_size"]
        element_grp_name = ELEMENT_Grp.format(_name=self.config["name"])

        # CREATE THE GLOBAL CONTROLLER---
        root_matrix = pm.PyNode(self.slaves[0][0]).getMatrix(ws=1)  # TODO : change this to average value
        masterCC = create_ctl(parent=None,
                              name=element_grp_name + "_MCtl",
                              m=root_matrix,
                              color=self.config["color"],
                              icon="sphere",
                              w=size
                              # **kwargs
                              )
        pm.controller(masterCC)
        element_grp = addNPO(masterCC, rename=element_grp_name)[0]
        self.element_grp = element_grp
        if pm.objExists(MASTER_GRP_NAME):
            self.master_grp = pm.PyNode(MASTER_GRP_NAME)
            pm.parent(self.element_grp, self.master_grp)
        else:
            self.master_grp = addNPO(self.element_grp, rename=MASTER_GRP_NAME)[0]

        # add attrs
        for attr in ["strength", "xVal", "yVal", "zVal", "falloff", "speed", "offset", "delay"
                     # "parameter_X", "offsetX", "ampX", "delayX", "rdmX", "falloffX",
                     # "parameter_Y", "offsetY", "ampY", "delayY", "rdmY", "falloffY",
                     # "parameter_Z", "offsetZ", "ampZ", "delayZ", "rdmZ", "falloffZ"
                     ]:
            if attr in ["strength", "speed", "falloff"]:
                pm.addAttr(masterCC, ln=attr, at='double', smn=0, smx=10, keyable=True)
            else:
                pm.addAttr(masterCC, ln=attr, at='double', smn=-10, smx=10, keyable=True)

        # if attr.startswith("par"):
        #     pm.addAttr(masterCC, ln=attr, at='enum', en="----------:", keyable=True)
        # elif attr.startswith("del"):
        #     pm.addAttr(masterCC, ln=attr, at='double', dv=1, keyable=True)
        # elif attr.startswith("rdm"):
        #     pm.addAttr(masterCC, ln=attr, at='double', dv=100, keyable=True)
        # else:
        #     pm.addAttr(masterCC, ln=attr, at='double', keyable=True)

        # lock attrs
        lock_attrs(self.element_grp)
        lock_attrs(self.master_grp)
        self.master_ctl = masterCC

    def set_exp(self):
        for fk_setup in self.fk_setups:
            elements = fk_setup.ctls_fk
            self._set_exp(self.master_ctl, elements)

    @staticmethod
    def _set_exp(masterCtl, elements):
        joint_count = len(elements)

        EXP = """
        float $xVal = {_masterName}.xVal * 0.1;
        float $yVal = {_masterName}.yVal * 0.1;
        float $zVal = {_masterName}.zVal * 0.1;
        float $falloff = {_masterName}.falloff * ({_joint_count}-1) * 0.1;  
        float $totalAmp = (({_masterName}.strength * 1.1) * ({_masterName}.strength * 1.1)) * (($falloff / 5) + 1);
        float $freq = {_masterName}.speed * 0.1 ;
        float $delay = {_masterName}.delay * -5;
        float $off = {_masterName}.offset; \n
        """.format(_masterName=masterCtl.name(), _joint_count=joint_count)

        elements.reverse()
        for index, item in enumerate(elements):
            if isinstance(item, str):
                try:
                    pm.PyNode(item)
                except:
                    return pm.warning(item, " is not valid")

            EXP += """
            {_item}.rotateZ = 
            sin( time * $freq * 3.141592653589793 * 2 
            + $off 
            + $delay 
            * ({_index} + 1 - clamp(0,{_index},$falloff)) / ({_joint_count} * 2))      
            // * $totalAmp 
            * 10
            * ({_index} + 1 - clamp(0,{_index},$falloff)) / ({_joint_count} * 2)      
            * (1.0 - ({_index} + 1) / ({_joint_count} * 2))                               
            * $zVal; \n
            """.format(_item=item,
                       _index=index,
                       # _joint_count=float(joint_count * 2),
                       _joint_count=float(joint_count),
                       )
            pm.delete(item, expressions=1)
        pm.expression(s=EXP,
                      ae=1, uc='all',
                      o="",
                      n=(elements[0] + "_exp"))
        pm.setAttr(masterCtl.speed, 10)
        pm.setAttr(masterCtl.zVal, 5)
# （（sin(time *$freq + $off + $delay * ((jointAdj - clamp(0, jointNo,$falloff)) - 1) / (jointTotal - 1)) * $totalAmp * (
# (jointAdj - clamp(0, jointNo, $falloff)) - 1) / (jointTotal - 1) * (1.0 - (2 / jointTotal))) * $xVal);
#
# （（sin(time *$freq + $off + $delay * ((2 - clamp(0, 1,$falloff)) - 1) / (34 - 1)) * $totalAmp * (
# (jointAdj - clamp(0, jointNo, $falloff)) - 1) / (34 - 1) * (1.0 - (2 / 34))) * $xVal);
