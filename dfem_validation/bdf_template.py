# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 14:10:50 2022

@author: DONIK94
"""


def add_title(title, text, mark="<<TITLE>>"):
    """
    Replaces mark with given title
    """
    output = f"TITLE = {title}"
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def add_SPC_ID(SPC_ID, text, mark="<<SPC>>"):
    """
    Replaces mark with given spc id
    """
    output = f"SPC = {SPC_ID}"
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def add_result_request(
    text,
    set_id="ALL",
    disp=False,
    disp_settings="PLOT",
    spcforce=False,
    spcforce_settings="PRINT",
    mpcforce=False,
    mpcforce_settings="PLOT",
    stress=False,
    stress_settings="CENTER,PLOT",
    vector=False,
    vector_settings="PLOT",
    ese=False,
    ese_settings="PLOT",
    mark="<<RESULTS>>",
):
    """
    Replaces mark with givenresult settings
    """
    results = []
    if disp:
        results.append(f"DISP({disp_settings}) = {set_id}\n")
    if spcforce:
        results.append(f"SPCFORCE({spcforce_settings}) = {set_id}\n")
    if mpcforce:
        results.append(f"MPCFORCE({mpcforce_settings}) = {set_id}\n")
    if stress:
        results.append(f"STRESS({stress_settings}) = {set_id}\n")
    if vector:
        results.append(f"VECTOR({vector_settings}) = {set_id}\n")
    if ese:
        results.append(f"ESE({ese_settings}) = {set_id}\n")
    output = "".join(results)
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def replace_by_mark(mark, text, insertion):
    """
    Replaces mark with given insertion text
    """
    if text.find(mark) > 0:
        return text.replace(mark, insertion)
    else:
        print(f"Mark {mark} is not found")


def add_spc_constrain(text, SPC_ID, grid_id, mark="<<SPC_BULKDATA>>"):
    """
    Replaces spc mark in bulkdata section with corresponding spc
    """
    output = f"""
$_______________________________________________________________________
$
$                       B O U N D A R Y
$_______________________________________________________________________
$      ><      ><      ><      ><      ><      ><      ><      ><      >
SPC1    {int(SPC_ID):8d}  123456{int(grid_id):8d}
"""
    if mark in text:
        return text.replace(mark, output)
    else:
        return text


def replace_spcadd_card_in_text(text, spcadd_card):
    lines = text.split("\n")
    for line_num in range(len(lines)):
        line = lines[line_num]
        if line.startswith("SPCADD"):
            lines[line_num] = "".join(["%-8s" % member for member in spcadd_card[:9]])
            if len(spcadd_card) > 9:
                lines[line_num + 1] = "        " + "".join(
                    ["%-8s" % member for member in spcadd_card[9:17]]
                )
                break
    return "\n".join(lines)
