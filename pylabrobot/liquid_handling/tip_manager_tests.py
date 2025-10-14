import time
import asyncio  # Import asyncio for running async functions
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling import TipManager
from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend, STARBackend
from pylabrobot.visualizer.visualizer import Visualizer
from pylabrobot.resources import (
    Coordinate,
	STARDeck,
	TIP_CAR_480_A00,
	TIP_50ul_w_filter,
	PLT_CAR_L5AC_A00,
	Cor_96_wellplate_1mL_Vb,
	MFX_CAR_L5_base,
	Trough_CAR_4R200_A00,
	Trough_CAR_5X60_A00,
	Tube_CAR_24_A00,
	Tube_CAR_32_A00,
	HTF,
	STF,
	Hamilton_1_trough_60ml_Vb,
	AGenBio_1_troughplate_190000uL_Fl,
	Thermo_Nunc_96_well_plate_1300uL_Rb,
	Eppendorf_96_wellplate_250ul_Vb,
	BioRad_384_wellplate_50uL_Vb,
    PLT_CAR_L5PCR_A01,
    PCR_Plate_96_Well,
    Thermo_TS_96_wellplate_1200ul_Rb,
    )
from pylabrobot.resources.eppendorf.tubes import (
	Eppendorf_1_5ml_Vb,
	Eppendorf_5ml_Vb,
)
from pylabrobot.liquid_handling.liquid_classes.hamilton import (
  get_star_liquid_class,
)
from pylabrobot.resources import set_tip_tracking, set_volume_tracking
from pylabrobot.heating_shaking import HeaterShaker
from pylabrobot.heating_shaking.chatterbox import HeaterShakerChatterboxBackend
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources import Deck, Well, Resource, ItemizedResource, Tube, Trough, Plate, Liquid
from typing import List, cast
from pylabrobot.liquid_handling.liquid_classes.hamilton import get_star_liquid_class

