import unittest
from src.utils.factory import Registry

class DummyBase:
    pass

class DummyClassA(DummyBase):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

class DummyClassB(DummyBase):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = Registry[DummyBase]("dummy")

    def test_register_and_create(self):
        @self.registry.register("class_a")
        class RegisteredA(DummyClassA):
            pass

        instance = self.registry.create("class_a", foo="bar")
        self.assertIsInstance(instance, DummyClassA)
        self.assertEqual(instance.kwargs, {"foo": "bar"})

    def test_register_multiple_names(self):
        @self.registry.register("name1", "name2")
        class RegisteredB(DummyClassB):
            pass

        instance1 = self.registry.create("name1")
        instance2 = self.registry.create("name2")
        self.assertIsInstance(instance1, DummyClassB)
        self.assertIsInstance(instance2, DummyClassB)

    def test_create_unknown_provider(self):
        with self.assertRaises(ValueError) as context:
            self.registry.create("unknown")
        self.assertIn("Unsupported dummy provider: unknown", str(context.exception))

    def test_copy(self):
        self.registry.register("class_a")(DummyClassA)
        copied = self.registry.copy()
        self.assertIn("class_a", copied)
        self.assertEqual(copied["class_a"], DummyClassA)
        
        # Modify original, copy should not be affected
        self.registry.register("class_b")(DummyClassB)
        self.assertIn("class_b", self.registry)
        self.assertNotIn("class_b", copied)

    def test_clear(self):
        self.registry.register("class_a")(DummyClassA)
        self.assertIn("class_a", self.registry)
        self.registry.clear()
        self.assertNotIn("class_a", self.registry)

    def test_update(self):
        other_dict = {"class_b": DummyClassB}
        self.registry.update(other_dict)
        self.assertIn("class_b", self.registry)
        self.assertEqual(self.registry["class_b"], DummyClassB)

    def test_contains_and_getitem(self):
        self.registry.register("class_a")(DummyClassA)
        self.assertTrue("class_a" in self.registry)
        self.assertFalse("class_b" in self.registry)
        
        self.assertEqual(self.registry["class_a"], DummyClassA)
        with self.assertRaises(KeyError):
            _ = self.registry["class_b"]

if __name__ == "__main__":
    unittest.main()
