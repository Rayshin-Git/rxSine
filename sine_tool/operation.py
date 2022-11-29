import pymel.core as pm
from pymel.core import datatypes
from pymel.core.datatypes import Point, Vector, Matrix
# from mgear.rigbits import addNPO, addJnt, createCTL

from .helper import addNPO, addJoint, create_ctl, addCnstJnt, \
    lock_attrs, create_group, get_average_distance_on_curve, \
    get_defaultMatrix


def crete_exp(masterName, elements):
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
    """.format(_masterName=masterName, _joint_count=joint_count)

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
    pm.setAttr("SineSCA_MCtl.speed", 10)
    pm.setAttr("SineSCA_MCtl.zVal", 5)


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
        self.ik_color = config["color"]
        self.ik_count = config["ik_count"]
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
        # TODO : connect attrs on the curve to master controller

    def create_base_joints(self):
        elements = self.slaves[self.index]
        _length = 0
        for i in range(len(elements)):
            m = self.matrices[self.index][i]
            _parent = None if i == 0 else self.jnt_ik[i - 1]
            _chain_index = alphabet_index(self.index)
            _joint_index = "{:0>2d}".format(i) if len(elements) <= 100 else "{:0>3d}".format(i)
            _jnt_name = self.ik_base_name + _chain_index + "_" + _joint_index + "_jnt"
            print(_jnt_name, self.IK_chain_Grp_name)
            # general joints creation
            jnt = addJoint(parent=_parent,
                           name=_jnt_name,
                           m=m,
                           vis=True)
            pm.makeIdentity(jnt)
            self.jnt_ik.append(jnt)

            # create groups during the process of the first joint creation
            if i == 0:
                base_name = self.ik_base_name + \
                            alphabet_index(self.index)
                setupGrp = addNPO(jnt, rename=self.IK_chain_Grp_name + "_Setup")[0]
                self.ik_grp = addNPO(setupGrp, rename=self.IK_chain_Grp_name)[0]
                elementGrp = addNPO(self.ik_grp, rename=base_name)
                pm.parent(elementGrp, self.parent)

            if i != len(elements) - 1:
                _length += (self.jnt_ik[i].getTranslation(ws=1) - self.jnt_ik[i - 1].getTranslation(ws=1)).length()

            # add last joint tip
            else:
                _length += (self.jnt_ik[i].getTranslation() - self.jnt_ik[i - 1].getTranslation()).length()
                last_joint = pm.PyNode(self.jnt_ik[-1])
                average_length = _length / (len(elements) - 1.0)
                tip = pm.duplicate(last_joint, n=last_joint.name().replace(last_joint.namespace(), '') + '_TIP')[0]
                pm.parent(tip, last_joint)
                tip.setTranslation(last_joint.getTranslation(space='object') * average_length, space='object')
                tip.radius.set(last_joint.radius.get())
                self.jnt_ik.append(tip)

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
            # create grp for each controller
            name = self.IK_chain_Grp_name + "_{}_".format(i)
            matrix = get_defaultMatrix(ctl_positions[i])
            grp = create_group(name=name + "CGrp", matrix=matrix, parent=self.ik_grp)
            ctl = create_ctl(parent=grp,
                             name=name + "Ctl",
                             m=matrix,
                             color=self.ik_color,
                             icon="null",
                             )
            jnt = addJoint(parent=ctl,
                           name=name + "CJnt",
                           m=matrix,
                           vis=False)
            jnts.append(jnt)
        pm.skinCluster(*jnts, self.curve, tsb=True, dr=2.0, n=self.curve.getShape().name() + "_skinCluster")


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
        self.element_grp = None
        self.master_grp = None
        self.master_ctl = None

        self.slaves = slaves
        self.matrices = matrices
        self.config = config
        self.ctrls = {}
        self.jnt_ik = []

        # steps
        self.create_master()
        self.create_content()
        self.group_up()

    def create_content(self):
        # spline IK setup
        size = self.config["ik_size"]
        for index in self.slaves:
            chain = self.slaves[index]
            SplineIKSetup(
                slaves=self.slaves,
                matrices=self.matrices,
                config=self.config,
                index=index,
                parent=self.element_grp)

        # FK setup
        size = self.config["fk_size"]
        for index in self.slaves:
            chain = self.slaves[index]
            if len(chain) >= 1000:
                return pm.warning("chain length shouldn't over 1000")

    def create_master(self):
        size = 0.1 * self.config["fk_size"]
        element_grp_name = ELEMENT_Grp.format(_name=self.config["name"])

        # CREATE THE GLOBAL CONTROLLER---
        root_matrix = pm.PyNode(self.slaves[0][0]).getMatrix(ws=1)  # TODO : change this to average value
        masterCC = create_ctl(parent=None,
                              name=element_grp_name + "_MCtl",
                              m=root_matrix,
                              color=self.config["color"],
                              icon="sphere",
                              # **kwargs
                              )
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

    def group_up(self):
        pass

# （（sin(time *$freq + $off + $delay * ((jointAdj - clamp(0, jointNo,$falloff)) - 1) / (jointTotal - 1)) * $totalAmp * (
# (jointAdj - clamp(0, jointNo, $falloff)) - 1) / (jointTotal - 1) * (1.0 - (2 / jointTotal))) * $xVal);
#
# （（sin(time *$freq + $off + $delay * ((2 - clamp(0, 1,$falloff)) - 1) / (34 - 1)) * $totalAmp * (
# (jointAdj - clamp(0, jointNo, $falloff)) - 1) / (34 - 1) * (1.0 - (2 / 34))) * $xVal);
