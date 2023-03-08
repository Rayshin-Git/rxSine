import os
import maya.OpenMaya as om

PIPLINE_AVAILABLE = False
try:
    import pipeline3.pipeline as pp
except ImportError:
    om.MGlobal.displayWarning("couldn't import pipline3,")
else:
    PIPLINE_AVAILABLE = True
# print(PIPLINE_AVAILABLE)
USER_NAME = pp.get_user() if PIPLINE_AVAILABLE else ""
PROJECT_NAME = pp.get_project() if PIPLINE_AVAILABLE else ""
BASE_PATH = pp.get_base_path() if PIPLINE_AVAILABLE else ""
MGEAR_CUSTOM_PATH = os.path.join(BASE_PATH, PROJECT_NAME, "mGear", "build", "custom_steps") if PIPLINE_AVAILABLE else ""
USER_BASE_PATH = os.path.join(BASE_PATH, PROJECT_NAME, "user") if PIPLINE_AVAILABLE else ""
USER_PATH = os.path.join(USER_BASE_PATH, USER_NAME) if PIPLINE_AVAILABLE else ""
