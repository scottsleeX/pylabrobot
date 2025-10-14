from __future__ import annotations

import logging
from typing import List, TYPE_CHECKING

from pylabrobot.liquid_handling.errors import ChannelizedError
from pylabrobot.resources import Deck, TipRack, TipSpot
from pylabrobot.liquid_handling.liquid_handler import LiquidHandler
from pylabrobot.liquid_handling.backends.backend import LiquidHandlerBackend


if TYPE_CHECKING:
  from pylabrobot.liquid_handling.liquid_handler import LiquidHandler



logger = logging.getLogger(__name__)


class TipManager(LiquidHandler):
  """ A class to manage tip boxes and tip pickup with retries. """

  def __init__(self, backend: LiquidHandlerBackend, deck: Deck):
    super().__init__(backend=backend, deck=deck)
    self._tip_spot_lists: dict[str, list[TipSpot]] = {}
    self.refresh()

  def refresh(self):
    """ Refresh the list of available tips from the tip racks. """
    self._tip_spot_lists.clear()

    # Find all tip racks on the deck by traversing the resource tree.
    tip_racks = []
    resources_to_visit = [self.deck]
    while resources_to_visit:
      resource = resources_to_visit.pop(0)
      if isinstance(resource, TipRack):
        tip_racks.append(resource)
      resources_to_visit.extend(resource.children)

    for rack in tip_racks:
      # Group tip spots by the class name of the tip rack.
      rack_type = rack.__class__.__name__
      if rack_type not in self._tip_spot_lists:
        self._tip_spot_lists[rack_type] = []
      for spot in rack.get_all_items():
        if spot.has_tip():
          self._tip_spot_lists[rack_type].append(spot)

  async def pick_up_tips_by_type(
    self,
    tip_types: list[str],
    **kwargs,
  ):
    """ Pick up tips from specified rack types, with retries on failure.

    Args:
      tip_types: A list of tip rack types (as strings) to pick up tips from. The length of the
        list determines how many tips to pick up and which channels to use. For example:
        `["HTF", "HTF"]` will pick up two tips from the first available `HTF` racks.
      **kwargs: Additional keyword arguments to pass to `self.pick_up_tips`.
    """
    use_channels = kwargs.get("use_channels", list(range(len(tip_types))))
    if len(tip_types) != len(use_channels):
      raise ValueError("Length of tip_types must match length of use_channels.")

    # A copy of the tip spots we can try to use.
    candidate_tips = {
        tip_type: list(spots) for tip_type, spots in self._tip_spot_lists.items()
    }
    print(candidate_tips)

    # Map channels to the tip type they need to pick up.
    channel_tip_type_map = dict(zip(use_channels, tip_types))

    # Attempt to find a full column first, if all tip types are the same.
    if len(set(tip_types)) == 1:
      tip_type = tip_types[0]
      num_tips = len(tip_types)

      # Group spots by rack and column.
      columns = {}
      for spot in self._tip_spot_lists.get(tip_type, []):
        rack = spot.parent
        # Tip spots are named e.g. "A1", "B1", etc. The column is the number.
        col_id = int("".join(filter(str.isdigit, spot.name)))
        if (rack, col_id) not in columns:
          columns[(rack, col_id)] = []
        columns[(rack, col_id)].append(spot)

      for (rack, col_id), spots in sorted(columns.items(), key=lambda item: item[0][1]):
        if len(spots) >= num_tips:
          # Sort spots by name to ensure they are in order (A1, B1, C1...)
          spots.sort(key=lambda s: s.name)
          for i in range(len(spots) - num_tips + 1):
            spots_to_try = spots[i:i+num_tips]
            try:
              await self.pick_up_tips(spots_to_try, use_channels=use_channels, **kwargs)
              self.refresh()
              return # Success
            except ChannelageError as e:
              for channel in e.errors:
                spot_to_clear = spots_to_try[use_channels.index(channel)]
                spot_to_clear.set_tip(None)
              continue # Try next set of tips in the column.
            except Exception:
              logger.error("An unexpected error occurred during tip pickup.")
              raise

    # Fallback to original behavior if full column pickup is not possible or fails.
    attempted_spots = {}
    for channel, tip_type in channel_tip_type_map.items():
      if not candidate_tips.get(tip_type):
        raise RuntimeError(f"No available tips of type {tip_type}")
      attempted_spots[channel] = candidate_tips[tip_type].pop(0)

    while True:
      if not attempted_spots: # All tips picked up successfully.
        break

      channels_to_try = list(attempted_spots.keys())
      spots_to_try = list(attempted_spots.values())

      try:
        await self.pick_up_tips(spots_to_try, use_channels=channels_to_try, **kwargs)
        break # Success
      except ChannelizedError as e:
        logger.info("Failed to pick up tips on channels %s. Retrying with new tips.", e.errors)

        failed_channels = e.errors.keys()
        new_attempts = {}
        for channel in failed_channels:
          # Mark the failed tip spot as empty.
          spot_to_clear = attempted_spots[channel]
          spot_to_clear.set_tip(None)

          tip_type = channel_tip_type_map[channel]
          if not candidate_tips.get(tip_type):
            raise RuntimeError(f"Ran out of tips of type {tip_type} for channel {channel}.")
          new_attempts[channel] = candidate_tips[tip_type].pop(0)
        attempted_spots = new_attempts
      except Exception:
        logger.error("An unexpected error occurred during tip pickup.")
        raise

    self.refresh()
