# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 14:16:19 2022

@author: DONIK94
"""

from collections import defaultdict
from pathlib import Path


def get_mass_data_from_gpwg(output_from_gpwg, CoG_grid_id):
    line_number = -1
    mass_data = defaultdict()
    for line in output_from_gpwg:
        line_number += 1
        if (
            "MASS AXIS SYSTEM (S)     MASS              X-C.G.        Y-C.G.        Z-C.G."
            in line
        ):
            mass_data["raw_lines"] = output_from_gpwg[line_number : line_number + 4]
            mass_data["mass_x"] = mass_data["raw_lines"][1].split()[1]
            mass_data["mass_y"] = mass_data["raw_lines"][2].split()[1]
            mass_data["mass_z"] = mass_data["raw_lines"][3].split()[1]
            mass_data["xdir_Cog_x"] = mass_data["raw_lines"][1].split()[2]
            mass_data["xdir_Cog_y"] = mass_data["raw_lines"][1].split()[3]
            mass_data["xdir_Cog_z"] = mass_data["raw_lines"][1].split()[4]
            mass_data["ydir_Cog_x"] = mass_data["raw_lines"][2].split()[2]
            mass_data["ydir_Cog_y"] = mass_data["raw_lines"][2].split()[3]
            mass_data["zdir_Cog_z"] = mass_data["raw_lines"][2].split()[4]
            mass_data["zdir_Cog_x"] = mass_data["raw_lines"][3].split()[2]
            mass_data["zdir_Cog_y"] = mass_data["raw_lines"][3].split()[3]
            mass_data["zdir_Cog_z"] = mass_data["raw_lines"][3].split()[4]
            mass_data["cog_grid_card"] = (
                f"$ CENTER OF GRAVITY GRID POINT\n"
                f"$------><------><------><------><------><------><------><------><------>\n"
                f"GRID*           {CoG_grid_id:8d}                {float(mass_data['ydir_Cog_x']):16f}"
                f"{float(mass_data['zdir_Cog_y']):16f}*\n*       {float(mass_data['xdir_Cog_z']):16f}\n"
            )

            break

    if not (mass_data["mass_x"] == mass_data["mass_y"] == mass_data["mass_z"]):
        print(f"Masses in different directions are not the same!")
        print("\n".join(mass_data["raw_lines"]))
    return mass_data


def oload_spcforce_processing(lines_dict):
    output_dict = defaultdict(dict)
    for subcase in lines_dict.keys():
        for line in lines_dict[subcase]:
            line1 = line.replace("----", "0.0")
            output_dict[subcase]["lines"] = lines_dict[subcase]

            if line1.split()[2] == "FX":
                T1 = float(line1.split()[3])
                T2 = float(line1.split()[4])
                T3 = float(line1.split()[5])
                R1 = float(line1.split()[6])
                R2 = float(line1.split()[7])
                R3 = float(line1.split()[8])
                output_dict[subcase]["FX"] = [T1, T2, T3, R1, R2, R3]
            else:
                load_type = line1.strip().split()[0]
                T1 = float(line1.split()[1])
                T2 = float(line1.split()[2])
                T3 = float(line1.split()[3])
                R1 = float(line1.split()[4])
                R2 = float(line1.split()[5])
                R3 = float(line1.split()[6])
                output_dict[subcase][load_type] = [T1, T2, T3, R1, R2, R3]
    return output_dict


def maximum_values_processing(lines_dict):
    output_dict = defaultdict()
    #    if len(line.strip().split()) == 7:
    for subcase in lines_dict.keys():
        line = lines_dict[subcase]
        T1 = float(line.strip().split()[2])
        T2 = float(line.strip().split()[3])
        T3 = float(line.strip().split()[4])
        R1 = float(line.strip().split()[5])
        R2 = float(line.strip().split()[6])
        R3 = float(line.strip().split()[7])
        output_dict[subcase] = [T1, T2, T3, R1, R2, R3]
    return output_dict


def compare_oload_spcforce(oload, spcforce, tol=1):
    for subcase in oload.keys():
        abs_difference_in_totals = [
            n2 + n1
            for n1, n2 in zip(oload[subcase]["TOTALS"], spcforce[subcase]["TOTALS"])
        ]
        rel_difference_in_totals = [
            (n2 + n1) / (abs(n1) + 1e-09)
            for n1, n2 in zip(oload[subcase]["TOTALS"], spcforce[subcase]["TOTALS"])
        ]
        for abs_diff, rel_diff in zip(
            abs_difference_in_totals, rel_difference_in_totals
        ):
            if abs_diff > tol and rel_diff > tol:
                print(f"Check OLOAD - SPCFORCE balance for subcase {subcase}")
                print(
                    f"Both absolute or relative diference in TOTALS are greater than {tol}"
                )


def create_f06_result_dict(filename, CoG_grid_id):
    with open(Path(filename), "r") as f:
        f06_lines = f.readlines()
        line_number = -1

        f06_result_dict = defaultdict(dict)

        for line in f06_lines:
            line_number += 1

            if "FATAL" in line:
                print(f"FATAL ERROR in the file {filename}")
                exit

            if (
                "O U T P U T   F R O M   G R I D   P O I N T   W E I G H T   G E N E R A T O R"
                in line
            ):
                output_from_gpwg = f06_lines[line_number : line_number + 30]
                f06_result_dict["output_from_gpwg"]["lines"] = output_from_gpwg
                f06_result_dict["mass_data"] = get_mass_data_from_gpwg(
                    output_from_gpwg, CoG_grid_id=CoG_grid_id
                )

            if "MAXIMUM MATRIX-TO-FACTOR-DIAGONAL RATIO OF" in line:
                matrix_to_factor_diag_ratio = float(line.split()[-1])
                if matrix_to_factor_diag_ratio > 1e7:
                    print(
                        f"WARNING! Matrix-to-factor-diagonal ratio is {matrix_to_factor_diag_ratio} which is greater than 10E7"
                    )
                    break
                else:
                    f06_result_dict["matrix_to_factor_diag_ratio"][
                        "value"
                    ] = matrix_to_factor_diag_ratio
                    f06_result_dict["matrix_to_factor_diag_ratio"]["line"] = line
                    # since external work always goes after OLOAD resultant
                    number_of_subcases = len(
                        f06_result_dict["OLOAD    RESULTANT"]["lines"].keys()
                    )
                    f06_result_dict["EXTERNAL WORK"]["lines"] = f06_lines[
                        line_number - 1 : line_number + 4 + number_of_subcases
                    ]

            result_types = [
                "OLOAD    RESULTANT",
                "SPCFORCE RESULTANT",
                "MAXIMUM  SPCFORCES",
                "MAXIMUM  DISPLACEMENTS",
                "MAXIMUM  APPLIED LOADS",
                "MPCFORCE RESULTANT",
                "MAXIMUM  MPCFORCES",
                "R E A L   E I G E N V A L U E S",
            ]

            for result_type in result_types:
                if result_type in line and result_type not in f06_result_dict.keys():
                    for res in f06_result_dict.keys():
                        f06_result_dict[res]["started"] = False
                    f06_result_dict[result_type]["started"] = True
                    f06_result_dict[result_type]["lines"] = defaultdict()
                    f06_result_dict[result_type]["header"] = f06_lines[
                        line_number : line_number + 3
                    ]

                if (
                    "RESULTANT" in result_type
                    and result_type in f06_result_dict.keys()
                    and f06_result_dict[result_type]["started"]
                    and line.startswith("0")
                    and len(line.split()) > 3
                    and line.split()[2] == "FX"
                    and line.split()[1].isdigit()
                ):

                    subcase = int(line.split()[1])
                    f06_result_dict[result_type]["lines"][subcase] = f06_lines[
                        line_number : line_number + 7
                    ]

                elif (
                    "MAXIMUM" in result_type
                    and result_type in f06_result_dict.keys()
                    and f06_result_dict[result_type]["started"]
                    and line.startswith("0")
                    and len(line.split()) > 6
                    and line.split()[1].isdigit()
                ):

                    subcase = int(line.split()[1])
                    f06_result_dict[result_type]["lines"][subcase] = line
                elif (
                    result_type == "R E A L   E I G E N V A L U E S"
                    and result_type in f06_result_dict.keys()
                    and f06_result_dict[result_type]["started"]
                    and line.startswith("      ")
                    and len(line.split()) >= 7
                    and line.split()[1].isdigit()
                ):
                    mode = int(line.split()[0])
                    #                    print(f"mode {mode}")
                    f06_result_dict[result_type]["lines"][mode] = line
                    if "frequencies" not in f06_result_dict[result_type].keys():
                        f06_result_dict[result_type]["frequencies"] = defaultdict()
                        f06_result_dict[result_type]["frequencies"][
                            mode
                        ] = line.strip().split()[4]
                    else:
                        f06_result_dict[result_type]["frequencies"][
                            mode
                        ] = line.strip().split()[4]

    return f06_result_dict


def analyse_f06(f06_filename, CoG_grid_id, OLOAD_SPCFORCE_comparison=True):

    if Path(f06_filename).exists():
        f06_result_dict = create_f06_result_dict(
            filename=f06_filename, CoG_grid_id=CoG_grid_id
        )
    else:
        print(f"File {f06_filename} does not exist")

    if OLOAD_SPCFORCE_comparison:
        # get OLOAD RESULTANT from f06 file
        oload = oload_spcforce_processing(
            f06_result_dict["OLOAD    RESULTANT"]["lines"]
        )

        # get SPCFORCE RESULTANT from f06 file
        spcforce = oload_spcforce_processing(
            f06_result_dict["SPCFORCE RESULTANT"]["lines"]
        )

        # compare OLOAD and SPCFORCE resultants and print warning if absolute and relative
        # difference for any subcase or resultant component exceed 'tol'
        compare_oload_spcforce(oload, spcforce, tol=1)

    return f06_result_dict
