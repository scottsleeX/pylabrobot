import enum
from typing import Callable, Optional, Union, List, Tuple, Sequence

from .container import Container
from .errors import ResourceNotFoundError
from .liquid import Liquid
from .well_container import WellContainer


class TroughBottomType(enum.Enum):
  """Enum for the type of bottom of a trough."""
  FLAT = "flat"
  U = "U"
  V = "V"
  UNKNOWN = "unknown"


class Trough(WellContainer, Container):
  """A trough is a container, particularly useful for multichannel liquid handling operations."""

  def __init__(
    self,
    name: str,
    size_x: float,
    size_y: float,
    size_z: float,
    max_volume: float,
    material_z_thickness: Optional[float] = None,
    through_base_to_container_base: float = 0,
    category: Optional[str] = "trough",
    model: Optional[str] = None,
    bottom_type: Union[TroughBottomType, str] = TroughBottomType.UNKNOWN,
    compute_volume_from_height: Optional[Callable[[float], float]] = None,
    compute_height_from_volume: Optional[Callable[[float], float]] = None,
  ):
    if isinstance(bottom_type, str):
      bottom_type = TroughBottomType(bottom_type)

    super().__init__(
      name=name,
      size_x=size_x,
      size_y=size_y,
      size_z=size_z,
      material_z_thickness=material_z_thickness,
      max_volume=max_volume,
      category=category,
      model=model,
      compute_volume_from_height=compute_volume_from_height,
      compute_height_from_volume=compute_height_from_volume,
    )
    self.through_base_to_container_base = through_base_to_container_base
    self.bottom_type = bottom_type

    self.tracker.register_callback(self._state_updated)

  def serialize(self) -> dict:
    return {**super().serialize(), "max_volume": self.max_volume}

  def set_liquids(self, liquids: List[Tuple[Optional["Liquid"], float]]):
    """Set the liquids in the tube.

    (wraps :meth:`~.VolumeTracker.set_liquids`)

    Example:
      Set the liquids in a tube to 10 uL of water:

      >>> tube.set_liquids([(Liquid.WATER, 10)])
    """

    self.tracker.set_liquids(liquids)

  def get_trough(self, identifier: Union[str, int, Tuple[int, int]]) -> "Trough":
    """Get the trough itself, if the identifier is valid for a single-item rack."""
    if identifier in ("A1", 0, (0, 0)):
      return self
    raise ResourceNotFoundError(f"Trough {self.name} does not have an item with identifier '{identifier}'.")

  def get_troughs(self, identifier: Union[str, Sequence[int]]) -> List["Trough"]:
    """Get the trough itself as a list, if the identifier is valid for a single-item rack."""
    if (isinstance(identifier, str) and identifier == "A1") or \
       (isinstance(identifier, Sequence) and not isinstance(identifier, str) and len(identifier) == 1 and identifier[0] == 0):
      return [self]
    raise ResourceNotFoundError(f"Trough {self.name} does not have items with identifier '{identifier}'.")

  def __getitem__(self, identifier: Union[str, int, Tuple[int, int]]) -> "Trough":
    """Get the trough itself, if the identifier is valid for a single-item rack."""
    return self.get_trough(identifier)

  @property
  def num_items(self) -> int:
    return 1

  def get_all_items(self) -> List["Trough"]:
    return [self]

  def set_well_liquids(
    self,
    liquids: Union[
      List[List[Tuple[Optional["Liquid"], Union[int, float]]]],
      List[Tuple[Optional["Liquid"], Union[int, float]]],
      Tuple[Optional["Liquid"], Union[int, float]],
    ],
  ) -> None:
    """Update the liquid in the volume tracker for the trough.

    Behaves like :meth:`pylabrobot.resources.TroughRack.set_well_liquids` for a single trough.
    """

    if isinstance(liquids, tuple):
      liquids = [liquids]
    elif isinstance(liquids, list) and len(liquids) > 0 and isinstance(liquids[0], list):
      if len(liquids) == 1 and len(liquids[0]) == 1:
        liquids = liquids[0]
      else:
        raise ValueError("For a single trough, liquids must be a single item or a 1x1 list of lists.")

    if len(liquids) != 1:
      raise ValueError(
        f"Number of liquids ({len(liquids)}) does not match number of troughs (1) in Trough '{self.name}'."
      )

    self.set_liquids(liquids)

  def disable_volume_trackers(self) -> None:
    """Disable volume tracking for this trough."""
    self.tracker.disable()

  def enable_volume_trackers(self) -> None:
    """Enable volume tracking for this trough."""
    self.tracker.enable()
