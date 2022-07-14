# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 14:05:47 2022

@author: DONIK94
"""
import pandas as pd
from . import bdf_template
from pathlib import Path
from . import nastran_functions as nf
from sys import platform


def add_subcases(text, mark="<<SUBCASES>>"):
    """
    Replaces subcases mark with 3 gravity subcases
    """
    output = f"""
SUBCASE=1
    SUBTITLE=Gravity_-1GX
    LABEL=Gravity_-1GX
    LOAD=99999991

SUBCASE=2
    SUBTITLE=Gravity_-1GY
    LABEL=Gravity_-1GY
    LOAD=99999992

SUBCASE=3
    SUBTITLE=Gravity_-1GZ
    LABEL=Gravity_-1GZ
    LOAD=99999993  
    """
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def add_bulk_loads(text, mark="<<LOADS_BULKDATA>>"):
    """
    Replaces loads mark in bulkdata section with 3 gravity loads
    """
    output = f"""
$_______________________________________________________________________
$
$                       L O A D S
$_______________________________________________________________________
$ Gravity
$      ><      ><      ><      ><      ><      ><      ><      ><      >
GRAV    99999991          10000.     -1.      0.      0.
GRAV    99999992          10000.      0.     -1.      0.
GRAV    99999993          10000.      0.      0.     -1. 
    """
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def add_bc(text, spc_card, mark="<<SPC_BULKDATA>>"):
    """
    Replaces spc mark in bulkdata section with 3 gravity spc from input
    """
    output = f"""
$_______________________________________________________________________
$
$                       B O U N D A R Y
$_______________________________________________________________________
"""
    output += spc_card
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def get_3_isostatic_spc_nodes(df_element_grids):
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
        .query("relY >= 0.99*relY.max()")
        .query("abs(relZ) == relZ.abs().min()")
        .iloc[0]
    )
    df_extreme = df_extreme.append(
        df_element_grids.query("relX >= 0.9*relX.max()")
        .query("relY <= 0.99*relY.min()")
        .query("abs(relZ) == relZ.abs().min()")
        .iloc[0]
    )

    df_extreme = df_extreme.append(
        df_element_grids.query("relX <= 0.9*relX.min()")
        .query("relZ <= 0.99*relZ.min()")
        .query("abs(relY) == relY.abs().min()")
        .iloc[0]
    )

    nodes = df_extreme["n_1"].to_list()
    return df_extreme, nodes


def get_isostatic_spc_card(df_element_grids, SPC_ID):
    df_gravity_nodes, gravity_check_iso_spc_nodes = get_3_isostatic_spc_nodes(
        df_element_grids
    )
    df_gravity_nodes.sort_values(by=["X"], inplace=True)
    node1 = df_gravity_nodes["n_1"].iloc[0]
    node2 = df_gravity_nodes["n_1"].iloc[1]
    node3 = df_gravity_nodes["n_1"].iloc[2]
    card = f"""
$ Isostatic mounting
$      ><  ID  >< NODE >< DOF  ><      >
SPC     {SPC_ID:8d}{node1:8d}      23      0.
SPC     {SPC_ID:8d}{node2:8d}      13      0.
SPC     {SPC_ID:8d}{node3:8d}      13      0.
"""
    return card


def create_bdf(
    text, df_element_grids, SPC_ID, spcadd_card=[], filename="Gravity_check.dat"
):
    """
    Creates bulkdata file for gravity check
    """

    if spcadd_card == []:
        SPC_ID_global = SPC_ID
    else:
        SPC_ID_global = spcadd_card[1]

    gravity_check_text = bdf_template.add_title(title="Gravity Check", text=text)
    gravity_check_text = bdf_template.add_SPC_ID(
        SPC_ID=SPC_ID_global, text=gravity_check_text
    )
    gravity_check_text = bdf_template.add_result_request(
        text=gravity_check_text, disp=True, spcforce=True, mpcforce=True, stress=True
    )
    gravity_check_text = add_subcases(text=gravity_check_text)
    gravity_check_text = add_bulk_loads(text=gravity_check_text)

    spc_card = get_isostatic_spc_card(df_element_grids, SPC_ID=SPC_ID)
    gravity_check_text = add_bc(text=gravity_check_text, spc_card=spc_card)

    if spcadd_card != []:
        spcadd_card.append(SPC_ID)
        gravity_check_text = bdf_template.replace_spcadd_card_in_text(
            gravity_check_text, spcadd_card
        )

    gravity_check_text = gravity_check_text.replace("INCLUDE '../", "INCLUDE '../../")
    gravity_check_text = gravity_check_text.replace("INCLUDE './", "INCLUDE '../")

    with open(filename, "w") as f:
        f.write(gravity_check_text)


def launch_gravity_check(
    df_element_grids,
    BDF_FILE_TEMPLATE,
    SPC_ID,
    spcadd_card,
    overwrite,
    gravity_check_filename="./DFEM_Validation/Gravity_Check.dat",
    wait_completion=True,
):

    # nastran launcher filename
    gravity_check_launcher = Path(
        Path(gravity_check_filename).parent
        / Path(Path(gravity_check_filename).stem.lower() + "_launcher.sh")
    )

    # read nastran template
    with open(BDF_FILE_TEMPLATE, "r") as f:
        bdf_file_template_text = "".join(f.readlines())

    # write gravity check Nastran input
    create_bdf(
        text=bdf_file_template_text,
        df_element_grids=df_element_grids,
        SPC_ID=SPC_ID,
        spcadd_card=spcadd_card,
        filename=gravity_check_filename,
    )

    # create nastran launcher for the above input
    nf.create_nastran_launcher(
        filemask=str(Path(gravity_check_filename)), filename=gravity_check_launcher
    )

    # check if f06 file from previous calcualtion exists
    if not overwrite:
        pass

    # if not, nastran is launched automatically on stress4 server
    elif platform == "linux":
        nf.launch_nastran(gravity_check_launcher, wait=wait_completion)
