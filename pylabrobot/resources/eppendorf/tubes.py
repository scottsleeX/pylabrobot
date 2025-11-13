from pylabrobot.resources.tube import Tube
import math


def _compute_volume_from_height_Eppendorf_1_5mL_Vb(h: float) -> float:
    a, b, c, d, e = -4.557517e-03, 2.866057e-01, -3.987186e+00, 3.075703e+01, -2.834161e+00
    V = a * h**4 + b * h**3 + c * h**2 + d * h + e
    return round(V,3)
    # R =  10.5/2
    # Hk = 20.
    # Hc = 16.

    # total_height = Hk + Hc
    # if not (0 <= h <= total_height):
    #     raise ValueError(f"Height must be between 0 and {total_height}")

    # # Case 1: Liquid is in the conical part (0 <= h <= Hk)
    # if h <= Hk:
    #     volume = (math.pi * R**2 * h**3) / (3 * Hk**2)
    #     print(f"input height < cone height: volume={volume}")
    #     return round(volume,3)

    # # Case 2: Liquid is in the cylindrical part (h > Hk)
    # else:
    #     volume_cone = (1/3) * math.pi * R**2 * Hk
    #     volume_in_cylinder = math.pi * R**2 * (h - Hk)
    #     print(f"input height > cone height: height={volume_cone+volume_in_cylinder}")
    #     return round(volume_cone + volume_in_cylinder,3)

def _compute_height_from_volume_Eppendorf_1_5mL_Vb(V: float) -> float:
    a, b, c, d, e = -1.462645e+01, 6.252253e+01, -9.364077e+01, 6.977987e+01, 9.578706e-01
    V /= 1000.
    V = a * V**4 + b * V**3 + c * V**2 + d * V + e
    return round(V,3)
    # R =  10.5/2
    # Hk = 20.
    # Hc = 16.

    # volume_cone = (1/3) * math.pi * R**2 * Hk
    # volume_cylinder = math.pi * R**2 * Hc
    # total_volume = volume_cone + volume_cylinder

    # if not (0 <= V <= total_volume):
    #     raise ValueError(f"Volume must be between 0 and {total_volume:.2f}")

    # # Case 1: Liquid is in the conical part (V <= Vk)
    # if V <= volume_cone:
    #     # Using the rearranged formula h = Hk * (V / Vk)^(1/3) for stability
    #     height = Hk * (V / volume_cone)**(1/3)
    #     print(f"input volume < cone: height={height}")
    #     return round(height,3)

    # # Case 2: Liquid is in the cylindrical part (V > Vk)
    # else:
    #     volume_in_cylinder = V - volume_cone
    #     height_in_cylinder = volume_in_cylinder / (math.pi * R**2)
    #     print(f"input volume > cone: height={height}")
    #     return round(Hk + height_in_cylinder,3)




def _compute_volume_from_height_Eppendorf_5mL_Vb(h: float) -> float:
    a, b, c, d, e = -2.085268e-03, 1.515189e-01, -7.119490e-01, 1.517639e+01, 1.040188e+01
    V = a * h**4 + b * h**3 + c * h**2 + d * h + e
    return round(V,3)
    # R =  16.5/2.
    # Hk = 25.
    # Hc = 28.

    # total_height = Hk + Hc
    # if not (0 <= h <= total_height):
    #     raise ValueError(f"Height must be between 0 and {total_height}")

    # # Case 1: Liquid is in the conical part (0 <= h <= Hk)
    # if h <= Hk:
    #     volume = (math.pi * R**2 * h**3) / (3 * Hk**2)
    #     print(f"input height < cone height: volume={volume}")
    #     return round(volume,3)

    # # Case 2: Liquid is in the cylindrical part (h > Hk)
    # else:
    #     volume_cone = (1/3) * math.pi * R**2 * Hk
    #     volume_in_cylinder = math.pi * R**2 * (h - Hk)
    #     print(f"input height > cone height: height={volume_cone+volume_in_cylinder}")
    #     return round(volume_cone + volume_in_cylinder,3)

