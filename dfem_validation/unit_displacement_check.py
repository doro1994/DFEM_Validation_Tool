# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 14:12:10 2022

@author: DONIK94
"""
from . import bdf_template
from pathlib import Path
import pandas as pd
from . import nastran_functions as nf
from sys import platform
import numpy as np


def insert_to_nth_pos(text, line_to_insert, pos):
    """
    Inserts substring to specific position
    """
    return f"{text[:pos]}{line_to_insert}{text[pos:]}"


def insert_to_every_nth_pos(text, line_to_insert, pos):
    """
    Inserts substring to every n_th position
    """
    n = 1
    output = text
    while pos * n < len(output):
        output = insert_to_nth_pos(output, line_to_insert, pos * n)
        n += 1
    return output


def add_subcases(text, mark="<<SUBCASES>>"):
    """
    Replaces subcases mark with 6 unit displacement subcases
    """
    output = f"""
SUBCASE 1 
    SUBTITLE=Unit Trans X 
    LABEL=Unit Trans X 
    LOAD = 99999991
    
SUBCASE 2 
    SUBTITLE=Unit Trans Y 
    LABEL=Unit Trans Y
    LOAD = 99999992
    
SUBCASE 3 
    SUBTITLE=Unit Trans Z 
    LABEL=Unit Trans Z
    LOAD = 99999993
    
SUBCASE 4 
    SUBTITLE=Unit Rot X 
    LABEL=Unit Rot X 
    LOAD = 99999994
    
SUBCASE 5 
    SUBTITLE=Unit Rot Y
    LABEL=Unit Rot Y
    LOAD = 99999995
    
SUBCASE 6 
    SUBTITLE=Unit Rot Z
    LABEL=Unit Rot Z
    LOAD = 99999996
"""
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def create_RBE2(dependent_node_list, central_node, RBE_id):
    """
    Creates RBE2 between central node and given dependent nodes
    """
    dep_nodes = f""
    for node in dependent_node_list:
        dep_nodes = dep_nodes + f"{int(node):8d}"
    card = f"RBE2    {int(RBE_id):8d}{int(central_node):8d}{123456:8d}" + dep_nodes
    return insert_to_every_nth_pos(card, "+\n+       ", 72)


def add_load_introduction(
    text,
    CoG_grid_id,
    CoG_grid_card,
    dependent_node_list,
    RBE_id,
    mark="<<LOADS_BULKDATA>>",
):
    """
    Replaces loads mark in bulkdata section with corresponding unit check loads
    """
    output = f"""
$_______________________________________________________________________
$
$                       L O A D  I N T R O D U C T I O N
$_______________________________________________________________________
"""
    output = output + CoG_grid_card + "\n"
    output = output + create_RBE2(
        central_node=CoG_grid_id, dependent_node_list=dependent_node_list, RBE_id=RBE_id
    )
    output += f"""
