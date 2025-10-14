import unittest

from pylabrobot.resources.tube import Tube
from pylabrobot.resources.trough import Trough
from pylabrobot.resources.well_container import WellContainer


class TestWellContainer(unittest.TestCase):
  """ Tests for the WellContainer wrapper. """

  def test_tube_getitem(self):
    tube = Tube("tube", size_x=10, size_y=10, size_z=10, max_volume=100)
    container = WellContainer(tube)
    self.assertEqual(container["A1"], [tube])
    self.assertEqual(container[0], [tube])
    with self.assertRaises(IndexError):
      _ = container["A2"]
    with self.assertRaises(IndexError):
      _ = container[1]

  def test_trough_getitem(self):
    trough = Trough("trough", size_x=10, size_y=10, size_z=10, max_volume=100)
    container = WellContainer(trough)
    self.assertEqual(container["A1"], [trough])
    self.assertEqual(container[0], [trough])
    with self.assertRaises(IndexError):
      _ = container["A2"]
    with self.assertRaises(IndexError):
      _ = container[1]

  def test_getattr(self):
    tube = Tube("tube", size_x=10, size_y=10, size_z=10, max_volume=100)
    container = WellContainer(tube)
    self.assertEqual(container.name, "tube")
    self.assertEqual(container.max_volume, 100)


if __name__ == "__main__":
  unittest.main()
