"""Defines the EnhancedLiquidHandler class."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional, Sequence, Union

from pylabrobot.liquid_handling.liquid_handler import LiquidHandler
from pylabrobot.resources import (
    Container,
    Coordinate,
    Deck,
    Plate,
    TipRack,
    Trash,
    Well,
    TipSpot,
    does_volume_tracking,
    Tube,
)
from pylabrobot.liquid_handling.resources import adjust_resources_for_pipetting
from pylabrobot.machines.machine import need_setup_finished
from pylabrobot.liquid_handling.errors import ChannelizedError

logger = logging.getLogger(__name__)


class EnhancedLiquidHandler(LiquidHandler):
  """
  An enhanced liquid handler that automates parameter calculations and includes advanced
  tip management with retries.
  """

  def __init__(
      self,
      backend,
      deck,
      default_aspiration_params: Optional[Dict[str, Any]] = None,
      default_dispense_params: Optional[Dict[str, Any]] = None,
  ):
    """ Initialize the EnhancedLiquidHandler.

    Args:
      backend: The liquid handling backend to use.
      deck: The deck layout.
      default_aspiration_params: A dictionary of default parameters to pass to the backend's
        `aspirate` method. These will be used unless overridden in a specific `aspirate` call.
      default_dispense_params: A dictionary of default parameters to pass to the backend's
        `dispense` method. These will be used unless overridden in a specific `dispense` call.
    """
    super().__init__(backend=backend, deck=deck)
    self._tip_spot_lists: dict[str, list[TipSpot]] = {}
    self.default_aspiration_params = default_aspiration_params or {}
    self.default_dispense_params = default_dispense_params or {}
    self.refresh()

  def refresh(self):
    """ Refresh the list of available tips from the tip racks on the deck. """
    self._tip_spot_lists.clear()
    tip_racks = self.deck.get_resources(TipRack)
    for rack in tip_racks:
      rack_type = rack.model
      if rack_type is None:
        continue
      if rack_type not in self._tip_spot_lists:
        self._tip_spot_lists[rack_type] = []
      for spot in rack.get_all_items():
        if spot.has_tip():
          self._tip_spot_lists[rack_type].append(spot)

  async def pick_up_tips(
    self,
    tip_types: list[Union[str, TipSpot]],
    **kwargs,
  ):
    """ Pick up tips from specified rack models with retry logic, or directly from TipSpots. """
    if not tip_types:
        await super().pick_up_tips(tip_spots=[], **kwargs)
        return

    if isinstance(tip_types[0], TipSpot):
      await super().pick_up_tips(tip_spots=tip_types, **kwargs)
      return

    if isinstance(tip_types, str):
      tip_types = [tip_types]

    use_channels = kwargs.get("use_channels", list(range(len(tip_types))))
    if len(tip_types) != len(use_channels):
      raise ValueError("Length of tip_types must match length of use_channels.")

    candidate_tips = {
        tip_type: list(spots) for tip_type, spots in self._tip_spot_lists.items()
    }
    channel_tip_type_map = dict(zip(use_channels, tip_types))

    if len(set(tip_types)) == 1:
      tip_type = tip_types[0]
      num_tips = len(tip_types)
      columns = {}
      for spot in candidate_tips.get(tip_type, []):
        rack = spot.parent
        col_id = int("".join(filter(str.isdigit, spot.name)))
        columns.setdefault((rack, col_id), []).append(spot)

      for (rack, col_id), spots in sorted(columns.items(), key=lambda item: item[0][1]):
        if len(spots) >= num_tips:
          spots.sort(key=lambda s: s.name)
          for i in range(len(spots) - num_tips + 1):
            spots_to_try = spots[i:i+num_tips]
            try:
              await super().pick_up_tips(spots_to_try, use_channels=use_channels, **kwargs)
              self.refresh()
              return
            except ChannelizedError as e:
              for channel in e.errors:
                spot_to_clear = spots_to_try[use_channels.index(channel)]
                spot_to_clear.set_tip(None)
                if tip_type in candidate_tips and spot_to_clear in candidate_tips[tip_type]:
                  candidate_tips[tip_type].remove(spot_to_clear)
              break
            except Exception:
              logger.error("An unexpected error occurred during tip pickup.")
              raise

    attempted_spots = {}
    for channel, tip_type in channel_tip_type_map.items():
      if not candidate_tips.get(tip_type):
        raise RuntimeError(f"No available tips of type {tip_type}")
      attempted_spots[channel] = candidate_tips[tip_type].pop(0)

    while True:
      if not attempted_spots:
        break
      channels_to_try = list(attempted_spots.keys())
      spots_to_try = list(attempted_spots.values())
      try:
        await super().pick_up_tips(spots_to_try, use_channels=channels_to_try, **kwargs)
        break
      except ChannelizedError as e:
        logger.info("Failed to pick up tips on channels %s. Retrying.", e.errors)
        failed_channels = e.errors.keys()
        new_attempts = {}
        for channel in failed_channels:
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

  @need_setup_finished
  async def aspirate(
    self,
    resources: Sequence[Container],
    vols: List[float],
    use_channels: Optional[List[int]] = None,
    liquid_height: Optional[List[Optional[float]]] = None,
    **backend_kwargs,
  ):
    if not isinstance(resources, Sequence) or isinstance(resources, str):
        resources = [resources]
    self._check_containers(resources)
    use_channels_was_provided = use_channels is not None
    if not use_channels_was_provided:
        if self._default_use_channels is not None:
            use_channels = self._default_use_channels
        else:
            num_ops = len(vols) if len(resources) == 1 and isinstance(vols, list) and len(vols) > 1 else len(resources)
            use_channels = list(range(num_ops))
    num_ops = len(use_channels)
    if len(set(use_channels)) != num_ops:
        raise ValueError("Channels must be unique.")
    if use_channels_was_provided:
        if len(vols) != num_ops:
            raise ValueError(f"Length of `vols` ({len(vols)}) must equal length of `use_channels` ({num_ops}).")
    else:
        if len(vols) == 1 and num_ops > 1:
            vols = [vols[0]] * num_ops
        elif len(vols) != num_ops:
            raise ValueError(f"Length of `vols` ({len(vols)}) must be 1 or equal to inferred number of operations ({num_ops}).")

    if len(resources) == 1 and isinstance(resources[0], Tube) and len(use_channels) > 1:
        for i, channel in enumerate(use_channels):
            await self.aspirate(resources=resources, vols=[vols[i]], use_channels=[channel], **backend_kwargs)
        return

    resources = adjust_resources_for_pipetting(resources, len(use_channels))

    merged_backend_kwargs = {**self.default_aspiration_params, **backend_kwargs}

    if liquid_height is None and does_volume_tracking():
        liquid_height = [r.tracker.get_liquid_height() for r in resources]

    if "surface_following_distance" not in merged_backend_kwargs and does_volume_tracking():
        resource_to_total_vol = {}
        for i, r in enumerate(resources):
            r_id = id(r)
            if r_id not in resource_to_total_vol:
                resource_to_total_vol[r_id] = {"resource": r, "total_vol": 0}
            resource_to_total_vol[r_id]["total_vol"] += vols[i]

        sfd_list = []
        can_compute_sfd = True
        for r in resources:
            if not hasattr(r, "compute_height_from_volume"):
                can_compute_sfd = False
                break
            r_id = id(r)
            current_vol = r.tracker.get_volume()
            total_aspirate_vol = resource_to_total_vol[r_id]["total_vol"]
            sfd = r.compute_height_from_volume(current_vol) - r.compute_height_from_volume(current_vol - total_aspirate_vol)
            sfd_list.append(sfd)

        if can_compute_sfd:
            merged_backend_kwargs["surface_following_distance"] = sfd_list

    await super().aspirate(
        resources=resources,
        vols=vols,
        use_channels=use_channels,
        liquid_height=liquid_height,
        **merged_backend_kwargs,
    )

  @need_setup_finished
  async def dispense(
    self,
    resources: Sequence[Container],
    vols: List[float],
    use_channels: Optional[List[int]] = None,
    liquid_height: Optional[List[Optional[float]]] = None,
    **backend_kwargs,
  ):
    if not isinstance(resources, Sequence) or isinstance(resources, str):
        resources = [resources]
    self._check_containers(resources)
    use_channels_was_provided = use_channels is not None
    if not use_channels_was_provided:
        if self._default_use_channels is not None:
            use_channels = self._default_use_channels
        else:
            num_ops = len(vols) if len(resources) == 1 and isinstance(vols, list) and len(vols) > 1 else len(resources)
            use_channels = list(range(num_ops))
    num_ops = len(use_channels)
    if len(set(use_channels)) != num_ops:
        raise ValueError("Channels must be unique.")
    if use_channels_was_provided:
        if len(vols) != num_ops:
            raise ValueError(f"Length of `vols` ({len(vols)}) must equal length of `use_channels` ({num_ops}).")
    else:
        if len(vols) == 1 and num_ops > 1:
            vols = [vols[0]] * num_ops
        elif len(vols) != num_ops:
            raise ValueError(f"Length of `vols` ({len(vols)}) must be 1 or equal to inferred number of operations ({num_ops}).")

    if len(resources) == 1 and isinstance(resources[0], Tube) and len(use_channels) > 1:
        for i, channel in enumerate(use_channels):
            await self.dispense(resources=resources, vols=[vols[i]], use_channels=[channel], **backend_kwargs)
        return

    resources = adjust_resources_for_pipetting(resources, len(use_channels))

    if liquid_height is None and does_volume_tracking():
        liquid_height = [r.tracker.get_liquid_height() for r in resources]

    merged_backend_kwargs = {**self.default_dispense_params, **backend_kwargs}

    await super().dispense(
        resources=resources,
        vols=vols,
        use_channels=use_channels,
        liquid_height=liquid_height,
        **merged_backend_kwargs,
    )