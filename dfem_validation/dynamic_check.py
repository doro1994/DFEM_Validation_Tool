# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 14:11:25 2022

@author: DONIK94
"""
from . import bdf_template
from pathlib import Path
from . import nastran_functions as nf
from sys import platform


def add_subcases(text, CoG_grid_id, mark="<<SUBCASES>>"):
    output = f"""
$ Modal
SUBCASE=1
    SUBTITLE=MODAL
    LABEL=MODAL
    METHOD=1
    
GROUNDCHECK(SET=ALL,GRID={int(CoG_grid_id):8d},SET=ALL,DATAREC=YES,RTHRESH=0.1)=YES
"""
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def add_load_introduction(text, EIGRL_card, CoG_grid_card, mark="<<LOADS_BULKDATA>>"):
    output = f"""
$_______________________________________________________________________
$
$                       L O A D  I N T R O D U C T I O N
$_______________________________________________________________________
"""
    output += CoG_grid_card + "\n"
    output += EIGRL_card + "\n"
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def add_bc(text, SPC_ID, CoG_grid_id, mark="<<SPC_BULKDATA>>"):
    output = f"""
$_______________________________________________________________________
$
$                       B O U N D A R Y
$_______________________________________________________________________
$      ><      ><      ><      ><      ><      ><      ><      ><      >
SPC1    {int(SPC_ID):8d}  123456{int(CoG_grid_id):8d}
"""
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def create_bdf(
    text, CoG_grid_id, CoG_grid_card, SPC_ID, spcadd_card, filename="Dynamic_check.dat"
):

    if spcadd_card == []:
        SPC_ID_global = SPC_ID
    else:
        SPC_ID_global = spcadd_card[1]

    dynamic_check_text = bdf_template.add_title(title="Dynamic Check", text=text)
    dynamic_check_text = dynamic_check_text.replace("SOL 101", "SOL 103")
    dynamic_check_text = bdf_template.add_SPC_ID(
        SPC_ID=SPC_ID_global, text=dynamic_check_text
    )
    dynamic_check_text = bdf_template.add_result_request(
        text=dynamic_check_text,
        disp=False,
        spcforce=True,
        mpcforce=False,
        stress=False,
        vector=True,
        ese=True,
    )

    dynamic_check_text = add_subcases(text=dynamic_check_text, CoG_grid_id=CoG_grid_id)

    EIGRL_card = f"""
$      ><      ><      ><      ><      ><      ><      ><      ><      >
EIGRL    1                      21      0                       MAX
"""
    dynamic_check_text = add_load_introduction(
        text=dynamic_check_text, CoG_grid_card=CoG_grid_card, EIGRL_card=EIGRL_card
    )

    dynamic_check_text = bdf_template.add_spc_constrain(
        text=dynamic_check_text, SPC_ID=SPC_ID, grid_id=CoG_grid_id
    )

    if spcadd_card != []:
        spcadd_card.append(SPC_ID)
        dynamic_check_text = bdf_template.replace_spcadd_card_in_text(
            dynamic_check_text, spcadd_card
        )

    dynamic_check_text = dynamic_check_text.replace("INCLUDE '../", "INCLUDE '../../")
    dynamic_check_text = dynamic_check_text.replace("INCLUDE './", "INCLUDE '../")

    with open(filename, "w") as f:
        f.write(dynamic_check_text)


def launch_dynamic_check(
    df_element_grids,
    BDF_FILE_TEMPLATE,
    f06_with_mass_data,
    CoG_grid_id,
    SPC_ID,
    spcadd_card,
    dynamic_check_filename="./DFEM_Validation/Dynamic_Check.dat",
    wait_completion=False,
):
    # nastran launcher filename
    dynamic_check_launcher = Path(
        Path(dynamic_check_filename).parent
        / Path(Path(dynamic_check_filename).stem.lower() + "_launcher.sh")
    )

    with open(BDF_FILE_TEMPLATE, "r") as f:
        bdf_file_template_text = "".join(f.readlines())
    create_bdf(
        text=bdf_file_template_text,
        CoG_grid_id=CoG_grid_id,
        CoG_grid_card=f06_with_mass_data["mass_data"]["cog_grid_card"],
        SPC_ID=SPC_ID,
        spcadd_card=spcadd_card,
        filename=dynamic_check_filename,
    )

    # create nastran launcher for the above input
    nf.create_nastran_launcher(
        filemask=str(Path(dynamic_check_filename)), filename=dynamic_check_launcher
    )

    # nastran is launched automatically on stress4 server
    if platform == "linux":
        nf.launch_nastran(dynamic_check_launcher, wait=wait_completion)
