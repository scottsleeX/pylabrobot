import unittest
from unittest.mock import AsyncMock, MagicMock, call

from pylabrobot.liquid_handling.errors import ChannelizedError
from pylabrobot.liquid_handling.tip_manager import TipManager
from pylabrobot.resources import Deck, STF_L, TipRack, TipSpot, Tip

class TestTipManager(unittest.IsolatedAsyncioTestCase):
  """ Tests for the TipManager class. """

  def setUp(self):
    self.deck = Deck()
    self.tip_rack1 = TipRack("tip_rack1", "A1", "B1", num_items=8)
    self.tip_rack2 = TipRack("tip_rack2", "A1", "B1", num_items=8)
    self.deck.assign_child_resource(self.tip_rack1, location=(0, 0, 0))
    self.deck.assign_child_resource(self.tip_rack2, location=(100, 0, 0))

    for i in range(8):
      self.tip_rack1.get_item(i).set_tip(Tip(name="STF", total_tip_length=1, has_filter=True,
        maximal_volume=1, fitting_depth=1))
      self.tip_rack2.get_item(i).set_tip(Tip(name="STF", total_tip_length=1, has_filter=True,
        maximal_volume=1, fitting_depth=1))

    self.lh = MagicMock()
    self.lh.pick_up_tips = AsyncMock()

  async def test_pick_up_tips_success(self):
    """ Test that pick_up_tips works in the ideal case. """
    tm = TipManager(deck=self.deck)
    await tm.pick_up_tips(self.lh, ["STF", "STF"])
    self.lh.pick_up_tips.assert_called_once_with(
      [self.tip_rack1.get_item(0), self.tip_rack1.get_item(1)],
      use_channels=[0, 1]
    )

  async def test_pick_up_tips_full_column(self):
    """ Test that pick_up_tips prioritizes full columns. """
    # Empty the first column of tip_rack1
    for i in range(8):
      if i < 4: # A1, B1, C1, D1
        self.tip_rack1.get_item(i).set_tip(None)
    tm = TipManager(deck=self.deck)
    await tm.pick_up_tips(self.lh, ["STF", "STF", "STF", "STF"])
    # Should pick up from the second column of tip_rack1, which is full.
    self.lh.pick_up_tips.assert_called_once_with(
      self.tip_rack2.get_all_items()[0:4],
      use_channels=[0, 1, 2, 3]
    )

  async def test_pick_up_tips_retry(self):
    """ Test that pick_up_tips retries on failure. """
    self.lh.pick_up_tips.side_effect = [
      ChannelizedError({0: Exception("Failed to pick up tip.")}),
      None
    ]
    tm = TipManager(deck=self.deck)
    await tm.pick_up_tips(self.lh, ["STF", "STF"])

    self.assertEqual(self.lh.pick_up_tips.call_count, 2)
    self.lh.pick_up_tips.assert_has_calls([
      call(self.tip_rack1.get_all_items()[0:2], use_channels=[0, 1]),
      call([self.tip_rack1.get_item(2)], use_channels=[0])
    ])

  async def test_pick_up_tips_out_of_tips(self):
    """ Test that pick_up_tips raises an error when out of tips. """
    # Make it fail every time.
    self.lh.pick_up_tips.side_effect = ChannelizedError({0: Exception("Failed.")})
    deck = Deck()
    tip_rack = TipRack("tip_rack1", "A1", "B1", num_items=8)
    deck.assign_child_resource(tip_rack, location=(0, 0, 0))
    for i in range(8):
      tip_rack.get_item(i).set_tip(Tip(name="STF", total_tip_length=1, has_filter=True,
        maximal_volume=1, fitting_depth=1))
    tm = TipManager(deck=deck)
    with self.assertRaises(RuntimeError):
      await tm.pick_up_tips(self.lh, ["STF"])

  async def test_pick_up_tips_marks_failed_spot_empty(self):
    """ Test that a failed tip spot is marked as empty. """
    self.lh.pick_up_tips.side_effect = [
      ChannelizedError({0: Exception("Failed to pick up tip.")}),
      None
    ]
    tm = TipManager(deck=self.deck)
    await tm.pick_up_tips(self.lh, ["STF"])
    self.assertFalse(self.tip_rack1.get_item(0).has_tip())

if __name__ == "__main__":
  unittest.main()
