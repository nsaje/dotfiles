from django import test
import ast
import os
import glob


class LocalSettingsTestCase(test.TestCase):

    def _is_valid_attribute(self, attribute_name):
        if attribute_name.startswith("_"):
            return False
        return attribute_name.upper() == attribute_name

    def _build_config_file_list(self):
        PATH = os.path.dirname(os.path.abspath(__file__))
        ls = glob.glob("{path}/localsettings.py.*".format(path=PATH))
        return ls

    def _build_key_list(self, filename):
        keys = set()
        module_code = open(filename).read()
        ast_object_tree = ast.parse(module_code)
        for ast_object in ast_object_tree.body:
            if type(ast_object) == ast.Assign:
                target = ast_object.targets[0]
                if type(target) == ast.Subscript:
                    continue
                attribute_name = target.id
                if self._is_valid_attribute(attribute_name):
                    keys.add(attribute_name)
        return keys

    def _settings_differece(self, settings1, settings2):
        missing_from_2 = settings1.difference(settings2)
        missing_from_1 = settings2.difference(settings1)
        return (not(len(missing_from_1) == 0 and len(missing_from_2) == 0),  missing_from_1, missing_from_2)

    def test_localsettings_consistency(self):
        settings_filename_list = self._build_config_file_list()
        referrence_settings_filename = settings_filename_list.pop()

        referrence_settings_keys = self._build_key_list(referrence_settings_filename)
        for curr_settings_file in settings_filename_list:
            curr_settings_keys = self._build_key_list(curr_settings_file)

            (missing_config_keys, missing_from_1, missing_from_2) = self._settings_differece(referrence_settings_keys, curr_settings_keys)
            if missing_config_keys:
                print("\n>>> Comparing {conf1} to {conf2} <<<".format(conf1=referrence_settings_filename, conf2=curr_settings_file))
                if len(missing_from_1) > 0:
                    print("{filename} is missing: {missing}".format(filename=referrence_settings_filename, missing=missing_from_1))
                if len(missing_from_2) > 0:
                    print("{filename} is missing: {missing}".format(filename=curr_settings_file, missing=missing_from_2))
            self.assertFalse(missing_config_keys)
