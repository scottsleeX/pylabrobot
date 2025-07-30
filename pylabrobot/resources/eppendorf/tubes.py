from pylabrobot.resources.tube import Tube
import math


def _compute_volume_from_height_Eppendorf_1_5mL_Vb(h: float) -> float:
    R =  10.5/2
    Hk = 20.
    Hc = 16.

    total_height = Hk + Hc
    if not (0 <= h <= total_height):
        raise ValueError(f"Height must be between 0 and {total_height}")

    # Case 1: Liquid is in the conical part (0 <= h <= Hk)
    if h <= Hk:
        volume = (math.pi * R**2 * h**3) / (3 * Hk**2)
        print(f"input height < cone height: volume={volume}")
        return round(volume,3)

    # Case 2: Liquid is in the cylindrical part (h > Hk)
    else:
        volume_cone = (1/3) * math.pi * R**2 * Hk
        volume_in_cylinder = math.pi * R**2 * (h - Hk)
        print(f"input height > cone height: height={volume_cone+volume_in_cylinder}")
        return round(volume_cone + volume_in_cylinder,3)

def _compute_height_from_volume_Eppendorf_1_5mL_Vb(V: float) -> float:
    R =  10.5/2
    Hk = 20.
    Hc = 16.

    volume_cone = (1/3) * math.pi * R**2 * Hk
    volume_cylinder = math.pi * R**2 * Hc
    total_volume = volume_cone + volume_cylinder

    if not (0 <= V <= total_volume):
        raise ValueError(f"Volume must be between 0 and {total_volume:.2f}")

    # Case 1: Liquid is in the conical part (V <= Vk)
    if V <= volume_cone:
        # Using the rearranged formula h = Hk * (V / Vk)^(1/3) for stability
        height = Hk * (V / volume_cone)**(1/3)
        print(f"input volume < cone: height={height}")
        return round(height,3)

    # Case 2: Liquid is in the cylindrical part (V > Vk)
    else:
        volume_in_cylinder = V - volume_cone
        height_in_cylinder = volume_in_cylinder / (math.pi * R**2)
        print(f"input volume > cone: height={height}")
        return round(Hk + height_in_cylinder,3)




def _compute_volume_from_height_Eppendorf_5mL_Vb(h: float) -> float:
    R =  16.5/2.
    Hk = 25.
    Hc = 28.

    total_height = Hk + Hc
    if not (0 <= h <= total_height):
        raise ValueError(f"Height must be between 0 and {total_height}")

    # Case 1: Liquid is in the conical part (0 <= h <= Hk)
    if h <= Hk:
        volume = (math.pi * R**2 * h**3) / (3 * Hk**2)
        print(f"input height < cone height: volume={volume}")
        return round(volume,3)

    # Case 2: Liquid is in the cylindrical part (h > Hk)
    else:
        volume_cone = (1/3) * math.pi * R**2 * Hk
        volume_in_cylinder = math.pi * R**2 * (h - Hk)
        print(f"input height > cone height: height={volume_cone+volume_in_cylinder}")
        return round(volume_cone + volume_in_cylinder,3)

def _compute_height_from_volume_Eppendorf_5mL_Vb(V: float) -> float:
    R =  16.5/2.
    Hk = 25.
    Hc = 28.

    volume_cone = (1/3) * math.pi * R**2 * Hk
    volume_cylinder = math.pi * R**2 * Hc
    total_volume = volume_cone + volume_cylinder

    if not (0 <= V <= total_volume):
        raise ValueError(f"Volume must be between 0 and {total_volume:.2f}")

    # Case 1: Liquid is in the conical part (V <= Vk)
    if V <= volume_cone:
        # Using the rearranged formula h = Hk * (V / Vk)^(1/3) for stability
        height = Hk * (V / volume_cone)**(1/3)
        print(f"input volume < cone: height={height}")
        return round(height,3)

    # Case 2: Liquid is in the cylindrical part (V > Vk)
    else:
        volume_in_cylinder = V - volume_cone
        height_in_cylinder = volume_in_cylinder / (math.pi * R**2)
        print(f"input volume > cone: height={Hk + height_in_cylinder}")
        return round(Hk + height_in_cylinder,3)





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
  material_z_thickness = 1
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
  # material_z_thickness = 2.4 mm
  material_z_thickness = 1
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
