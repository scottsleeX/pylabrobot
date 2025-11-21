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
    Trough,
)
from pylabrobot.liquid_handling.resources import adjust_resources_for_pipetting
from pylabrobot.machines.machine import need_setup_finished
from pylabrobot.liquid_handling.errors import ChannelizedError
from pylabrobot.liquid_handling.backends import STARBackend

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
      num_channels: int = 16,
      simulation: bool = True,
      default_aspiration_params: Optional[Dict[str, Any]] = None,
      default_dispense_params: Optional[Dict[str, Any]] = None,
  ):
    """ Initialize the EnhancedLiquidHandler.

    Args:
      backend: The liquid handling backend to use.
      deck: The deck layout.
      num_channels: The number of channels in the liquid handler.
      simulation: Whether the liquid handler is in simulation mode.
      default_aspiration_params: A dictionary of default parameters to pass to the backend's
        `aspirate` method. These will be used unless overridden in a specific `aspirate` call.
      default_dispense_params: A dictionary of default parameters to pass to the backend's
        `dispense` method. These will be used unless overridden in a specific `dispense` call.
    """
    super().__init__(backend=backend, deck=deck)
    self.num_channels = num_channels
    self.simulation = simulation
    self._tip_spot_lists: dict[str, list[TipSpot]] = {}
    self.default_aspiration_params = default_aspiration_params or {}
    self.default_dispense_params = default_dispense_params or {}
    # First refresh should not be async, as it's called in constructor
    self._sync_refresh()

  def _sync_refresh(self):
    """ Synchronous version of refresh for use in constructor. """
    self._tip_spot_lists.clear()
    tip_racks = []
    for resource in self.deck.children:
      if hasattr(resource, "sites"):
        for i in range(len(resource.sites)):
          holder = resource[i]
          item = holder.resource
          if isinstance(item, TipRack):
            tip_racks.append(item)
      elif isinstance(resource, TipRack):
        tip_racks.append(resource)

    for rack in tip_racks:
      rack_type = rack.model
      if rack_type is None:
        continue
      if rack_type not in self._tip_spot_lists:
        self._tip_spot_lists[rack_type] = []
      for spot in rack.get_all_items():
        if spot.has_tip():
          self._tip_spot_lists[rack_type].append(spot)

  async def refresh(self):
    """ Asynchronously refresh the list of available tips from the tip racks on the deck. """
    self._sync_refresh()

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

    num_tips = len(tip_types)
    if self.simulation:
      default_use_channels = list(range(num_tips))
    else:
      # default_use_channels = list(
      #     range(self.num_channels - 1, self.num_channels - 1 - num_tips, -1)
      # )
      # default_use_channels.sort()
      default_use_channels = list(range(num_tips))

    use_channels = kwargs.pop("use_channels", default_use_channels)
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
              await self.refresh()
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
    await self.refresh()

  def _is_compute_height_from_volume_implemented(self, resource: Container) -> bool:
    try:
        resource.compute_height_from_volume(0)
        return True
    except NotImplementedError:
        return False

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

    if len(resources) == 1 and isinstance(resources[0], (Tube, Trough)) and len(use_channels) > 1:
        for i, channel in enumerate(use_channels):
            await self.aspirate(resources=resources, vols=[vols[i]], use_channels=[channel], **backend_kwargs)
        return

    resources = adjust_resources_for_pipetting(resources, len(use_channels))

    merged_backend_kwargs = {**self.default_aspiration_params, **backend_kwargs}

    if liquid_height is None and does_volume_tracking():
        liquid_height = [r.compute_height_from_volume(r.tracker.get_used_volume()) if self._is_compute_height_from_volume_implemented(r) else None for r in resources]

    # if "immersion_depth" not in merged_backend_kwargs and liquid_height is not None:
    #     immersion_depths = [min(lh, 2.0) if lh is not None else None for lh in liquid_height]
    #     merged_backend_kwargs["immersion_depth"] = immersion_depths

    # if "lld_mode" not in merged_backend_kwargs and does_volume_tracking():
    #     lld_modes = [STARBackend.LLDMode.GAMMA if r.tracker.get_used_volume() > 0 else STARBackend.LLDMode.Z_TOUCH_OFF for r in resources]
    #     merged_backend_kwargs["lld_mode"] = lld_modes

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
            if not self._is_compute_height_from_volume_implemented(r):
                can_compute_sfd = False
                break
            r_id = id(r)
            current_vol = r.tracker.get_used_volume()
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

    if len(resources) == 1 and isinstance(resources[0], (Tube, Trough)) and len(use_channels) > 1:
        for i, channel in enumerate(use_channels):
            await self.dispense(resources=resources, vols=[vols[i]], use_channels=[channel], **backend_kwargs)
        return

    resources = adjust_resources_for_pipetting(resources, len(use_channels))

    if liquid_height is None and does_volume_tracking():
        liquid_height = [r.compute_height_from_volume(r.tracker.get_used_volume()) if self._is_compute_height_from_volume_implemented(r) else None for r in resources]

    merged_backend_kwargs = {**self.default_dispense_params, **backend_kwargs}

    # if "immersion_depth" not in merged_backend_kwargs and liquid_height is not None:
    #     immersion_depths = [min(lh, 2.0) if lh is not None else None for lh in liquid_height]
    #     merged_backend_kwargs["immersion_depth"] = immersion_depths

    # if "lld_mode" not in merged_backend_kwargs and does_volume_tracking():
    #     lld_modes = [STARBackend.LLDMode.GAMMA if r.tracker.get_used_volume() > 0 else STARBackend.LLDMode.Z_TOUCH_OFF for r in resources]
    #     merged_backend_kwargs["lld_mode"] = lld_modes

    await super().dispense(
        resources=resources,
        vols=vols,
        use_channels=use_channels,
        liquid_height=liquid_height,
        **merged_backend_kwargs,
    )

  @need_setup_finished
  async def transfer_chunk(
    self,
    source_wells: Union[Sequence[Well], Well],
    dest_wells: Union[Sequence[Well], Well],
    vols: Union[Sequence[float], float],
    tip_types: Optional[Union[str, List[str]]] = None,
    use_channels: Optional[List[int]] = None,
    aspirate_kwargs: Optional[dict] = None,
    dispense_kwargs: Optional[dict] = None,
    drop_tips: bool = True,
  ):
    """ Transfer a chunk of liquids from source wells to destination wells.
    This method performs a complete transfer operation for a chunk of transfers, which includes:
    1. Picking up tips (optional).
    2. Aspirating liquid from source wells.
    3. Dispensing liquid to destination wells.
    4. Dropping tips in the trash (optional).
    Args:
      source_wells: A well or a list of wells to aspirate from.
      dest_wells: A well or a list of wells to dispense to.
      vols: A volume or a list of volumes to transfer.
      tip_types: The type of tip to use for the transfer. Can be a single string or a list of
        strings. If a single string is provided, it will be used for all channels. If None, no tips
        will be picked up.
      use_channels: A list of channels to use for the transfer. If None, channels will be inferred.
      aspirate_kwargs: Keyword arguments to pass to the `aspirate` method.
      dispense_kwargs: Keyword arguments to pass to the `dispense` method.
      drop_tips: Whether to drop the tips after the transfer.
    """

    if not isinstance(source_wells, Sequence) or isinstance(source_wells, str):
        source_wells = [source_wells]
    if not isinstance(dest_wells, Sequence) or isinstance(dest_wells, str):
        dest_wells = [dest_wells]
    if not isinstance(vols, Sequence):
        vols = [vols]

    if use_channels is None:
      use_channels = list(range(len(vols)))

    # 1. Pick up tips
    if tip_types is not None:
      if isinstance(tip_types, str):
        tips_to_pick_up = [tip_types] * len(use_channels)
      else:
        tips_to_pick_up = tip_types

      if len(tips_to_pick_up) != len(use_channels):
        raise ValueError(
          f"Length of tip_types ({len(tips_to_pick_up)}) must match number of channels "
          f"({len(use_channels)})."
        )
      print(tips_to_pick_up)
      await self.pick_up_tips(tip_types=tips_to_pick_up, use_channels=use_channels)

    # 2. Aspirate
    aspirate_kwargs = aspirate_kwargs or {}
    print(source_wells)
    print(vols)
    await self.aspirate(resources=source_wells, vols=vols, use_channels=use_channels, **aspirate_kwargs)

    # 3. Dispense
    dispense_kwargs = dispense_kwargs or {}
    print(dest_wells)
    print(vols)
    await self.dispense(resources=dest_wells, vols=vols, use_channels=use_channels, **dispense_kwargs)

    # 4. Drop tips
    if drop_tips:
      trash = None
      for resource in self.deck.children:
        if isinstance(resource, Trash):
          trash = resource
          break
      if trash is None:
        # maybe it is in a holder
        for resource in self.deck.children:
          if hasattr(resource, "sites"):
            for i in range(len(resource.sites)):
              holder = resource[i]
              item = holder.resource
              if isinstance(item, Trash):
                trash = item
                break
          if trash is not None:
            break
      if trash is None:
        raise RuntimeError("No trash found on deck.")

      await self.discard_tips()