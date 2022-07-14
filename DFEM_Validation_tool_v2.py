"""
File Name:    DFEM_Validation_Tool.py  
Version:      1    
Date:         19.05.2022   

Author/Owner: N. Dorofeev

-------------------------------------------------------------------------------------------

# Current script is created for DFEM Validation 
# It takes as input runnable bdf file from which all the relevant information about 
# the DFEM is extracted

-------------------------------------------------------------------------------------------
Version Description:

  Version   | Version Description
 -----------|-----------------------
  1         | - initial creation by N. Dorofeev
            |            
"""
import sys

# sys.path.append("./modules")
from dfem_validation import bdf_processing
import dfem_validation.unix_process_functions as upf
import time
import traceback
import tkinter as tk
import os
from pathlib import Path
from dfem_validation.merge_bdf import merge_bdf
from dfem_validation.gravity_check import launch_gravity_check
from dfem_validation.unit_displacement_check import launch_unit_check
from dfem_validation.dynamic_check import launch_dynamic_check
from dfem_validation.thermoelastic_check import launch_thermoelastic_check
from dfem_validation.f06_processing import analyse_f06
from sys import platform
from tkinter import filedialog
from dfem_validation.word_creation import create_report
from dfem_validation.hyperview_tcl import create_screenshots_with_hyperview