async def main():
    # --- Liquid Handler Setup ---
    print("Setting up Liquid Handler...")
    backend = STARBackend()
    deck = STARDeck()
    lh = TipManager(backend=LiquidHandlerChatterboxBackend(), deck=deck)
    await lh.setup()
    print("Liquid Handler setup complete.")

    # --- Visualizer Setup ---
    print("Setting up Visualizer...")
    # vis = Visualizer(resource=lh)
    # await vis.setup()

    set_tip_tracking(True)
    set_volume_tracking(True)

    # --- Main Code ---
        # --- Deck Setup ---
    # In this script, we are setting up the deck of the Hamilton liquid handling robot.
    # This involves defining the carriers, the labware (plates, tip racks, tubes),
    # and assigning them to their specific locations on the deck.

    # Pre-defined carriers are created and assigned to the deck rails as specified in the layout.
    # These carriers will hold all the necessary labware for the experiment.

    # Define the carrier for tips at slot 1
    tip_carrier1 = TIP_CAR_480_A00(name='tip_carrier1')
    lh.deck.assign_child_resource(tip_carrier1, rails=1)

    # Define the carrier for tips at slot 8
    tip_carrier2 = TIP_CAR_480_A00(name='tip_carrier2')
    lh.deck.assign_child_resource(tip_carrier2, rails=8)

    # Define a single carrier for all plates at slot 15 to ensure compactness.
    plate_carrier1 = PLT_CAR_L5AC_A00(name='plate_carrier1')
    lh.deck.assign_child_resource(plate_carrier1, rails=15)

    # Define the carrier for plates at slot 22
    plate_carrier2 = PLT_CAR_L5AC_A00(name='plate_carrier2')
    lh.deck.assign_child_resource(plate_carrier2, rails=22)

    # Define the carrier for PCR plates at slot 29
    PCR_plate_carrier = PLT_CAR_L5PCR_A01(name='PCR_plate_carrier')
    lh.deck.assign_child_resource(PCR_plate_carrier, rails=29)

    # Define the carrier for narrow troughs at slot 36
    narrow_trough_carrier = Trough_CAR_5X60_A00(name='narrow_trough_carrier')
    lh.deck.assign_child_resource(narrow_trough_carrier, rails=36)

    # Define the carrier for 1.5mL tubes at slot 38
    tube_carrier_32 = Tube_CAR_32_A00(name='tube_carrier_32')
    lh.deck.assign_child_resource(tube_carrier_32, rails=38)

    # Define the carrier for 5mL tubes at slot 40
    tube_carrier_24 = Tube_CAR_24_A00(name='tube_carrier_24')
    lh.deck.assign_child_resource(tube_carrier_24, rails=40)

    # Tip setup
    # A single box of 50uL tips is required for the protocol.
    tips_50ul_1 = TIP_50ul_w_filter(name='tips_50ul_1')
    tip_carrier1[0] = tips_50ul_1

    tips_50ul_2 = STF(name='STF_name')
    tip_carrier1[1] = tips_50ul_2

    tips_50ul_3 = HTF(name='HTF_name')
    tip_carrier1[2] = tips_50ul_3

    tips_50ul_4 = HTF(name='HTF_name2')
    tip_carrier1[3] = tips_50ul_4

    lh.refresh()

    # Source labware setup
    # This section defines the plates and tubes containing the source reagents
    # and sets their initial liquid volumes.

    # Nuclease-Free Water is placed in a single-well plate on plate_carrier1.
    nuclease_free_water_plate = AGenBio_1_troughplate_190000uL_Fl(name='nuclease_free_water_plate')
    plate_carrier1[0] = nuclease_free_water_plate
    nuclease_free_water_plate.set_well_liquids([('Nuclease-Free Water', 218.385)])
    nuclease_free_water_volume = 218.385

    # Reagent tubes are placed on the tube_carrier_32.
    q5_hot_start_tube = Eppendorf_1_5ml_Vb(name='q5_hot_start_tube')
    tube_carrier_32[0] = q5_hot_start_tube
    q5_hot_start_tube.set_liquids([('Q5 Hot Start High-Fidelity 2X Master Mix', 158.125)])
    q5_hot_start_volume = 158.125

    dmso_tube = Eppendorf_1_5ml_Vb(name='dmso_tube')
    tube_carrier_32[1] = dmso_tube
    dmso_tube.set_liquids([('DMSO', 100.0)])
    dmso_volume = 100.0

    onetaq_hot_start_tube = Eppendorf_1_5ml_Vb(name='onetaq_hot_start_tube')
    tube_carrier_32[2] = onetaq_hot_start_tube
    onetaq_hot_start_tube.set_liquids([('OneTaq Hot Start 2X Master Mix with Standard Buffer', 100.0)])
    onetaq_hot_start_volume = 100.0

    # Destination labware setup
    # This section defines the destination plates for the PCR mastermix.
    # These plates are initially empty and are placed on the same carrier as the source plate.

    destination_plate_group_3 = BioRad_384_wellplate_50uL_Vb(name='DestinationPlate_group_3')
    plate_carrier1[1] = destination_plate_group_3

    destination_plate_group_4 = BioRad_384_wellplate_50uL_Vb(name='DestinationPlate_group_4')
    plate_carrier1[2] = destination_plate_group_4

    destination_plate_group_2 = BioRad_384_wellplate_50uL_Vb(name='DestinationPlate_group_2')
    plate_carrier1[3] = destination_plate_group_2

    destination_plate_group_1 = BioRad_384_wellplate_50uL_Vb(name='DestinationPlate_group_1')
    plate_carrier1[4] = destination_plate_group_1

        # --- Operations ---
    # ### Error Correction Analysis
    # The previous code failed with a `pylabrobot.resources.errors.TooLittleLiquidError`. The traceback indicates that the script attempted to aspirate 15.0 uL of "Q5 Hot Start High-Fidelity 2X Master Mix" from `q5_hot_start_tube` when only 8.125 uL was available.
    # The root cause is a cumulative volume deficit. The protocol specifies 11 separate aspirations of 15.0 uL from this tube, for a total required volume of 165.0 uL (11 * 15.0). However, the initial volume in `q5_hot_start_tube` is only 158.125 uL. The script fails on the 11th aspiration because the total required volume exceeds the initial supply.
    # I will correct this by reducing the aspiration volume for all 11 transfers involving "Q5 Hot Start High-Fidelity 2X Master Mix". I will change the aspiration volume from 15.0 uL to 14.0 uL. This reduces the total required volume to 154.0 uL (11 * 14.0), which is safely below the initial 158.125 uL, while still providing a 1.5 uL overage for each 12.5 uL dispense.

    # Operations for DestinationPlate_group_1

    # Step 1: Transfer Nuclease-Free Water
    await lh.pick_up_tips(["STF"])
    # await lh.pick_up_tips(tips_50ul_1["A1:C1"])
    time.sleep(0.2)
    await lh.aspirate(dmso_tube["A1"],vols=[1,2])
    await lh.dispense(dmso_tube["A1"],vols=[1,2])
    await lh.discard_tips()
    time.sleep(0.2)

    await lh.pick_up_tips(["STF"])
    time.sleep(0.2)
    await lh.discard_tips()

    # --- Cleanup ---
    print("--- Cleaning up Liquid Handler ---")
    await lh.stop()
    # await vis.stop()
    print("Cleanup complete.")


if __name__ == "__main__":
    asyncio.run(main())

