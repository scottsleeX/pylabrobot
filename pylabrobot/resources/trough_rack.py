from typing import Dict, List, Optional, Sequence, Tuple, Union, cast

from pylabrobot.resources.itemized_resource import ItemizedResource
from pylabrobot.resources.trough import Trough

from .liquid import Liquid
from .resource import Coordinate, Resource


class TroughRack(ItemizedResource[Trough]):
  """Trough rack resource."""

  def __init__(
    self,
    name: str,
    size_x: float,
    size_y: float,
    size_z: float,
    ordered_items: Optional[Dict[str, Trough]] = None,
    model: Optional[str] = None,
  ):
    """Initialize a TroughRack resource.

    Args:
      name: Name of the trough rack.
      size_x: Size of the trough rack in the x direction.
      size_y: Size of the trough rack in the y direction.
      size_z: Size of the trough rack in the z direction.
      items: List of lists of troughs.
      model: Model of the trough rack.
    """
    super().__init__(
      name=name,
      size_x=size_x,
      size_y=size_y,
      size_z=size_z,
      ordered_items=ordered_items,
      model=model,
    )

  def assign_child_resource(
    self,
    resource: Resource,
    location: Optional[Coordinate] = None,
    reassign: bool = True,
  ):
    assert location is not None, "Location must be specified for resource."
    return super().assign_child_resource(resource, location=location, reassign=reassign)

  def __repr__(self) -> str:
    return (
      f"{self.__class__.__name__}(name={self.name!r}, size_x={self._size_x}, "
      f"size_y={self._size_y}, size_z={self._size_z}, location={self.location})"
    )

  def get_trough(self, identifier: Union[str, int, Tuple[int, int]]) -> Trough:
    """Get the item with the given identifier.

    See :meth:`~.get_item` for more information.
    """

    return super().get_item(identifier)

  def get_troughs(self, identifier: Union[str, Sequence[int]]) -> List[Trough]:
    """Get the troughs with the given identifier.

    See :meth:`~.get_items` for more information.
    """

    return super().get_items(identifier)

  def set_well_liquids(
    self,
    liquids: Union[
      List[List[Tuple[Optional["Liquid"], Union[int, float]]]],
      List[Tuple[Optional["Liquid"], Union[int, float]]],
      Tuple[Optional["Liquid"], Union[int, float]],
    ],
  ) -> None:
    """Update the liquid in the volume tracker for each trough in the rack.

    Args:
      liquids: A list of liquids, one for each trough in the rack. The list can be a list of lists,
        where each inner list contains the liquids for each trough in a column. If a single tuple is
        given, the volume is assumed to be the same for all troughs. Liquids are in uL.

    Raises:
      ValueError: If the number of liquids does not match the number of troughs in the rack.

    Example:
      Set the volume of each trough in a 1x12 rack to 1000 uL.

      >>> rack = TroughRack("rack", 127.76, 85.48, 14.5, num_items_x=12, num_items_y=1)
      >>> rack.set_trough_liquids((Liquid.WATER, 1000))
    """

    if isinstance(liquids, tuple):
      liquids = [liquids] * self.num_items
    elif isinstance(liquids, list) and all(isinstance(column, list) for column in liquids):
      # mypy doesn't know that all() checks the type
      liquids = cast(List[List[Tuple[Optional["Liquid"], float]]], liquids)
      liquids = [list(column) for column in zip(*liquids)]  # transpose the list of lists
      liquids = [volume for column in liquids for volume in column]  # flatten the list of lists

    if len(liquids) != self.num_items:
      raise ValueError(
        f"Number of liquids ({len(liquids)}) does not match number of troughs "
        f"({self.num_items}) in rack '{self.name}'."
      )

    for i, (liquid, volume) in enumerate(liquids):
      trough = self.get_trough(i)
      trough.tracker.set_liquids([(liquid, volume)])  # type: ignore

  def disable_volume_trackers(self) -> None:
    """Disable volume tracking for all troughs in the rack."""

    for trough in self.get_all_items():
      trough.tracker.disable()

  def enable_volume_trackers(self) -> None:
    """Enable volume tracking for all troughs in the rack."""

    for trough in self.get_all_items():
      trough.tracker.enable()