def main(
    INPUT_BDF_FILE="./NASTRAN_TEMPLATE.input", relaunch_gravitycheck=True, mode=12
):

    # Check if path exists
    if Path(INPUT_BDF_FILE).exists():
        input_bdf_file_path = Path(INPUT_BDF_FILE).resolve()
    else:
        print(INPUT_BDF_FILE, "could not be found")

    # Nastran checks filenames
    gravity_check_filename = str(
        Path(input_bdf_file_path.parent / Path("./DFEM_Validation/Gravity_Check.dat"))
    )
    unit_check_filename = str(
        Path(input_bdf_file_path.parent / Path("./DFEM_Validation/Unit_Check.dat"))
    )
    dynamic_check_filename = str(
        Path(input_bdf_file_path.parent / Path("./DFEM_Validation/Dynamic_Check.dat"))
    )
    thermoelastic_check_filename = str(
        Path(
            input_bdf_file_path.parent
            / Path("./DFEM_Validation/Thermoelastic_Check.dat")
        )
    )
    screenshots_folder = str(
        Path(input_bdf_file_path.parent / Path("./DFEM_Validation/screenshots"))
    )

    f06_gravitycheck_filename = f"{str(Path(gravity_check_filename).parent / Path(gravity_check_filename).stem)}.f06"
    overwrite_groundcheck = "y"
    if mode != 2 and platform == "linux" and Path(f06_gravitycheck_filename).exists():
        print("WARNING! {f06_gravitycheck_filename} already exists!")
        overwrite_groundcheck = input("Do you want to overwrite? (y/n)")
    if overwrite_groundcheck != "y" and overwrite_groundcheck != "n":
        print("Not valid input: {overwrite_groundcheck}! F06 file won't be overwritten")

    # get merged file
    merged_input = merge_bdf(input_bdf_file_path)

    # get all used ids
    existing_ids = bdf_processing.get_bdf_id_list(merged_input)

    # select free id for CoG grid
    CoG_grid_id = bdf_processing.select_free_id(
        existing_ids, starting_id=99999999, ascending=False
    )

    # select free id for SPC
    SPC_ID = bdf_processing.select_free_id(
        existing_ids, starting_id=1000, ascending=True
    )

    # get SPCADD card if existing
    spcadd_card = bdf_processing.get_spcadd_card(input_bdf_file_path)

    # get unit_check RBE2 ID
    RBE2_id = bdf_processing.select_free_id(existing_ids, starting_id=1, ascending=True)

    # get DFEM elements
    df_element_grids = bdf_processing.get_dfem_elements_df(merged_input)

    # create DFEM_Validation folder
    try:
        os.mkdir(Path(input_bdf_file_path.parent / "DFEM_Validation"))
    except FileExistsError:
        pass

    if mode == 1 or mode == 12:

        if overwrite_groundcheck == "y":
            print(f"Launching Gravity Check")
            # launch gravity check
            launch_gravity_check(
                df_element_grids,
                input_bdf_file_path,
                gravity_check_filename=gravity_check_filename,
                SPC_ID=SPC_ID,
                spcadd_card=spcadd_card,
                overwrite=(overwrite_groundcheck == "y"),
                wait_completion=True,
            )

        if mode == 1 and not Path(f06_gravitycheck_filename).exists():
            return
        # once calcualtion is finished, read f06 file and extract relevant information
        f06_gravitycheck_dict = analyse_f06(
            f06_gravitycheck_filename,
            CoG_grid_id=CoG_grid_id,
            OLOAD_SPCFORCE_comparison=False,
        )

        initial_nastran_proc = upf.findProcessIdByName("analysis")

        #        try:
        # launch unit-dispalcement check
        launch_unit_check(
            df_element_grids,
            input_bdf_file_path,
            f06_gravitycheck_dict,
            CoG_grid_id=CoG_grid_id,
            SPC_ID=SPC_ID,
            RBE_id=RBE2_id,
            unit_check_filename=unit_check_filename,
            spcadd_card=spcadd_card,
            wait_completion=False,
        )
        #        except:
        #            print("Something is wrong with Gtravity Check F06 file!")
        #            return

        # launch dynamic check
        launch_dynamic_check(
            df_element_grids,
            input_bdf_file_path,
            f06_gravitycheck_dict,
            CoG_grid_id=CoG_grid_id,
            SPC_ID=SPC_ID,
            dynamic_check_filename=dynamic_check_filename,
            spcadd_card=spcadd_card,
            wait_completion=False,
        )

        # launch thermoelastic check
        launch_thermoelastic_check(
            df_element_grids,
            input_bdf_file_path,
            SPC_ID=SPC_ID,
            thermoelastic_check_filename=thermoelastic_check_filename,
            spcadd_card=spcadd_card,
            wait_completion=True,
        )

        current_nastran_proc = upf.findProcessIdByName("analysis")

        # get process id in linux
        new_nastran_processes = [
            x for x in current_nastran_proc if x not in initial_nastran_proc
        ]

        # Wait until all the Nastran analyses are finished
        if platform == "linux":
            for process in new_nastran_processes:
                while upf.checkIfProcessRunningByID(int(process["pid"])):
                    # wait while Nastran is running
                    time.sleep(5)

    if mode == 2 or mode == 12:
        # Analyse Gravity Check F06 file
        f06_gravitycheck_filename = f"{str(Path(gravity_check_filename).parent / Path(gravity_check_filename).stem)}.f06"
        f06_gravitycheck_dict = analyse_f06(
            f06_gravitycheck_filename,
            CoG_grid_id=CoG_grid_id,
            OLOAD_SPCFORCE_comparison=False,
        )

        # Analyse Unit Displacement Check F06 file
        f06_unitcheck_filename = f"{str(Path(unit_check_filename).parent / Path(unit_check_filename).stem)}.f06"
        f06_unitcheck_dict = analyse_f06(
            f06_unitcheck_filename,
            CoG_grid_id=CoG_grid_id,
            OLOAD_SPCFORCE_comparison=False,
        )

        # Analyse Unit Displacement Check F06 file
        f06_dynamic_check_filename = f"{str(Path(dynamic_check_filename).parent / Path(dynamic_check_filename).stem)}.f06"
        f06_dynamic_dict = analyse_f06(
            f06_dynamic_check_filename,
            CoG_grid_id=CoG_grid_id,
            OLOAD_SPCFORCE_comparison=False,
        )

        # Analyse Thermoelastic Check F06 file
        f06_thermoelastic_check_filename = f"{str(Path(thermoelastic_check_filename).parent / Path(thermoelastic_check_filename).stem)}.f06"
        f06_thermoelastic_dict = analyse_f06(
            f06_thermoelastic_check_filename,
            CoG_grid_id=CoG_grid_id,
            OLOAD_SPCFORCE_comparison=False,
        )

        # create screeshots with hyperview
        create_screenshots_with_hyperview(
            gravity_check_filename=gravity_check_filename,
            unit_check_filename=unit_check_filename,
            dynamic_check_filename=dynamic_check_filename,
            thermoelastic_check_filename=thermoelastic_check_filename,
            screenshots_folder=screenshots_folder,
        )

        # create preliminary report
        report_name = Path(
            Path(input_bdf_file_path).parent
            / Path("./DFEM_Validation_Preliminary_report.docx")
        )
        create_report(
            f06_gravitycheck_dict=f06_gravitycheck_dict,
            f06_unitcheck_dict=f06_unitcheck_dict,
            f06_dynamic_dict=f06_dynamic_dict,
            f06_thermoelastic_dict=f06_thermoelastic_dict,
            screenshots_folder=screenshots_folder,
            filename=report_name,
        )


if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)

        input_file_path = filedialog.askopenfilename(
            parent=root,
            initialdir=os.getcwd(),
            title="Please select input file:",
            filetypes=[("Nastran bulk data file", ".input")],
        )
        display_text = (
            f"Choose program launching mode \n"
            f"1:  Create Nastran Files and Launch Nastran (if started under Linux) \n"
            f"2:  Create Word Report based on Nastran Results \n"
            f"12: Consecutive launch of both modes 1 and 2 \n"
        )

        mode = int(input(display_text))
        main(input_file_path, relaunch_gravitycheck=False, mode=mode)
    except Exception:
        ex_type, ex_value, ex_traceback = sys.exc_info()

        # Extract unformatter stack traces as tuples
        trace_back = traceback.extract_tb(ex_traceback)

        # Format stacktrace
        stack_trace = list()

        for trace in trace_back:
            stack_trace.append(
                "File : %s , Line : %d, Func.Name : %s, Message : %s"
                % (trace[0], trace[1], trace[2], trace[3])
            )

        print("Exception type : %s " % ex_type.__name__)
        print("Exception message : %s" % ex_value)
        print("Stack trace : %s" % stack_trace)

print("Finished")
