import unittest
from unittest.mock import AsyncMock, MagicMock, call

from pylabrobot.liquid_handling.errors import ChannelizedError
from pylabrobot.liquid_handling.tip_manager import TipManager
from pylabrobot.liquid_handling.backends.testing import NoTipErrorBackend
from pylabrobot.resources import Deck, STF_L, TipRack, TipSpot, Tip

class TestTipManager(unittest.IsolatedAsyncioTestCase):
  """ Tests for the TipManager class. """

  def setUp(self):
    self.backend = NoTipErrorBackend()
    self.deck = Deck()
    self.tip_rack1 = TipRack("tip_rack1", "A1", "B1", num_items=8)
    self.tip_rack2 = TipRack("tip_rack2", "A1", "B1", num_items=8)
    self.deck.assign_child_resource(self.tip_rack1, location=(0, 0, 0))
    self.deck.assign_child_resource(self.tip_rack2, location=(100, 0, 0))

    for i in range(8):
      self.tip_rack1.get_item(i).set_tip(Tip(total_tip_length=1, has_filter=True,
        maximal_volume=1, fitting_depth=1))
      self.tip_rack2.get_item(i).set_tip(Tip(total_tip_length=1, has_filter=True,
        maximal_volume=1, fitting_depth=1))

  async def test_pick_up_tips_success(self):
    """ Test that pick_up_tips works in the ideal case. """
    tm = TipManager(backend=self.backend, deck=self.deck)
    tm.pick_up_tips = AsyncMock()
    await tm.pick_up_tips_by_type(["Tip", "Tip"])
    tm.pick_up_tips.assert_called_once_with(
      [self.tip_rack1.get_item(0), self.tip_rack1.get_item(1)],
      use_channels=[0, 1]
    )

  async def test_pick_up_tips_full_column(self):
    """ Test that pick_up_tips prioritizes full columns. """
    # Empty the first column of tip_rack1
    for i in range(8):
      if i < 4: # A1, B1, C1, D1
        self.tip_rack1.get_item(i).set_tip(None)
    tm = TipManager(backend=self.backend, deck=self.deck)
    tm.pick_up_tips = AsyncMock()
    await tm.pick_up_tips_by_type(["Tip", "Tip", "Tip", "Tip"])
    # Should pick up from the second column of tip_rack1, which is full.
    tm.pick_up_tips.assert_called_once_with(
      self.tip_rack2.get_all_items()[0:4],
      use_channels=[0, 1, 2, 3]
    )

  async def test_pick_up_tips_retry(self):
    """ Test that pick_up_tips retries on failure. """
    tm = TipManager(backend=self.backend, deck=self.deck)
    tm.pick_up_tips = AsyncMock(side_effect=[
      ChannelizedError({0: Exception("Failed to pick up tip.")}),
      None
    ])
    await tm.pick_up_tips_by_type(["Tip", "Tip"])

    self.assertEqual(tm.pick_up_tips.call_count, 2)
    tm.pick_up_tips.assert_has_calls([
      call(self.tip_rack1.get_all_items()[0:2], use_channels=[0, 1]),
      call([self.tip_rack1.get_item(2)], use_channels=[0])
    ])

  async def test_pick_up_tips_out_of_tips(self):
    """ Test that pick_up_tips raises an error when out of tips. """
    tm = TipManager(backend=self.backend, deck=self.deck)
    tm.pick_up_tips = AsyncMock(side_effect=ChannelizedError({0: Exception("Failed.")}))
    with self.assertRaises(RuntimeError):
      await tm.pick_up_tips_by_type(["Tip"])

  async def test_pick_up_tips_marks_failed_spot_empty(self):
    """ Test that a failed tip spot is marked as empty. """
    tm = TipManager(backend=self.backend, deck=self.deck)
    tm.pick_up_tips = AsyncMock(side_effect=[
      ChannelizedError({0: Exception("Failed to pick up tip.")}),
      None
    ])
    await tm.pick_up_tips_by_type(["Tip"])
    self.assertFalse(self.tip_rack1.get_item(0).has_tip())

if __name__ == "__main__":
  unittest.main()
