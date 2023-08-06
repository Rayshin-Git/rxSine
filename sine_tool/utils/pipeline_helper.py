import os
import maya.OpenMaya as om

PIPLINE_AVAILABLE = False
try:
    import pipeline3.pipeline as pp
except ImportError:
    pass
else:
    PIPLINE_AVAILABLE = "pipeline3"
    om.MGlobal.displayInfo("pipeline using pipeline3")

# # print(PIPLINE_AVAILABLE)
USER_NAME = pp.get_user() if PIPLINE_AVAILABLE else ""
PROJECT_NAME = pp.get_project() if PIPLINE_AVAILABLE else ""
BASE_PATH = pp.get_base_path() if PIPLINE_AVAILABLE else ""
MGEAR_CUSTOM_PATH = os.path.join(BASE_PATH, PROJECT_NAME, "mGear", "build",
                                 "custom_steps") if PIPLINE_AVAILABLE else ""
USER_BASE_PATH = os.path.join(BASE_PATH, PROJECT_NAME, "user") if PIPLINE_AVAILABLE else ""
try:
    import PrismCore
except ImportError:
    pass
else:
    PIPLINE_AVAILABLE = "Prism"
    om.MGlobal.displayInfo("pipeline using PrismCore")

if PIPLINE_AVAILABLE and PIPLINE_AVAILABLE != "pipeline3":
    USER_PATH = os.environ['MGEAR_SHIFTER_CUSTOMSTEP_PATH']
    PROJECT_NAME = os.environ['MGEAR_SHIFTER_CUSTOMSTEP_PATH'].split("\\")[-2]
else:
    USER_PATH = os.path.join(USER_BASE_PATH, USER_NAME) if PIPLINE_AVAILABLE else ""
