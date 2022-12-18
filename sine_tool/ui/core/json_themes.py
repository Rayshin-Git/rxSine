import codecs
import json
import os
# IMPORT SETTINGS
# ///////////////////////////////////////////////////////////////
import sys

from .json_settings import Settings

PY2 = sys.version_info[0] == 2


# APP THEMES
# ///////////////////////////////////////////////////////////////
class Themes(object):
    # LOAD SETTINGS
    # ///////////////////////////////////////////////////////////////
    setup_settings = Settings()
    _settings = setup_settings.items

    # APP PATH
    # ///////////////////////////////////////////////////////////////
    json_file = "themes/{}.json".format(_settings['theme_name'])
    app_path = os.path.dirname(os.path.dirname(__file__))
    settings_path = os.path.normpath(os.path.join(app_path, json_file))
    if not os.path.isfile(settings_path):
        print("WARNING: \"themes/{}.json\" not found! check in the folder {}".format(_settings['theme_name'],
                                                                                     settings_path))

    # INIT SETTINGS
    # ///////////////////////////////////////////////////////////////
    def __init__(self):
        super(Themes, self).__init__()

        # DICTIONARY WITH SETTINGS
        self.items = {}

        # DESERIALIZE
        self.deserialize()

    # SERIALIZE JSON
    # ///////////////////////////////////////////////////////////////
    def serialize(self):
        # WRITE JSON FILE
        with codecs.open(self.settings_path, "w", 'utf-8') as write:
            json.dump(self.items, write, indent=4)
        # with open(self.settings_path, "w", encoding='utf-8') as write:
        #     json.dump(self.items, write, indent=4)

    # DESERIALIZE JSON
    # ///////////////////////////////////////////////////////////////
    def deserialize(self):
        # READ JSON FILE
        with codecs.open(self.settings_path, "r", 'utf-8') as reader:
            settings = json.loads(reader.read())
            self.items = settings
        # with open(self.settings_path, "r", encoding='utf-8') as reader:
        #     settings = json.loads(reader.read())
        #     self.items = settings
