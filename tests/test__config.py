from unittest import TestCase
from src.velocity._config import Config

c = Config()
c._config = {
    "test_one": 7,
    "test_two": False,
    "test_three": [5, "a"],
    "test_four": {
        "inner_test": "test"
    }
}

class TestConfig(TestCase):
    def test_set(self):
        c.set("test_four:inner_test", True)
        c.set("one:two:three", "test")
        c.set("again", 56)
        t = {
            "again": 56,
            "test_one": 7,
            "test_two": False,
            "test_three": [5, "a"],
            "test_four": {
                "inner_test": True
            },
            "one": {
                "two": {
                    "three": "test"
                }
            }
        }
        self.assertEqual(t, c._config)

    def test_get(self):
        self.assertEqual(7, c.get("test_one"))
        self.assertFalse(c.get("test_two"))
        self.assertEqual("a", c.get("test_three")[1])
        self.assertEqual("test", c.get("test_four:inner_test"))
