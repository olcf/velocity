from unittest import TestCase
from src.velocity._config import validate_and_generate_config

TEST_SCHEMA = {
    "type": dict,
    "properties": {
        "test_dict": {
            "type": dict,
            "properties": {
                "test_list": {},
                "test_str": {},
                "test_bool": {}
            }
        },
        "missing_dict": {}
    }
}


class Test(TestCase):
    """
    def test_validate_config(self):
        # misc
        self.assertFalse(validate_and_generate_config({}, {}))
        self.assertFalse(validate_and_generate_config(1, {}))

        # dict
        ts = {
            "type": dict,
            "required": True,
            "auto": False,
            "cardinality": "one",
            "properties": {}
        }
        self.assertTrue(validate_and_generate_config({}, ts))
        self.assertFalse(validate_and_generate_config(None, ts))
        self.assertFalse(validate_and_generate_config({"test": 0}, ts))

        ts = {
            "type": dict,
            "required": True,
            "auto": False,
            "cardinality": "one",
            "properties": {
                "test": {
                    "type": bool
                }
            }
        }
        self.assertFalse(validate_and_generate_config({"test": True}, ts))

        # list

        # str

        # bool

        self.fail()
        """
