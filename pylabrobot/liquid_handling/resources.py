from typing import List, Sequence

from pylabrobot.resources.container import Container
from pylabrobot.resources.tube import Tube

def adjust_resources_for_pipetting(
  resources: Sequence[Container],
  num_channels: int
) -> List[Container]:
  """ Adjusts the resources for pipetting operations.

  If a single resource is provided for a multi-channel operation, it is duplicated for each
  channel. For Tubes, this is handled serially in the liquid handler, so the resource is not
  duplicated here.
  """

  if len(resources) == 1 and num_channels > 1:
    if not isinstance(resources[0], Tube):
      return [resources[0]] * num_channels
  return list(resources)