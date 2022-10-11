import pymel.core as pm
from pymel.core import datatypes
from pymel.core.datatypes import Point, Vector, Matrix
# from mgear.rigbits import addNPO, addJnt, createCTL

from .helper import addNPO, create


def crete_exp(masterName, elements):
    joint_count = len(elements)

    EXP = """
    float $xVal = {cc}.xVal * 0.1;
    float $yVal = {cc}.yVal * 0.1;
    float $zVal = {cc}.zVal * 0.1;
    float $falloff = {cc}.falloff * ({jointCount}-1) * 0.1;  
    float $totalAmp = (({cc}.strength * 1.1) * ({cc}.strength * 1.1)) * (($falloff/5)+1);
    float $freq = {cc}.speed * 0.1 ;
    float $delay = {cc}.delay *-5;
    float $off = {cc}.offset; \n
    """.format(cc=masterName, jointCount=joint_count)

    elements.reverse()
    for index, item in enumerate(elements):
        if isinstance(item, str):
            try:
                pm.PyNode(item)
            except:
                return pm.warning(item, " is not valid")

        EXP += """
        {itemName}.rotateZ = 
        sin( time * $freq * 3.141592653589793 * 2 
        + $off 
        + $delay 
        * ({index}+1 - clamp(0,{index},$falloff)) / ({jointTotal}*2))      
        // * $totalAmp 
        * 10
        * ({index}+1 - clamp(0,{index},$falloff)) / ({jointTotal}*2)      
        * (1.0 - ({index}+1)/({jointTotal}*2))                               
        * $zVal; \n
        """.format(itemName=item,
                   index=index,
                   # jointTotal=float(joint_count * 2),
                   jointTotal=float(joint_count),
                   )
        pm.delete(item, expressions=1)
    print(EXP)
    pm.expression(s=EXP,
                  ae=1, uc='all',
                  o="",
                  n=(elements[0] + "_exp"))
    pm.setAttr("SineSCA_MCtl.speed", 10)
    pm.setAttr("SineSCA_MCtl.zVal", 5)


class SineMaster:
    def __init__(self, element, config):
        """
        init with the data passed in
        :param config->dict: {
            ctl_name->sting,
            fk_size->float,
            ik_size->float,
            ik_count->int,
            use_index->bool|int,
            color:rgb 0~1 -> (float,float,float)}
        """
        self.element = element
        self.config = config
        self.ctrls = {}

        self.create_master_ctl()
        # self.create_contents(data, ctl_size)

    def create_contents(self, data, size, name):
        for chain in data:
            self.ctrls[chain] = []
            for i in range(len(chain) - 1):
                start_obj, end_obj = data[i], data[i + 1]
                sm = start_obj.getMatrix(ws=1)
                sp = start_obj.getTranslation(ws=1)
                ep = end_obj.getTranslation(ws=1)
                length = (ep - sp).length()
                ctl = create_chain_box(length, size)
                ctl.setMatrix(sm, ws=1)
                self.ctrls[chain].append(ctl)

    def create_master_ctl(self):
        print(self.config["name"])
        size = 0.1 * self.config["fk_size"]
        master_name = "Sine_Master_" + self.config["name"]
        # CREATE THE GLOBAL CONTROLLER---
        master_matrix = pm.PyNode(self.element[0][-1]).getMatrix(ws=1)
        masterCC = create(parent=None,
                          name=master_name,
                          m=master_matrix,
                          color=self.config["color"],
                          icon="cube",
                          # **kwargs
                          )
        self.name = masterCC.name()
        masterGrp = addNPO(masterCC, "_Grp")
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
        for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]:
            pm.setAttr(masterCC.attr(attr),
                       lock=True, channelBox=False, keyable=False)
        self.master = masterCC

# （（sin(time *$freq + $off + $delay * ((jointAdj - clamp(0, jointNo,$falloff)) - 1) / (jointTotal - 1)) * $totalAmp * (
# (jointAdj - clamp(0, jointNo, $falloff)) - 1) / (jointTotal - 1) * (1.0 - (2 / jointTotal))) * $xVal);
#
# （（sin(time *$freq + $off + $delay * ((2 - clamp(0, 1,$falloff)) - 1) / (34 - 1)) * $totalAmp * (
# (jointAdj - clamp(0, jointNo, $falloff)) - 1) / (34 - 1) * (1.0 - (2 / 34))) * $xVal);
