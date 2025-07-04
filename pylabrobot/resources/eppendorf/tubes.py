from pylabrobot.resources.tube import Tube


def Eppendorf_DNA_LoBind_1_5ml_Vb(name: str) -> Tube:
  """1.5 mL round-bottom snap-cap Eppendorf tube. cat. no.: 022431021

  - bottom_type=TubeBottomType.V
  - snap-cap lid
  """
  # material_z_thickness = 2.4 mm
  diameter = 17
  return Tube(
    name=name,
    size_x=diameter,
    size_y=diameter,
    size_z=39,
    model="Eppendorf_DNA_LoBind_1_5ml_Vb",
    max_volume=1_400,  # units: ul
  )



def Eppendorf_1_5ml_Vb(name: str) -> Tube:
  """1.5 mL round-bottom snap-cap Eppendorf tube. cat. no.: 022431021

  - bottom_type=TubeBottomType.V
  - snap-cap lid
  """
  material_z_thickness = 1.0
  diameter = 10.6
  return Tube(
    name=name,
    size_x=diameter,
    size_y=diameter,
    size_z=38.6,
    model="Eppendorf_1_5ml_Vb",
    max_volume=1_500,  # units: ul
    material_z_thickness=material_z_thickness
  )



def Eppendorf_5ml_Vb(name: str) -> Tube:
  """1.5 mL round-bottom snap-cap Eppendorf tube. cat. no.: 022431021

  - bottom_type=TubeBottomType.V
  - snap-cap lid
  """
  material_z_thickness = 1.0
  diameter = 16.5
  return Tube(
    name=name,
    size_x=diameter,
    size_y=diameter,
    size_z=56,
    model="Eppendorf_5ml_Vb",
    max_volume=5_000,  # units: ul
    material_z_thickness=material_z_thickness
  )
