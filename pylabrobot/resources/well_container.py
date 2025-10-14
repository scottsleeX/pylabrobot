""" A tube or trough that has a single well can be seen as a container with a single well. This
mixin provides the ability to access that well using `__getitem__`, similar to how wells in a plate
can be accessed. """

from typing import List, Union

from .container import Container


class WellContainer:
  """ A container that has a single well. """

  def __getitem__(self, identifier: Union[str, int]) -> List[Container]:
    """ Get the item with the given identifier. """

    if identifier not in ["A1", 0]:
      raise IndexError(
        f"Identifier '{identifier}' is not valid for a single well container. "
        "Only 'A1' and 0 are supported."
      )
    return [self]