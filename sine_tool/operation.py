import pymel.core as pm
from pymel.core import datatypes
from pymel.core.datatypes import Point, Vector, Matrix
# from mgear.rigbits import addNPO, addJnt, createCTL

from .helper import addNPO, addJoint, create_ctl, addCnstJnt, lock_attrs


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


class SineSetup:
    def __init__(self, element, matrices, config):
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

        self.element = element
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
        # Sine
        # -- Sine_[element]_Grp
        #   -- Sine_Ik
        size = self.config["ik_size"]
        for index in self.element:
            chain = self.element[index]
            if len(chain) >= 1000:
                return pm.warning("chain length shouldn't over 1000")
            self.ctrls[index] = []
            # create joint chain for spline IK
            ik_base_name = ELEMENT_Grp.format(_name=self.config["name"]) + "_"
            for i in range(len(chain)):
                m = self.matrices[index][i]
                parent = None if i == 0 else self.jnt_ik[i - 1]
                _chain_index = alphabet_index(index)
                _joint_index = "{:0>2d}".format(i) if len(chain) <= 100 else "{:0>3d}".format(i)
                _jnt_name = ik_base_name + _chain_index + "_" + _joint_index + "_jnt"
                jnt = addJoint(parent=parent,
                               name=_jnt_name,
                               m=m,
                               vis=True)
                pm.makeIdentity(jnt)
                self.jnt_ik.append(jnt)
                if i == 0:
                    base_name = ik_base_name + \
                                alphabet_index(index)
                    IK_Grp_name = SIK_Grp.format(_name=self.config["name"],
                                                 _chain_index=_chain_index
                                                 )
                    setupGrp = addNPO(jnt, rename=IK_Grp_name + "_Setup")[0]
                    IKGrp = addNPO(setupGrp, rename=IK_Grp_name)[0]
                    elementGrp = addNPO(IKGrp, rename=base_name)
                    pm.parent(elementGrp, self.element_grp)
            # create ctls for spline IK
            # for i in range(len(chain) - 1):
            #     start_matrix, end_matrix = pm.xform(chain[i], q=1, m=1, ws=1), pm.xform(chain[i + 1], q=1, m=1, ws=1)
            #     length = (start_matrix - end_matrix).translate.length()
            #     parent =
            #     jnt =
            #     # ctl = create_chain_box(length, size)
            #     # ctl.setMatrix(sm, ws=1)
            #     # if i == 0 :
            #     #     self.ik_grp = addNPO(ctl, "_IKGrp")
            #     # self.ctrls[chain].append(ctl)

        # FK setup
        size = self.config["fk_size"]
        for index in self.element:
            chain = self.element[index]
            if len(chain) >= 1000:
                return pm.warning("chain length shouldn't over 1000")

    def create_master(self):
        size = 0.1 * self.config["fk_size"]
        element_grp_name = ELEMENT_Grp.format(_name=self.config["name"])

        # CREATE THE GLOBAL CONTROLLER---
        root_matrix = pm.PyNode(self.element[0][0]).getMatrix(ws=1)  # TODO : change this to average value
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
