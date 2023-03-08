from math import pi

import pymel.core as pm
from pymel.core.datatypes import Vector, Matrix

from .utils.helper import addNPO, addJoint, create_ctl, lock_attrs, create_group, \
    get_average_distance_on_curve, \
    get_defaultMatrix, addParentJnt, getWalkTag, getFrameRate, alphabet_index, add_controller_tag, getTransformFromPos

tau = pi * 2

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
        self.ctls_ik = []

        self.ik_base_name = ELEMENT_Grp.format(_name=self.name) + "_"
        self.IK_chain_Grp_name = SIK_Grp.format(_name=self.name, _chain_index=alphabet_index(self.index))

        # steps
        self.create_base_joints()
        self.create_spline_IK()
        self.create_ctrls()
        self.connect_slave()
        pm.addAttr(self.ctls_ik[0], ln="sine_multiplier_All", at='double', dv=1, min=0, max=1, keyable=True)
        for i in range(len(self.slaves)):
            pm.addAttr(self.ctls_ik[0], ln="FK_multiplier_{}".format(i), at='double', dv=1, keyable=True)

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
                           m=Matrix(m).homogenize(),
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
            size = self.ik_size
            if i == 0:
                size *= 1.5
            name = self.IK_chain_Grp_name + "_{}_".format(i)
            matrix = get_defaultMatrix(ctl_positions[i])
            grp = create_group(name=name + "CGrp", matrix=matrix, parent=self.ik_grp)
            ctl = create_ctl(parent=grp,
                             name=name + "Ctl",
                             m=Matrix(matrix).homogenize(),
                             color=self.color,
                             icon="null",
                             w=size
                             )
            self.ctls_ik.append(ctl)
            jnt = addJoint(parent=ctl,
                           name=name + "CJnt",
                           m=Matrix(matrix).homogenize(),
                           vis=False)
            jnts.append(jnt)
        # pm.skinCluster(*jnts, self.curve, tsb=True, dr=2.0, n=self.curve.getShape().name() + "_skinCluster")
        pm.skinCluster(jnts, self.curve, tsb=True, dr=2.0, n=self.curve.getShape().name() + "_skinCluster")

    def connect_slave(self):
        for ik, fk in zip(self.jnt_ik, self.slaves):
            ik.rotateX >> fk.rotateX
            ik.rotateY >> fk.rotateY
            ik.rotateZ >> fk.rotateZ
            ik.translateX >> fk.translateX
            ik.translateY >> fk.translateY
            ik.translateZ >> fk.translateZ


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
        self.jnt_offset = []
        self.jnt_exp = []
        self.jnt_fk = []
        self.ctls_fk = None

        self.fk_base_name = ELEMENT_Grp.format(_name=self.name) + "_"
        self.FK_chain_Grp_name = FK_Grp.format(_name=self.name, _chain_index=alphabet_index(self.index))

        # steps
        self.create_offset_joints()
        self.create_expression_joints()
        self.create_base_joints()
        self.create_ctrls()
        self.connect_slave()

    def create_offset_joints(self):
        elements = self.slaves
        _length = 0
        _localXsum = 0
        for i in range(len(elements)):
            m = self.matrices[i]
            _parent = None if i == 0 else self.jnt_offset[i - 1]
            _chain_index = alphabet_index(self.index)
            _joint_index = "{:0>2d}".format(i) if len(elements) <= 100 else "{:0>3d}".format(i)
            _jnt_name = self.fk_base_name + _chain_index + "_" + _joint_index + "_offset_jnt"
            # general joints creation
            jnt = addJoint(parent=_parent,
                           name=_jnt_name,
                           m=Matrix(m).homogenize(),
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

            elif i != 0 and i != len(elements) - 1:
                _length += (self.jnt_offset[i].getTranslation(ws=1) - self.jnt_offset[i - 1].getTranslation(
                    ws=1)).length()
                _localXsum += self.jnt_offset[i].getTranslation(ob=1)[0]

            # add last joint tip
            else:
                _length += (self.jnt_offset[i].getTranslation() - self.jnt_offset[i - 1].getTranslation()).length()
                _localXsum += self.jnt_offset[i].getTranslation(ob=1)[0]
                last_joint = pm.PyNode(self.jnt_offset[-1])
                average_length = _length / (len(elements) - 1.0) if len(elements) > 2 else _length
                scale = _localXsum / _length
                tip = pm.duplicate(last_joint, n=last_joint.name().replace(last_joint.namespace(), '') + '_TIP')[0]
                pm.parent(tip, last_joint)
                tip.setTranslation(Vector(average_length * scale, 0, 0), space='object')
                tip.radius.set(last_joint.radius.get())
                self.jnt_offset.append(tip)

    def create_expression_joints(self):
        for jnt_o in self.jnt_offset:
            # general joints creation
            jnt = addParentJnt(parent=jnt_o,
                               name=jnt_o.shortName().replace("_offset_jnt", "_exp_jnt"),
                               m=Matrix(jnt_o.getMatrix(ws=1)).homogenize(),
                               vis=True)
            # jnt.drawStyle.set(2)
            pm.makeIdentity(jnt, a=1, t=0, r=1, s=0, n=0, pn=1)
            self.jnt_exp.append(jnt)

    def create_base_joints(self):
        for jnt_e in self.jnt_exp:
            # general joints creation
            jnt = addParentJnt(parent=jnt_e,
                               name=jnt_e.shortName().replace("_exp_jnt", "_jnt"),
                               m=Matrix(jnt_e.getMatrix(ws=1)).homogenize(),
                               vis=True)
            # jnt.drawStyle.set(2)
            pm.makeIdentity(jnt, a=1, t=0, r=1, s=0, n=0, pn=1)
            self.jnt_fk.append(jnt)

    def create_ctrls(self):
        self.ctls_fk = []
        # check if the controller is on negate side.
        aim_V = (pm.PyNode(self.slaves[1]).getTranslation(ws=1) - pm.PyNode(self.slaves[0]).getTranslation(
            ws=1)).normal()
        x_axis = Vector(pm.PyNode(self.slaves[0]).getMatrix(ws=1)[0][:-1]).normal()
        negate_check = not (0.99 <= aim_V.dot(x_axis) <= 1.01)
        # print(x_axis)
        # print(aim_V.dot(x_axis))
        # print(negate_check)
        v = Vector(-1, 0, 0) if negate_check else Vector(1, 0, 0)
        for i in range(len(self.slaves)):
            # create controller
            name = self.FK_chain_Grp_name + "_{}_".format(i)
            matrix = self.matrices[i]
            pos_offset = self.jnt_fk[i + 1].getTranslation(ws=1) - self.jnt_fk[i].getTranslation(ws=1)
            length = pos_offset.length()
            ctl = create_ctl(parent=self.jnt_fk[i].getParent(),
                             name=name + "Ctl",
                             m=Matrix(matrix).homogenize(),
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
            if not pm.getAttr(slave + '.scaleX', lock=True):
                fk.scaleX >> pm.PyNode(slave).scaleX

            if not pm.getAttr(slave + '.scaleY', lock=True):
                fk.scaleY >> pm.PyNode(slave).scaleY

            if not pm.getAttr(slave + '.scaleZ', lock=True):
                fk.scaleZ >> pm.PyNode(slave).scaleZ
            pm.parentConstraint(fk, slave, mo=0, n=pm.PyNode(slave).name() + "_tempCns")


class SineSetupMain:
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
        self.ribbon_setups = []
        self.fk_setups = []
        self.ik_setups = []
        self.element_grp = None
        self.master_grp = None
        self.master_ctl = None

        self.slaves = slaves
        self.matrices = matrices
        self.config = config

        # steps
        USE_RIBBON = False  # USE_RIBBON method is temporarily discarded
        self.create_master()
        self.create_content(USE_RIBBON)
        self.set_exp(USE_RIBBON)
        self.create_sets()

    def create_master(self):
        size = 1.5 * self.config["ik_size"]
        element_grp_name = ELEMENT_Grp.format(_name=self.config["name"])

        # CREATE THE GLOBAL CONTROLLER---
        # # get the average position of root ctrls
        root_position = Vector(0, 0, 0)
        for i in range(len(self.slaves)):
            chain_root = pm.PyNode(self.slaves[i][0])
            root_position += chain_root.getTranslation(ws=1)
        root_position /= len(self.slaves)
        root_matrix = getTransformFromPos(root_position)

        masterCC = create_ctl(parent=None,
                              name=element_grp_name + "_MCtl",
                              m=Matrix(root_matrix).homogenize(),
                              color=self.config["color"],
                              icon="sphere",
                              w=size
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
        for attr in ["Sine_All",
                     "fk_vis", "ik_vis", "annotation_vis", "roll", "twist",
                     "strength",

                     "parameter_X", "loop_per_second_X",
                     "ampX", "amp_bias_rangeX", "amp_bias_LPS_multX", "amp_bias_noiseX",
                     "offset_frameX", "offset_noiseX", "offset_rdmX",
                     "delayX", "falloffX",
                     "amp_offsetX", "amp_positive_multX", "amp_negative_multX",

                     "parameter_Y", "loop_per_second_Y",
                     "ampY", "amp_bias_rangeY", "amp_bias_LPS_multY", "amp_bias_noiseY",
                     "offset_frameY", "offset_noiseY", "offset_rdmY",
                     "delayY", "falloffY",
                     "amp_offsetY", "amp_positive_multY", "amp_negative_multY",

                     "parameter_Z", "loop_per_second_Z",
                     "ampZ", "amp_bias_rangeZ", "amp_bias_LPS_multZ", "amp_bias_noiseZ",
                     "offset_frameZ", "offset_noiseZ", "offset_rdmZ",
                     "delayZ", "falloffZ",
                     "amp_offsetZ", "amp_positive_multZ", "amp_negative_multZ"
                     ]:
            if attr == "strength":
                pm.addAttr(masterCC, ln=attr, at='double', dv=1, keyable=True)
            elif "_vis" in attr:
                pm.addAttr(masterCC, ln=attr, at='bool', dv=1, min=0, max=1, keyable=True)
            elif "_mult" in attr and "_LPS" not in attr:
                pm.addAttr(masterCC, ln=attr, at='double', dv=1, keyable=True)
            elif attr.startswith("par") or attr == "Sine_All":
                pm.addAttr(masterCC, ln=attr, at='enum', en="----------:", keyable=True)
            elif "_range" in attr:
                pm.addAttr(masterCC, ln=attr, at='double', dv=0, smn=0, smx=1, keyable=True)
            elif attr.startswith("fall"):
                pm.addAttr(masterCC, ln=attr, at='double', dv=0, smn=0, smx=10, keyable=True)
            else:
                pm.addAttr(masterCC, ln=attr, at='double', dv=0, keyable=True)

        # add annotation node on master ctl
        x, y, z = root_position
        annotation = pm.annotate(masterCC, tx=element_grp_name, p=(x, y + size * 0.75, z)).getParent()
        annotation.rename(element_grp_name + "_annotation")
        annotation.getShape().displayArrow.set(0)
        annotation.overrideEnabled.set(1)
        annotation.overrideDisplayType.set(1)
        pm.parent(annotation, masterCC)
        masterCC.attr("annotation_vis") >> annotation.v

        # lock attrs
        lock_attrs(self.element_grp)
        lock_attrs(self.master_grp)
        self.master_ctl = masterCC

    def create_content(self, use_ribbon=False):
        # # FK setup
        for index in self.slaves:
            fk_setup = FKSetup(slaves=self.slaves[index],
                               matrices=self.matrices[index],
                               config=self.config,
                               index=index,
                               parent=self.element_grp)
            self.fk_setups.append(fk_setup)
            self.master_ctl.attr("fk_vis") >> fk_setup.fk_grp.v
            fk_setup.fk_grp.v.set(keyable=False, lock=True)
            # spline IK setup
            # for index in self.slaves:
            ik_setup = SplineIKSetup(slaves=fk_setup.jnt_offset,
                                     matrices=self.matrices[index],
                                     config=self.config,
                                     index=index,
                                     parent=self.element_grp)

            # ----------------------------------------------------------------------------
            # temporarily add constraint outside ik_setup class cuz this one not related to it's slave
            pm.parentConstraint(pm.PyNode(fk_setup.slaves[0]).getParent(), ik_setup.ik_grp,
                                n=ik_setup.ik_grp.name() + "_tempCns")
            # ---------------------------------------------------------------------------

            self.ik_setups.append(ik_setup)
            self.master_ctl.attr("ik_vis") >> ik_setup.ik_grp.v
            self.master_ctl.attr("roll") >> ik_setup.handle.roll
            self.master_ctl.attr("twist") >> ik_setup.handle.twist
            ik_setup.ik_grp.v.set(keyable=False, lock=True)
            """
            if use_ribbon:
                ribbon_setup = RibbonSetup(slaves_count=len(fk_setup.jnt_exp),
                                           config=self.config,
                                           index=index,
                                           fk_setup=fk_setup
                                           )
                self.ribbon_setups.append(ribbon_setup)
            """

    @staticmethod
    def _ensure_sets(name, allow_existing=True):
        if pm.objExists(name) and allow_existing:
            sets = pm.PyNode(name)
        elif pm.objExists(name) and not allow_existing:
            pm.delete(name)
            sets = pm.sets(em=1, n=name)
        else:
            sets = pm.sets(em=1, n=name)
        return sets

    def create_sets(self):
        # flags = ["se", "si", "sr", "sw", "ssw"]
        # state = {}
        # for x in flags:
        #     kwargs = {"q": True, x: True}
        #     val = pm.scriptEditorInfo(**kwargs)
        #     state[x] = val
        # # print(state)
        # pm.scriptEditorInfo(e=1, se=1, si=1, sr=1, sw=1, ssw=1)
        # # ---------------------------------------------------------

        sine_main_sets_name = "Sine_Main_Sets"
        base_name = self.fk_setups[0].fk_base_name

        sine_main_sets = self._ensure_sets(sine_main_sets_name)
        element_sets = self._ensure_sets(base_name + "Sets", allow_existing=False)

        sine_main_fk_sets = self._ensure_sets(base_name + "FK_Sets", allow_existing=False)
        sine_main_exp_sets = self._ensure_sets(base_name + "EXP_Sets", allow_existing=False)
        sine_main_ik_sets = self._ensure_sets(base_name + "IK_Sets", allow_existing=False)

        fk_sub_sets = []
        for fk_setup in self.fk_setups:
            ctrls = fk_setup.ctls_fk
            fk_sub_set = pm.sets(ctrls, n=fk_setup.FK_chain_Grp_name + "_Sets")
            sine_main_fk_sets.add(fk_sub_set)
            fk_sub_sets.append(fk_sub_set)

        exp_sub_jnt_sets = []
        for fk_setup in self.fk_setups:
            jnts = fk_setup.jnt_exp
            exp_sub_set = pm.sets(jnts, n=fk_setup.FK_chain_Grp_name + "_Exp_Sets")
            sine_main_exp_sets.add(exp_sub_set)
            exp_sub_jnt_sets.append(exp_sub_set)

        ik_sub_sets = []
        for ik_setup in self.ik_setups:
            ctrls = ik_setup.ctls_ik
            ik_sub_set = pm.sets(ctrls, n=ik_setup.IK_chain_Grp_name + "_Sets")
            sine_main_ik_sets.add(ik_sub_set)
            ik_sub_sets.append(ik_sub_set)

        element_sets.union([self.master_ctl, sine_main_fk_sets, sine_main_ik_sets, sine_main_exp_sets])
        sine_main_sets.add(element_sets)

        sine_main_bake_sets = self._ensure_sets(sine_main_sets_name.replace("_Sets", "_Bake_Sets"), allow_existing=True)
        sine_sub_bake_sets = self._ensure_sets(base_name + "Bake_Sets", allow_existing=False)
        slave_nodes = [ctrl for chain in self.slaves.values() for ctrl in chain]
        sine_sub_bake_sets.union(slave_nodes)
        sine_main_bake_sets.add(sine_sub_bake_sets)

        # # ---------------------------------------------------------
        # if PY2:
        #     for x, val in state.iteritems():  # noqa
        #         kwargs = {"e": True, x: val}
        #         pm.scriptEditorInfo(**kwargs)
        # else:
        #     for x, val in state.items():
        #         kwargs = {"e": True, x: val}
        #         pm.scriptEditorInfo(**kwargs)

    def set_exp(self, use_ribbon):
        if not use_ribbon:
            for index, fk_setup in enumerate(self.fk_setups):
                elements = fk_setup.jnt_exp
                self._set_exp(self.master_ctl, elements, index, len(self.fk_setups), self.ik_setups[index])

    @staticmethod
    def _set_exp(masterCtl, elements, chain_index, chain_count, ik_setup):
        jnt_count = len(elements)

        EXP = """
            float $sine_mult = {_ik_ctl}.sine_multiplier_All;
            float $strength = {_masterName}.strength;

            \n
            float $freqX = {_masterName}.loop_per_second_X * {_tau} * time ;
            float $falloffX = {_masterName}.falloffX * ({_joint_count}) * 0.1;  
            float $xVal = {_masterName}.ampX * 0.1 * (($falloffX / 5) + 1);
            float $xBias = {_masterName}.amp_bias_rangeX * noise({_masterName}.amp_bias_LPS_multX * $freqX 
                                                                + ({_chain_index}+1)*{_masterName}.amp_bias_noiseX); 
            float $delayX = {_masterName}.delayX * -7;
            float $offX = {_masterName}.offset_frameX / {_frame_rate} * $freqX / time;
            float $noiseX = {_masterName}.offset_noiseX * ({_chain_index}+1)/({_chain_count});
            float $rdmX = {_masterName}.offset_rdmX * noise({_masterName}.offset_rdmX + {_chain_index});
            float $ampOffX = {_masterName}.amp_offsetX;
            float $plusMultX = {_masterName}.amp_positive_multX;
            float $minusMultX = {_masterName}.amp_negative_multX;
            \n
            float $freqY = {_masterName}.loop_per_second_Y * {_tau} * time;
            float $falloffY = {_masterName}.falloffY * ({_joint_count}) * 0.1;  
            float $yVal = {_masterName}.ampY * 0.1* (($falloffY / 5) + 1);
            float $yBias = {_masterName}.amp_bias_rangeY * noise({_masterName}.amp_bias_LPS_multY * $freqY 
                                                                 + ({_chain_index}+1)*{_masterName}.amp_bias_noiseY); 
            float $delayY = {_masterName}.delayY * -7;
            float $offY = {_masterName}.offset_frameY / {_frame_rate} * $freqY / time;
            float $noiseY = {_masterName}.offset_noiseY * ({_chain_index}+1)/({_chain_count});
            float $rdmY = {_masterName}.offset_rdmY * noise({_masterName}.offset_rdmY + {_chain_index});
            float $ampOffY = {_masterName}.amp_offsetY;
            float $plusMultY = {_masterName}.amp_positive_multY;
            float $minusMultY = {_masterName}.amp_negative_multY;
            \n
            float $freqZ = {_masterName}.loop_per_second_Z * {_tau} * time;
            float $falloffZ = {_masterName}.falloffZ * ({_joint_count}) * 0.1;  
            float $zVal = {_masterName}.ampZ * 0.1* (($falloffZ / 5) + 1);
            float $zBias = {_masterName}.amp_bias_rangeZ * noise(({_masterName}.amp_bias_LPS_multZ * $freqZ / 100) 
                                                                 + (({_chain_index}+1)*{_masterName}.amp_bias_noiseZ));
            float $delayZ = {_masterName}.delayZ * -7;
            float $offZ = {_masterName}.offset_frameZ / {_frame_rate} * $freqZ / time;
            float $noiseZ = {_masterName}.offset_noiseZ * ({_chain_index}+1)/({_chain_count});
            float $rdmZ= {_masterName}.offset_rdmZ * noise({_masterName}.offset_rdmZ + {_chain_index});
            float $ampOffZ = {_masterName}.amp_offsetZ;
            float $plusMultZ = {_masterName}.amp_positive_multZ;
            float $minusMultZ = {_masterName}.amp_negative_multZ;
            """.format(_masterName=masterCtl.name(),
                       _joint_count=jnt_count,
                       _tau=tau,
                       _frame_rate=getFrameRate(),
                       _chain_index=chain_index,
                       _chain_count=chain_count,
                       _ik_ctl=ik_setup.ctls_ik[0].name()
                       )

        for jnt_index, item in enumerate(elements):
            if isinstance(item, str):
                try:
                    pm.PyNode(item)
                except:
                    return pm.warning(item, " is not valid")

            EXP += """
             // -----------------------------------------------------------------------\n    
            float $fk_mult_{_jnt_id} = {_ik_ctl}.FK_multiplier_{_jnt_id};       
            float $sinX_{_index} = sin ( 
                $freqX 
                + $rdmX 
                + $noiseX
                + $offX
                + $delayX
                * ({_index} - clamp(0,{_index},$falloffX)) / ({_joint_count} * 2.0) 
                )
                * 100 * (1 + $xBias)
                * ({_index} - clamp(0,{_index},$falloffX)) / ({_joint_count} * 2.0)      
                * (1.0 - ({_index}+1)/ ({_joint_count} * 2.0))                       
                * $xVal
                * $strength;
            if($sinX_{_index}>=0)
                {_item}.rotateX = $sinX_{_index} * $plusMultX;
            if($sinX_{_index}<0)
                {_item}.rotateX = $sinX_{_index} * $minusMultX;
            if ({_index} == 1)
                {_item}.rotateX += $ampOffX; 
            {_item}.rotateX *= $sine_mult*$fk_mult_{_jnt_id};\n

            float $sinY_{_index} = sin ( 
                    $freqY
                    + $rdmY
                    + $noiseY
                    + $offY
                    + $delayY
                    * ({_index} - clamp(0,{_index},$falloffY)) / ({_joint_count} * 2.0) 
                    )
                    * 100 * (1 + $yBias)
                    * ({_index} - clamp(0,{_index},$falloffY)) / ({_joint_count} * 2.0)      
                    * (1.0 - ({_index}+1)/ ({_joint_count} * 2.0))                         
                    * $yVal
                    * $strength;     
            if($sinY_{_index}>=0)
                {_item}.rotateY = $sinY_{_index} * $plusMultY;
            if($sinY_{_index}<0)
                {_item}.rotateY = $sinY_{_index} * $minusMultY;
            if ({_index} == 1)
                {_item}.rotateY += $ampOffY;
            {_item}.rotateY *= $sine_mult*$fk_mult_{_jnt_id}; \n

            float $sinZ_{_index} = sin ( 
                    $freqZ 
                    + $rdmZ
                    + $noiseZ
                    + $offZ 
                    + $delayZ
                    * ({_index} - clamp(0,{_index},$falloffZ)) / ({_joint_count} * 2.0) 
                    )
                     * 100 * (1 + $zBias)
                    * ({_index} - clamp(0,{_index},$falloffZ)) / ({_joint_count} * 2.0)      
                    * (1.0 - ({_index}+1)/ ({_joint_count} * 2.0))                         
                    * $zVal
                    * $strength;  
            if ({_index} == 1)
                $sinZ_{_index} += $ampOffZ;
            if($sinZ_{_index}>=0)
                {_item}.rotateZ = $sinZ_{_index} * $plusMultZ;
            if($sinZ_{_index}<0)
                {_item}.rotateZ = $sinZ_{_index} * $minusMultZ;
            {_item}.rotateZ *= $sine_mult*$fk_mult_{_jnt_id};
            \n
             // -----------------------------------------------------------------------\n
                """.format(_item=item,
                           _index=int(jnt_index + 1),
                           _jnt_id=int(jnt_index),
                           _joint_count=float(jnt_count),
                           _ik_ctl=ik_setup.ctls_ik[0].name()
                           )
            pm.delete(item, expressions=1)
        pm.expression(s=EXP,
                      ae=1, uc='all',
                      o="",
                      n=(elements[0] + "_exp"))


"""
Temporarily Discarded Methods
(Just in case we need to add it back if we need other animation methods, such as noise or other deformer-driven things)
-------------------------------------

-------------------------------------
class to build a ribbon for applying deformers
-------------------------------------
class RibbonSetup:
    " " "
        Sine Ribbon constructions for single chain
    " " "

    def __init__(self, slaves_count, config, index, fk_setup=None):
        " " "
        getting the attributes from parent SineSetup for generate the Spline IK setup
        " " "
        # attrs
        self.name = config["name"]
        self.slaves_count = slaves_count
        self.index = index
        self.fk_setup = fk_setup

        self.ribbon = None
        self.ribbon_grp = None
        self.follicle_grp = None
        self.follicle_list = []
        self.sine_deformer = None

        self.base_name = ELEMENT_Grp.format(_name=self.name) + "_"
        self.FK_chain_Grp_name = FK_Grp.format(_name=self.name, _chain_index=alphabet_index(self.index))

        # steps
        self.create_nurbsPlane()
        self.create_follicle()
        self.create_deformer()

    def create_nurbsPlane(self):
        nurbsPlane = pm.nurbsPlane(p=(0, 0, 0), ax=(0, 1, 0), lr=0.1, d=3, ch=3,
                                   w=self.slaves_count,
                                   u=self.slaves_count * 10,
                                   n="ribbon_test")[0]
        pm.delete(nurbsPlane, constructionHistory=True)
        ribbon_grp = addNPO(nurbsPlane)

        self.ribbon = nurbsPlane
        self.ribbon_grp = ribbon_grp

    def create_follicle(self):
        shape = self.ribbon.getShapes()
        follicle_grp = pm.createNode("transform", n="f_grp")
        follicle_grp.setParent(self.ribbon_grp)
        for i in range(self.slaves_count + 1):
            follicle, follicleShape = self._create_follicle(shape, name="blah", uVal=i / self.slaves_count)
            pm.parent(follicle, follicle_grp)
            # addJnt(follicle)
        self.follicle_grp = follicle_grp

    def create_deformer(self):
        self.sine_deformer = self._create_deformer(defType='sine', lowBound=0, highBound=1, rotate=(0, 0, 90),
                                                   objects=[self.ribbon],
                                                   name=self.ribbon.name(),
                                                   translate=(self.slaves_count / 2.0, 0, 0),
                                                   scale=(self.slaves_count / 2.0,
                                                          self.slaves_count,
                                                          self.slaves_count / 2.0))

    @staticmethod
    def _create_follicle(inputSurface=[], scaleGrp='', uVal=0.5, vVal=0.5, hide=1, name='follicle'):
        # Create a follicle
        follicleShape = pm.createNode('follicle')
        # Get the transform of the follicle
        follicleTrans = pm.listRelatives(follicleShape, parent=True)[0]
        # Rename the follicle
        follicleTrans = pm.rename(follicleTrans, name)
        # follicleShape = pm.rename(cmds.listRelatives(follicleTrans, c=True)[0], (name + 'Shape'))
        follicleShape = follicleTrans.getShape()
        # If the inputSurface is of type 'nurbsSurface', connect the surface to the follicle
        if pm.objectType(inputSurface[0]) == 'nurbsSurface':
            pm.connectAttr((inputSurface[0] + '.local'), (follicleShape + '.inputSurface'))
        # If the inputSurface is of type 'mesh', connect the surface to the follicle
        if pm.objectType(inputSurface[0]) == 'mesh':
            pm.connectAttr((inputSurface[0] + '.outMesh'), (follicleShape + '.inputMesh'))
        # Connect the worldMatrix of the surface into the follicleShape
        cmds.connectAttr((inputSurface[0] + '.worldMatrix[0]'), (follicleShape + '.inputWorldMatrix'))
        # pm the follicleShape to it's transform
        pm.connectAttr((follicleShape + '.outRotate'), (follicleTrans + '.rotate'))
        pm.connectAttr((follicleShape + '.outTranslate'), (follicleTrans + '.translate'))
        # Set the uValue and vValue for the current follicle
        pm.setAttr((follicleShape + '.parameterU'), uVal)
        pm.setAttr((follicleShape + '.parameterV'), vVal)
        # Lock the translate/rotate of the follicle
        pm.setAttr((follicleTrans + '.translate'), lock=True)
        pm.setAttr((follicleTrans + '.rotate'), lock=True)
        # If it was set to be hidden, hide the follicle
        if hide:
            pm.setAttr((follicleShape + '.visibility'), 0)
        # If a scale-group was defined and exists
        if scaleGrp and pm.objExists(scaleGrp):
            # Connect the scale-group to the follicle
            pm.connectAttr((scaleGrp + '.scale'), (follicleTrans + '.scale'))
            # Lock the scale of the follicle
            pm.setAttr((follicleTrans + '.scale'), lock=True)
        # Return the follicle and it's shape
        return follicleTrans, follicleShape

    @staticmethod
    def _create_deformer(objects=[], defType=None, lowBound=-1, highBound=1, translate=None, rotate=None,
                         scale=None,
                         name='nonLinear'):
        # If something went wrong or the type is not valid, raise exception
        if not objects or defType not in ['bend', 'flare', 'sine', 'squash', 'twist', 'wave']:
            raise Exception("function: 'nonlinearDeformer' - Make sure you specified a mesh and a valid deformer")
        # Create and rename the deformer
        nonLinDef = cmds.nonLinear(objects[0].name(), type=defType, lowBound=lowBound, highBound=highBound,
                                   n=name + '_' + defType + '_def')
        # # If translate was specified, set the translate
        if translate:
            pm.setAttr((nonLinDef[1] + '.translate'), translate[0], translate[1], translate[2])
        # If rotate was specified, set the rotate
        if rotate:
            pm.setAttr((nonLinDef[1] + '.rotate'), rotate[0], rotate[1], rotate[2])
        if scale:
            pm.setAttr((nonLinDef[1] + '.scale'), scale[0], scale[1], scale[2])
        # Return the deformer
        return nonLinDef

-------------------------------------
good old expression for single chain with 1 axis
-------------------------------------
    @staticmethod
    def _set_exp(masterCtl, elements):
        joint_count = len(elements)

        EXP = " " "
            float $xVal = {_masterName}.xVal * 0.1;
            float $yVal = {_masterName}.yVal * 0.1;
            float $zVal = {_masterName}.zVal * 0.1;
            float $falloff = {_masterName}.falloff * ({_joint_count}) * 0.1;  
            float $totalAmp = (({_masterName}.strength * 1.1) * ({_masterName}.strength * 1.1)) * (($falloff / 5) + 1);
            float $freq = {_masterName}.speed * 0.1 * {_tau} ;
            float $delay = {_masterName}.delay * -5;
            float $off = {_masterName}.offset; \n
            " " ".format(_masterName=masterCtl.name(), _joint_count=joint_count, _tau=tau)

        for index, item in enumerate(elements):
            if isinstance(item, str):
                try:
                    pm.PyNode(item)
                except:
                    return pm.warning(item, " is not valid")

            EXP += " " "
                {_item}.rotateZ = 
                sin ( 
                    time * $freq
                    + $off 
                    + $delay 
                    * ({_index} - clamp(0,{_index},$falloff)) / ({_joint_count} * 2.0) 
                    )   
                * $totalAmp 
                * ({_index} - clamp(0,{_index},$falloff)) / ({_joint_count} * 2.0)      
                * (1.0 - ({_index}+1)/ ({_joint_count} * 2.0))                          
                * $zVal; \n
                " " ".format(_item=item,
                           _index=index + 1,
                           _joint_count=float(joint_count),
                           )
            pm.delete(item, expressions=1)
        pm.expression(s=EXP,
                      ae=1, uc='all',
                      o="",
                      n=(elements[0] + "_exp"))
        pm.setAttr(masterCtl.speed, 10)
        pm.setAttr(masterCtl.zVal, 5)

"""
