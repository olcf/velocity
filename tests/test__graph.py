from unittest import TestCase
from re import compile
from src.velocity._graph import (
    Version,
    Image
)


class Test(TestCase):
    def test_version_regex(self):
        p = compile(r"^(?P<major>[0-9]+)(?:\.(?P<minor>[0-9]+)(:?\.(?P<patch>[0-9]+))?)?(?:-(?P<suffix>[a-zA-Z0-9]+))?$")

        # test 2.3.5-s90er
        m = p.search("2.3.5-s90er")
        self.assertEqual("2", m.group("major"))
        self.assertEqual("3", m.group("minor"))
        self.assertEqual("5", m.group("patch"))
        self.assertEqual("s90er", m.group("suffix"))

        # test 2.3.5
        m = p.search("2.3.5")
        self.assertEqual("2", m.group("major"))
        self.assertEqual("3", m.group("minor"))
        self.assertEqual("5", m.group("patch"))
        self.assertIsNone(m.group("suffix"))

        # test 2.3
        m = p.search("2.3")
        self.assertEqual("2", m.group("major"))
        self.assertEqual("3", m.group("minor"))
        self.assertIsNone(m.group("patch"))
        self.assertIsNone(m.group("suffix"))

        # test 2
        m = p.search("2")
        self.assertEqual("2", m.group("major"))
        self.assertIsNone(m.group("minor"))
        self.assertIsNone(m.group("patch"))
        self.assertIsNone(m.group("suffix"))


class TestVersion(TestCase):
    def test_init(self):
        # test 2.3.5-s90er
        v = Version("2.3.5-s90er")
        self.assertEqual(2, v.major)
        self.assertEqual(3, v.minor)
        self.assertEqual(5, v.patch)
        self.assertEqual("s90er", v.suffix)

        # test 2.3.5
        v = Version("2.3.5")
        self.assertEqual(2, v.major)
        self.assertEqual(3, v.minor)
        self.assertEqual(5, v.patch)
        self.assertIsNone(v.suffix)

        # test 2.3
        v = Version("2.3")
        self.assertEqual(2, v.major)
        self.assertEqual(3, v.minor)
        self.assertIsNone(v.patch)
        self.assertIsNone(v.suffix)

        # test 2
        v = Version("2")
        self.assertEqual(2, v.major)
        self.assertIsNone(v.minor)
        self.assertIsNone(v.patch)
        self.assertIsNone(v.suffix)

    def test_str(self):
        # test 2.3.5-s90er
        v = Version("2.3.5-s90er")
        self.assertEqual("2.3.5-s90er", v.__str__())

        # test 2.3.5
        v = Version("2.3.5")
        self.assertEqual("2.3.5", v.__str__())

        # test 2.3
        v = Version("2.3")
        self.assertEqual("2.3", v.__str__())

        # test 2
        v = Version("2")
        self.assertEqual("2", v.__str__())

    def test_comparisons(self):
        # test 2.3.4 vs 2.3.4
        one = Version("2.3.4")
        two = Version("2.3.4")
        self.assertTrue(one == two)
        self.assertFalse(one > two)
        self.assertTrue(one >= two)
        self.assertFalse(one < two)
        self.assertTrue(one <= two)

        # test 2.3.4-rc1 vs 2.3.4-rc1
        one = Version("2.3.4-rc1")
        two = Version("2.3.4-rc1")
        self.assertTrue(one == two)
        self.assertFalse(one > two)
        self.assertTrue(one >= two)
        self.assertFalse(one < two)
        self.assertTrue(one <= two)

        # test 2.3.4 vs 2.3.5
        one = Version("2.3.4")
        two = Version("2.3.5")
        self.assertFalse(one == two)
        self.assertFalse(one > two)
        self.assertFalse(one >= two)
        self.assertTrue(one < two)
        self.assertTrue(one <= two)

        # test 2.3.6 vs 2.3.4
        one = Version("2.3.6")
        two = Version("2.3.4")
        self.assertFalse(one == two)
        self.assertTrue(one > two)
        self.assertTrue(one >= two)
        self.assertFalse(one < two)
        self.assertFalse(one <= two)

        # test 2.3.4 vs 2.3.4-rc1
        one = Version("2.3.4")
        two = Version("2.3.4-rc1")
        self.assertTrue(one == two)
        self.assertFalse(one > two)
        self.assertTrue(one >= two)
        self.assertFalse(one < two)
        self.assertTrue(one <= two)

        # test 2.3.4 vs 2.3 & 2
        one = Version("2.3.4")
        two = Version("2.3")
        self.assertTrue(one == two)
        self.assertFalse(one > two)
        self.assertTrue(one >= two)
        self.assertTrue(one <= two)
        self.assertFalse(one < two)
        two = Version("2")
        self.assertTrue(one == two)
        self.assertFalse(one > two)
        self.assertTrue(one >= two)
        self.assertTrue(one <= two)
        self.assertFalse(one < two)


class TestImage(TestCase):
    def test_satisfies_spec(self):
        image = Image("gcc", "12.3.0", "frontier", "apptainer", "ubuntu", "")
        image2 = Image("test", "1", "frontier", "apptainer", "ubuntu", "")
        
        # name
        self.assertTrue(image.satisfies("gcc"))
        self.assertTrue(image2.satisfies("test"))
        self.assertFalse(image.satisfies("ubuntu"))
        
        # version
        self.assertTrue(image.satisfies("gcc@12.3.0"))
        self.assertTrue(image.satisfies("gcc@12.3"))
        self.assertTrue(image.satisfies("gcc@12"))
        self.assertTrue(image.satisfies("gcc@12.3.0:"))
        self.assertTrue(image.satisfies("gcc@:12.3.0"))
        self.assertTrue(image.satisfies("gcc@11.0.0:13.0.0"))
        self.assertTrue(image.satisfies("gcc@:12"))
        self.assertTrue(image.satisfies("gcc gcc@12.3.0"))

        self.assertFalse(image.satisfies("gcc@14.0.0"))
        self.assertFalse(image.satisfies("gcc@1"))
        self.assertFalse(image.satisfies("ubuntu@12.3.0"))
        self.assertFalse(image.satisfies("12.3.0"))
        self.assertFalse(image.satisfies("gcc@13.0.0:13.2.0"))

        # system
        self.assertTrue(image.satisfies("system=frontier"))
        self.assertFalse(image.satisfies("system=summit"))
        self.assertFalse(image.satisfies("frontier"))

        # backend
        self.assertTrue(image.satisfies("backend=apptainer"))
        self.assertFalse(image.satisfies("backend=podman"))
        self.assertFalse(image.satisfies("apptainer"))

        # distro
        self.assertTrue(image.satisfies("distro=ubuntu"))
        self.assertFalse(image.satisfies("dictro=opensuse"))
        self.assertFalse(image.satisfies("ubuntu"))

    #def test_add_spec(self):
    #    self.fail()

    #def test_hash(self):
    #    self.fail()
