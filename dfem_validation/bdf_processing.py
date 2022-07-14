# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 14:17:23 2022

@author: DONIK94
"""
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm
import os
import pandas as pd
from textwrap import wrap


def get_list_GRID(bdf_file):
    grid_list = []
    CORD2R_added_shift = get_ref_point_coord(bdf_file)
    line_count = -1
    with open(bdf_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            line_count += 1
            if line.startswith("GRID    "):
                grid_dict = dict.fromkeys(["n_1", "X", "Y", "Z"])
                grid_dict["n_1"] = int(line[8:16])
                grid_dict["cs"] = line[16:24]
                grid_dict["X"] = convert_to_float(line[24:32])
                grid_dict["Y"] = convert_to_float(line[32:40])
                grid_dict["Z"] = convert_to_float(line[40:48])

                if grid_dict["cs"] != "        ":
                    grid_dict["X"] += CORD2R_added_shift[int(line[16:24])][0]
                    grid_dict["Y"] += CORD2R_added_shift[int(line[16:24])][1]
                    grid_dict["Z"] += CORD2R_added_shift[int(line[16:24])][2]
                grid_list.append(grid_dict)

            elif line.startswith("GRID*   "):
                grid_dict = dict.fromkeys(["n_1", "X", "Y", "Z"])
                grid_dict["n_1"] = int(line[16:24])
                grid_dict["cs"] = line[24:40]
                grid_dict["X"] = convert_to_float(line[40:56])
                grid_dict["Y"] = convert_to_float(line[56:72])
                grid_dict["Z"] = convert_to_float(lines[line_count + 1][8:24])
                if grid_dict["cs"] != "        ":
                    grid_dict["X"] += CORD2R_added_shift[int(line[24:40])][0]
                    grid_dict["Y"] += CORD2R_added_shift[int(line[24:40])][1]
                    grid_dict["Z"] += CORD2R_added_shift[int(line[24:40])][2]
                grid_list.append(grid_dict)
    return grid_list


def get_list_CQUAD(bdf_file):
    with open(bdf_file, "r") as f:
        cquad_list = []
        for line in f.readlines():
            if line.startswith("CQUAD"):
                cquad_dict = dict.fromkeys(
                    ["Element", "prop", "n_1", "n_2", "n_3", "n_4"]
                )
                # CQUAD[i] = row[0:5]
                cquad_dict["Element"] = int(line[8:16])
                cquad_dict["prop"] = line[16:24]
                cquad_dict["n_1"] = int(line[24:32])
                cquad_dict["n_2"] = int(line[32:40])
                cquad_dict["n_3"] = int(line[40:48])
                cquad_dict["n_4"] = int(line[48:56])
                cquad_list.append(cquad_dict)
    return cquad_list


def get_list_CTRIA(bdf_file):
    with open(bdf_file, "r") as f:
        ctria_list = []
        for line in f.readlines():
            if "CTRIA" in line:
                ctria_dict = dict.fromkeys(["Element", "prop", "n_1", "n_2", "n_3"])
                ctria_dict["Element"] = int(line[8:16])
                ctria_dict["prop"] = line[16:24]
                ctria_dict["n_1"] = int(line[24:32])
                ctria_dict["n_2"] = int(line[32:40])
                ctria_dict["n_3"] = int(line[40:48])
                ctria_list.append(ctria_dict)
    return ctria_list


def id_is_used(id_to_check, bdf_file):
    with open(bdf_file, "r") as f:

        for line in f:
            if int(line[8:16]) == int(id_to_check):
                return True
    return False


def get_bdf_id_list(bdf_file):
    output = []
    with open(bdf_file, "r") as f:
        for line in f:
            if not line.startswith("$") and line[8:16].strip().isdigit():
                output.append(int(line[8:16]))
    return output


def select_free_id(existing_ids, starting_id, ascending=True):
    current_id = starting_id
    id_found = False
    while id_found == False:
        if current_id not in existing_ids:
            id_found = True
        else:
            if ascending:
                current_id += 1
            else:
                current_id -= 1
    return current_id


def load_CS(BDF_file):
    CORD2R_dict = defaultdict()
    empt = "        "
    CORD2R_dict[0] = [empt, empt, empt, empt, empt, empt, empt, empt, empt, empt]
    with open(BDF_file, "r") as f:
        read_next_line = False
        for line in f:
            if line.startswith("CORD2R "):
                CID = int(line[8:16])
                if line[16:24] == "        ":
                    RID = 0
                else:
                    RID = int(line[16:24])
                A1 = line[24:32]
                A2 = line[32:40]
                A3 = line[40:48]
                B1 = line[48:56]
                B2 = line[56:64]
                B3 = line[64:72]
                read_next_line = True
            if "     " in line and read_next_line == True:
                C1 = line[8:16]
                C2 = line[16:24]
                C3 = line[24:32]
                CORD2R_dict[CID] = [RID, A1, A2, A3, B1, B2, B3, C1, C2, C3]
                read_next_line = False
    return CORD2R_dict


def get_real_coord(node_cs, BDF_file, x=0, y=0, z=0):

    CORD2R_dict = load_CS(BDF_file)

    if node_cs != 0:
        x += convert_to_float(CORD2R_dict[node_cs][1])
        y += convert_to_float(CORD2R_dict[node_cs][2])
        z += convert_to_float(CORD2R_dict[node_cs][3])
        cord2r_rid = CORD2R_dict[node_cs][0]
        if cord2r_rid != 0:
            return get_real_coord(cord2r_rid, BDF_file, x, y, z)
    return [x, y, z]


def get_ref_point_coord(BDF_file):

    CORD2R_dict = load_CS(BDF_file)
    CORD2R_added_shift = defaultdict()

    for coord in CORD2R_dict.keys():

        if coord != 0:
            rid = CORD2R_dict[coord][0]
            a1 = convert_to_float(CORD2R_dict[coord][1])
            a2 = convert_to_float(CORD2R_dict[coord][2])
            a3 = convert_to_float(CORD2R_dict[coord][3])

            if rid == 0:
                CORD2R_added_shift[coord] = [a1, a2, a3]
            else:
                real_base_coordinates = get_real_coord(rid, BDF_file)
                x = a1 + real_base_coordinates[0]
                y = a2 + real_base_coordinates[1]
                z = a3 + real_base_coordinates[2]
                CORD2R_added_shift[coord] = [x, y, z]

    return CORD2R_added_shift


def convert_to_float(text):
    text = text.strip()
    try:
        if len(text.split(" ")) > 1:
            value = float(text.split(" ")[1])
        else:
            value = float(text.strip())
        return value
    except:
        return 0


def get_dfem_elements_df(bdf_file):
    df_dfem_grids = pd.DataFrame(data=get_list_GRID(bdf_file))
    df_dfem_cquads = pd.DataFrame(data=get_list_CQUAD(bdf_file))
    df_dfem_ctria = pd.DataFrame(data=get_list_CTRIA(bdf_file))
    df_dfem_elements = pd.concat(
        [
            df_dfem_cquads[["Element", "prop", "n_1"]],
            df_dfem_ctria[["Element", "prop", "n_1"]],
        ]
    )
    df_element_grids = df_dfem_grids.merge(df_dfem_elements, on="n_1", how="inner")
    bad_grids = []
    with open(bdf_file, "r") as f:
        for line in f:
            if line.startswith("RBE") or line.startswith("MPC") or line.startswith("+"):
                line_list = wrap(line, width=8, drop_whitespace=False)
                for item in line_list[2:]:
                    if item.strip().isdigit():
                        bad_grids.append(int(item))
    bad_grids = set(bad_grids)
    df_element_grids = df_element_grids[~df_element_grids["n_1"].isin(bad_grids)]
    return df_element_grids


def extract_id_from_card(card, card_type="GRID"):
    gls = card.find(card_type)
    if f"{card_type}    " in card:
        item_id = int(card[gls + 8 : gls + 16].strip())
    elif f"{card_type}*   " in card:
        item_id = int(card[gls + 8 : gls + 24].strip())
    return item_id


# def add_to_spcadd_if_existsing(spc_to_add, text):
def get_spcadd_card(bdf_file):
    with open(bdf_file, "r") as f:
        lines = f.readlines()
    spcadd_card = []
    for line_num in range(len(lines)):
        if lines[line_num].startswith("SPCADD"):
            spcadd_card = wrap(lines[line_num], 8)
            if (
                lines[line_num + 1].startswith("        ")
                or "*" in lines[line_num + 1][:8]
            ):
                spcadd_card += wrap(lines[line_num + 1], 8)
    return spcadd_card
