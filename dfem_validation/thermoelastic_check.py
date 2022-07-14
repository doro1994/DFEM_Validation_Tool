# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 14:15:48 2022

@author: DONIK94
"""

from . import bdf_template
from pathlib import Path
from . import nastran_functions as nf
from sys import platform
import pandas as pd


def add_subcases(text, mark="<<SUBCASES>>"):
    output = f"""
TEMP(INIT) = 1
SUBCASE=1
    SUBTITLE=Temperature dT +100K
    LABEL=Temperature dT +100K
    TEMP(LOAD)=2
"""
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def add_load_introduction(text, mark="<<LOADS_BULKDATA>>"):
    output = f"""
$_______________________________________________________________________
$
$                       L O A D S
$_______________________________________________________________________
$      ><      ><      ><      ><      ><      ><      ><      ><      >
TEMPD   1            20.
TEMPD   2           120. 
"""
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


def get_1_clamped_node(df_element_grids):
    df_element_grids["relX"] = (
        df_element_grids.X - (df_element_grids.X.max() + df_element_grids.X.min()) / 2
    )
    df_element_grids["relY"] = (
        df_element_grids.Y - (df_element_grids.Y.max() + df_element_grids.Y.min()) / 2
    )
    df_element_grids["relZ"] = (
        df_element_grids.Z - (df_element_grids.Z.max() + df_element_grids.Z.min()) / 2
    )

    df_extreme = pd.DataFrame(columns=df_element_grids.columns)
    df_extreme = df_extreme.append(
        df_element_grids.query("relX >= 0.9*relX.max()")
        .query("relZ >= 0.99*relZ.max()")
        .query("abs(relY) == relY.abs().min()")
        .iloc[0]
    )

    node = df_extreme["n_1"].iloc[0]
    return df_extreme, node


def create_bdf(
    text, clamped_grid, SPC_ID, spcadd_card, filename="Thermoelastic_check.dat"
):

    if spcadd_card == []:
        SPC_ID_global = SPC_ID
    else:
        SPC_ID_global = spcadd_card[1]

    thermoelastic_check_text = bdf_template.add_title(
        title="Thermoelastic Check", text=text
    )
    MAT_TECO_LINE = "MODEL_CHECK MAT_TECO=2.3e-5 MAT_TEIJ=0.0\n"
    thermoelastic_check_text = thermoelastic_check_text.replace(
        "SOL 101\n", "SOL 101\n" + MAT_TECO_LINE
    )
    thermoelastic_check_text = bdf_template.add_SPC_ID(
        SPC_ID=SPC_ID_global, text=thermoelastic_check_text
    )
    thermoelastic_check_text = bdf_template.add_result_request(
        text=thermoelastic_check_text,
        disp=True,
        spcforce=True,
        spcforce_settings="PRINT",
        mpcforce=True,
        stress=True,
    )
    thermoelastic_check_text = add_subcases(text=thermoelastic_check_text)
    thermoelastic_check_text = add_load_introduction(text=thermoelastic_check_text)
    thermoelastic_check_text = bdf_template.add_spc_constrain(
        text=thermoelastic_check_text, SPC_ID=SPC_ID, grid_id=clamped_grid
    )

    if spcadd_card != []:
        spcadd_card.append(SPC_ID)
        thermoelastic_check_text = bdf_template.replace_spcadd_card_in_text(
            thermoelastic_check_text, spcadd_card
        )

    thermoelastic_check_text = thermoelastic_check_text.replace(
        "INCLUDE '../", "INCLUDE '../../"
    )
    thermoelastic_check_text = thermoelastic_check_text.replace(
        "INCLUDE './", "INCLUDE '../"
    )
    with open(filename, "w") as f:
        f.write(thermoelastic_check_text)


def launch_thermoelastic_check(
    df_element_grids,
    BDF_FILE_TEMPLATE,
    SPC_ID,
    spcadd_card,
    thermoelastic_check_filename="./DFEM_Validation/Thermoelastic_Check.dat",
    wait_completion=False,
):
    # nastran launcher filename
    thermoelastic_check_launcher = Path(
        Path(thermoelastic_check_filename).parent
        / Path(Path(thermoelastic_check_filename).stem.lower() + "_launcher.sh")
    )
    # get clamped grid id
    _, clamped_grid = get_1_clamped_node(df_element_grids)

    with open(BDF_FILE_TEMPLATE, "r") as f:
        bdf_file_template_text = "".join(f.readlines())
        create_bdf(
            text=bdf_file_template_text,
            clamped_grid=clamped_grid,
            SPC_ID=SPC_ID,
            spcadd_card=spcadd_card,
            filename=thermoelastic_check_filename,
        )

    # create nastran launcher for the above input
    nf.create_nastran_launcher(
        filemask=str(Path(thermoelastic_check_filename)),
        filename=thermoelastic_check_launcher,
    )

    # nastran is launched automatically on stress4 server
    if platform == "linux":
        nf.launch_nastran(thermoelastic_check_launcher, wait=wait_completion)