$_______________________________________________________________________
$
$                       L O A D S
$_______________________________________________________________________
$      ><      ><      ><      ><      ><      ><      ><      ><      >
SPCD    99999991{int(CoG_grid_id):8d}       1      1.	
SPCD    99999992{int(CoG_grid_id):8d}       2      1.
SPCD    99999993{int(CoG_grid_id):8d}       3      1.
SPCD    99999994{int(CoG_grid_id):8d}       4      1.
SPCD    99999995{int(CoG_grid_id):8d}       5      1.
SPCD    99999996{int(CoG_grid_id):8d}       6      1.
"""

    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def get_4_most_distant_nodes(df_element_grids, f06_with_mass_data):
    #    df_element_grids = get_dfem_elements_df(bdf_file)

    df_element_grids["cogX"] = float(f06_with_mass_data["mass_data"]["ydir_Cog_x"])
    df_element_grids["cogY"] = float(f06_with_mass_data["mass_data"]["zdir_Cog_y"])
    df_element_grids["cogZ"] = float(f06_with_mass_data["mass_data"]["xdir_Cog_z"])

    df_element_grids["dist"] = np.sqrt(
        (np.abs(df_element_grids.X - df_element_grids.cogX)) ** 2
        + (np.abs(df_element_grids.Y - df_element_grids.cogY)) ** 2
        + (np.abs(df_element_grids.Z - df_element_grids.cogZ)) ** 2
    )

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
        df_element_grids.query("relX >= 0.75*relX.max()")
        .query("relZ >= 0.75*relZ.max()")
        .query("dist == dist.max()")
        .iloc[0]
    )
    df_extreme = df_extreme.append(
        df_element_grids.query("relX >= 0.75*relX.max()")
        .query("relZ <= 0.75*relZ.min()")
        .query("dist == dist.max()")
        .iloc[0]
    )

    df_extreme = df_extreme.append(
        df_element_grids.query("relX <= 0.75*relX.min()")
        .query("relY >= 0.75*relY.max()")
        .query("dist == dist.max()")
        .iloc[0]
    )
    df_extreme = df_extreme.append(
        df_element_grids.query("relX <= 0.75*relX.min()")
        .query("relY <= 0.75*relY.min()")
        .query("dist == dist.max()")
        .iloc[0]
    )
    """
    df_extreme = df_extreme.append(df_element_grids.query(
                                                        "relX >= 0.9*relX.max()").query(
                                                        "relZ >= 0.99*relZ.max()").query(
                                                        "abs(relY) == relY.abs().min()").iloc[0])
    
    df_extreme = df_extreme.append(df_element_grids.query(
                                                        "relX >= 0.9*relX.max()").query(
                                                        "relZ <= 0.99*relZ.min()").query(
                                                        "abs(relY) == relY.abs().min()").iloc[0])   
    
    df_extreme = df_extreme.append(df_element_grids.query(
                                                        "relX <= 0.9*relX.min()").query(
                                                        "relY >= 0.99*relY.max()").query(
                                                        "abs(relZ) == relZ.abs().min()").iloc[0])
    df_extreme = df_extreme.append(df_element_grids.query(
                                                        "relX <= 0.9*relX.min()").query(
                                                        "relY <= 0.99*relY.min()").query(
                                                        "abs(relZ) == relZ.abs().min()").iloc[0])  
    """
    nodes = df_extreme["n_1"].to_list()
    return df_extreme, nodes


def create_bdf(
    text,
    CoG_grid_card,
    SPC_ID,
    dependent_node_list,
    RBE_id,
    CoG_grid_id,
    spcadd_card,
    filename="Unit_check.dat",
):
    """
    Creates bulkdata file for unit displacement check
    """

    if spcadd_card == []:
        SPC_ID_global = SPC_ID
    else:
        SPC_ID_global = spcadd_card[1]

    unit_check_text = bdf_template.add_title(title="Unit Check", text=text)
    unit_check_text = bdf_template.add_SPC_ID(
        SPC_ID=SPC_ID_global, text=unit_check_text
    )
    unit_check_text = bdf_template.add_result_request(
        text=unit_check_text, disp=True, spcforce=True, mpcforce=True, stress=True
    )
    unit_check_text = add_subcases(text=unit_check_text)
    unit_check_text = add_load_introduction(
        text=unit_check_text,
        CoG_grid_id=CoG_grid_id,
        CoG_grid_card=CoG_grid_card,
        RBE_id=RBE_id,
        dependent_node_list=dependent_node_list,
    )
    if spcadd_card != []:
        spcadd_card.append(SPC_ID)
        unit_check_text = bdf_template.replace_spcadd_card_in_text(
            unit_check_text, spcadd_card
        )

    unit_check_text = bdf_template.add_spc_constrain(
        text=unit_check_text, SPC_ID=SPC_ID, grid_id=CoG_grid_id
    )

    unit_check_text = unit_check_text.replace("INCLUDE '../", "INCLUDE '../../")
    unit_check_text = unit_check_text.replace("INCLUDE './", "INCLUDE '../")
    with open(filename, "w") as f:
        f.write(unit_check_text)


def launch_unit_check(
    df_element_grids,
    BDF_FILE_TEMPLATE,
    f06_with_mass_data,
    CoG_grid_id,
    SPC_ID,
    RBE_id,
    spcadd_card,
    unit_check_filename="./DFEM_Validation/Unit_Displacement_Check.dat",
    wait_completion=False,
):

    # nastran launcher filename
    unit_check_launcher = Path(
        Path(unit_check_filename).parent
        / Path(Path(unit_check_filename).stem.lower() + "_launcher.sh")
    )

    # read nastran template
    with open(BDF_FILE_TEMPLATE, "r") as f:
        bdf_file_template_text = "".join(f.readlines())

    # get RBE2 nodes
    _, unit_check_rbe2_nodes = get_4_most_distant_nodes(
        df_element_grids, f06_with_mass_data=f06_with_mass_data
    )

    # create unti check file
    create_bdf(
        text=bdf_file_template_text,
        CoG_grid_card=f06_with_mass_data["mass_data"]["cog_grid_card"],
        SPC_ID=SPC_ID,
        dependent_node_list=unit_check_rbe2_nodes,
        CoG_grid_id=CoG_grid_id,
        RBE_id=RBE_id,
        spcadd_card=spcadd_card,
        filename=unit_check_filename,
    )

    # create nastran launcher for the above input
    nf.create_nastran_launcher(
        filemask=str(Path(unit_check_filename)), filename=unit_check_launcher
    )

    # nastran is launched automatically on stress4 server
    if platform == "linux":
        nf.launch_nastran(unit_check_launcher, wait=wait_completion)