def _compute_height_from_volume_Eppendorf_5mL_Vb(V: float) -> float:
    a, b, c, d, e, f = 2.253775e-01, -2.978262e+00, 1.478127e+01, -3.407929e+01, 4.278537e+01, 7.857063e-01
    V /= 1000.
    height = a * V**5 + b * V**4 + c * V**3 + d * V**2 + e * V + f
    return round(height,3)

    # R =  16.5/2.
    # Hk = 25.
    # Hc = 28.

    # volume_cone = (1/3) * math.pi * R**2 * Hk
    # volume_cylinder = math.pi * R**2 * Hc
    # total_volume = volume_cone + volume_cylinder

    # if not (0 <= V <= total_volume):
    #     raise ValueError(f"Volume must be between 0 and {total_volume:.2f}")

    # # Case 1: Liquid is in the conical part (V <= Vk)
    # if V <= volume_cone:
    #     # Using the rearranged formula h = Hk * (V / Vk)^(1/3) for stability
    #     height = Hk * (V / volume_cone)**(1/3)
    #     print(f"input volume < cone: height={height}")
    #     return round(height,3)

    # # Case 2: Liquid is in the cylindrical part (V > Vk)
    # else:
    #     volume_in_cylinder = V - volume_cone
    #     height_in_cylinder = volume_in_cylinder / (math.pi * R**2)
    #     print(f"input volume > cone: height={Hk + height_in_cylinder}")
    #     return round(Hk + height_in_cylinder,3)





def Eppendorf_DNA_LoBind_1_5ml_Vb(name: str, model="Eppendorf_DNA_LoBind_1_5ml_Vb") -> Tube:
  """1.5 mL round-bottom snap-cap Eppendorf tube.

  cat. no.: 022431021 (Eppendorf™ DNA LoBind™ Tubes)

  - bottom_type=TubeBottomType.V
  - snap-cap lid
  """
  diameter = 10.33  # measured
  return Tube(
    name=name,
    size_x=diameter,
    size_y=diameter,
    size_z=39.5,  # measured
    model="Eppendorf_DNA_LoBind_1_5ml_Vb",
    max_volume=1_400,
    material_z_thickness=0.8,  # measured
  )



def Eppendorf_1_5ml_Vb(name: str) -> Tube:
  """1.5 mL round-bottom snap-cap Eppendorf tube. cat. no.: 022431021

  - bottom_type=TubeBottomType.V
  - snap-cap lid
  """
  material_z_thickness = 3.5
  diameter = 10.6
  return Tube(
    name=name,
    size_x=diameter,
    size_y=diameter,
    size_z=38.6,
    model="Eppendorf_1_5ml_Vb",
    max_volume=1_500,  # units: ul
    material_z_thickness=material_z_thickness,
    compute_volume_from_height=_compute_volume_from_height_Eppendorf_1_5mL_Vb,
    compute_height_from_volume=_compute_height_from_volume_Eppendorf_1_5mL_Vb
  )



def Eppendorf_5ml_Vb(name: str) -> Tube:
  """1.5 mL round-bottom snap-cap Eppendorf tube. cat. no.: 022431021

  - bottom_type=TubeBottomType.V
  - snap-cap lid
  """
  material_z_thickness = 1.2
  diameter = 16.5
  return Tube(
    name=name,
    size_x=diameter,
    size_y=diameter,
    size_z=56,
    model="Eppendorf_5ml_Vb",
    max_volume=5_000,  # units: ul
    material_z_thickness=material_z_thickness,
    compute_volume_from_height=_compute_volume_from_height_Eppendorf_5mL_Vb,
    compute_height_from_volume=_compute_height_from_volume_Eppendorf_5mL_Vb
  )
def Eppendorf_Protein_LoBind_1_5ml_Vb(name: str) -> Tube:
  """1.5 mL round-bottom screw-cap Eppendorf tube.

  cat. no.: 022431081 (Eppendorf™ Protein LoBind™ Tubes)

  Same as Eppendorf_DNA_LoBind_1_5ml_Vb
  """
  return Eppendorf_DNA_LoBind_1_5ml_Vb(name=name, model="Eppendorf_Protein_LoBind_1_5ml_Vb")


def Eppendorf_DNA_LoBind_2ml_Ub(name: str) -> Tube:
  """2 mL round-bottom snap-cap Eppendorf tube. cat. no.: 022431048

  - bottom_type=TubeBottomType.U
  - snap-cap lid
  """
  diameter = 10.33  # measured
  return Tube(
    name=name,
    size_x=diameter,
    size_y=diameter,
    size_z=41,  # measured
    model="Eppendorf_DNA_LoBind_2ml_Ub",
    max_volume=2000,  # units: ul
    material_z_thickness=0.8,  # measured
  )
