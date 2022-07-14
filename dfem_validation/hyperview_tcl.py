# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 15:49:25 2022

@author: DONIK94
"""
from pathlib import Path
import os
from sys import platform
import time
from . import unix_process_functions as upf
from subprocess import call


def get_tcl_text(
    check_filename,
    screenshots_folder,
    picture_width=1024,
    picture_height=768,
    legend_decimals=2,
    data_types=["Displacement"],
):

    #    if data_type not in ['Displacement', 'Stress']:
    #        print("ERROR")

    current_dir = str(Path(check_filename).resolve().parent).replace("\\", "/")
    model_path = str(Path(check_filename).resolve()).replace("\\", "/")
    check_filename_path = Path(check_filename).resolve()
    filename = Path(check_filename).stem
    result_path = f"{str(Path(check_filename_path).parent / Path(check_filename).stem)}.op2".replace(
        "\\", "/"
    )

    tcl_filename = str(
        Path(check_filename_path.parent / Path(f"{filename.lower()}_script.tcl"))
    )
    folder_name = Path(screenshots_folder).name
    try:
        os.mkdir(Path(check_filename_path.parent / folder_name))
    except FileExistsError:
        pass

    output = f"""
###################################################################
#           EXTRACTING PICTURES FOR {filename.upper()}                  
###################################################################
    
# Change current dirrectory
cd {current_dir}

# set model and results
set model_path {model_path}
set result_path {result_path}

# get handles
hwi OpenStack
hwi GetSessionHandle session
session GetProjectHandle project
project GetPageHandle page [project GetActivePage]
page GetWindowHandle win [page GetActiveWindow]
win SetClientType animation
win GetClientHandle anim
win GetViewControlHandle vw_hndl

# load model
set id [anim AddModel $model_path "NASTRAN Model Input Reader"]
anim GetModelHandle myModel $id

# Get Parts list
set partlist [myModel GetEntityList part]

# Mask everything
myModel MaskAll system
myModel MaskAll parts
myModel MaskAll elements



# Unmask parts
foreach prt $partlist {{
	myModel GetComponentHandle comp $prt
	comp SetVisibility False
	comp SetVisibility True
	comp ReleaseHandle
}}

# Mask RBE
set rbe_set_id [myModel AddSelectionSet element]
myModel GetSelectionSetHandle rbe_set $rbe_set_id
# RIGID
rbe_set Add "config 5"   
# RIGIDLINK
rbe_set Add "config 55"   
# RBE3
rbe_set Add "config 56"   

myModel Mask $rbe_set_id

# fit view
vw_hndl Fit 

# Attach results
myModel SetResult $result_path
myModel GetResultCtrlHandle myResult

# Display legend
anim SetDisplayOptions "legend" true

# Set Grapic Area
p_SetGraphicArea {picture_width} {picture_height}

# get Subcases
set subcases [myResult GetSubcaseList Base]

# Hide Default Model Info
anim GetNoteHandle note_handle 1
note_handle SetVisibility False

# Create custom Note
anim GetNoteHandle new_note_handle [anim AddNote]
new_note_handle SetText "{{window.shortmodelfilename}} 
{{window.shortresultfilename}} 
{{window.loadcase}} #
{{window.simulationstep}}"

# Set Note position to the top right corner
new_note_handle SetPosition 1 0

myModel SetMeshMode meshlines

# Create counter for pictures
set pic_counter 0


foreach subcase $subcases {{

set simulations [myResult GetSimulationList $subcase]
# simulation counter
set sim_counter 0  

foreach simulation $simulations {{

set data_types {{{", ".join(data_types)}}}
        
foreach data_type $data_types {{
incr pic_counter
myResult SetCurrentSubcase $subcase
myResult SetCurrentSimulation $sim_counter

# Plot Result Contour
myResult GetContourCtrlHandle ResultContour
ResultContour SetDataType $data_type
ResultContour SetEnableState true
ResultContour SetDiscreteColor true
if {{$data_type == "Stress"}} {{
    ResultContour SetDataComponent "vonMises"
	ResultContour SetLayer "Max"

	}}

# Customize legend
ResultContour GetLegendHandle legend_hndl
legend_hndl SetFilter Linear
legend_hndl SetPosition upperleft
legend_hndl SetNumericFormat "fixed"
legend_hndl SetNumericPrecision "2"

# Reset animation to the First Frame
page GetAnimatorHandle animator
animator SetCurrentFrame 0
animator Start
animator Stop

incr sim_counter

#Apply vizual changes
anim Draw

# Save screenshot
save_pic "./{folder_name}" "{filename.lower()}" $pic_counter

# Release handles
animator ReleaseHandle
legend_hndl ReleaseHandle
ResultContour ReleaseHandle
}}
}}
}}

# Delete model
anim Clear

# Release handles
note_handle ReleaseHandle
new_note_handle ReleaseHandle
session ReleaseHandle
project ReleaseHandle
page ReleaseHandle
win ReleaseHandle
vw_hndl ReleaseHandle
hwi CloseStack

"""

    return output, tcl_filename


def add_common_procedures(text=""):
    output = text
    output += f"""
###################################################################
#           COMMON PROCEDURES
###################################################################
proc p_SetGraphicArea {{Width Height}} {{
  set gframe .mainFrame.center.f3.center_frm.graphicfrm
  set pinfo [pack info $gframe]
  set pmaster [dict get $pinfo -in]
  set pmasterH [winfo height $pmaster]
  set pmasterW [winfo width $pmaster]
  set padX [expr ($pmasterW-$Width)/2]
  set padY [expr ($pmasterH-$Height)/2]
  set padX [expr $padX<0?0:$padX]
  set padY [expr $padY<0?0:$padY]
  pack configure $gframe -padx $padX -pady $padY
  list $pmasterW $pmasterH

}}

proc save_pic {{dpath picname picnum}} {{
set picpath $dpath
append picpath "/" $picname "_" $picnum ".png"
session CaptureScreen PNG $picpath

}}    
"""
    return output


def add_close_hw(text=""):
    output = text
    output += f"""
###################################################################
#           Close Hyperview
###################################################################

hwi OpenStack
hwi GetSessionHandle session
session Close
"""
    return output


def add_to_tcl_masterfile(text_to_add, tcl_masterfile_text=""):

    output = tcl_masterfile_text + "\n" + text_to_add + "\n"
    return output


def write_tcl_script(tcl_filename, text_to_write):

    with open(tcl_filename, "w") as f:
        f.write(text_to_write)


def launch_hyperview(tcl_filename):
    if platform == "linux":
        hw_filepath = "/opt/altair/2021.2/altair/scripts/hw"
    else:
        hw_filepath = "C:/Program Files/Altair/2019/hw/bin/win64/hw.exe"

    print("Running Hyperview (platform:", platform, ") ...")
    print("Hyperview path:", hw_filepath)
    #        print("platform", platform)
    if platform == "linux":
        command = " -tcl " + str(Path(tcl_filename).resolve()).replace("\\", "/")
        line = hw_filepath + command
        process = call((hw_filepath, command), shell=False)
        while upf.checkIfProcessRunning("hw"):
            time.sleep(5)
    else:
        command = ' -tcl "' + str(Path(tcl_filename).resolve()).replace("\\", "/") + '"'
        line = '"' + hw_filepath + '"' + command
        process = call(line, shell=False)


# gravity_check_filename = './DFEM_Validation/Gravity_Check.dat'
# unit_check_filename = './DFEM_Validation/Unit_Check.dat'
# dynamic_check_filename = './DFEM_Validation/Dynamic_Check.dat'
# thermoelastic_check_filename = './DFEM_Validation/Thermoelastic_Check.dat'


def create_screenshots_with_hyperview(
    gravity_check_filename,
    unit_check_filename,
    dynamic_check_filename,
    thermoelastic_check_filename,
    screenshots_folder,
):
    gravity_check_tcl_text, _ = get_tcl_text(
        gravity_check_filename, screenshots_folder=screenshots_folder
    )
    unit_check_tcl_text, _ = get_tcl_text(
        unit_check_filename,
        data_types=["Stress"],
        screenshots_folder=screenshots_folder,
    )
    dynamic_check_tcl_text, _ = get_tcl_text(
        dynamic_check_filename, screenshots_folder=screenshots_folder
    )
    thermoelastic_check_tcl_text, tcl_filename = get_tcl_text(
        thermoelastic_check_filename,
        data_types=["Displacement", "Stress"],
        screenshots_folder=screenshots_folder,
    )
    tcl_masterfile_text = add_common_procedures()
    tcl_masterfile_text = add_to_tcl_masterfile(
        gravity_check_tcl_text, tcl_masterfile_text
    )
    tcl_masterfile_text = add_to_tcl_masterfile(
        unit_check_tcl_text, tcl_masterfile_text
    )
    tcl_masterfile_text = add_to_tcl_masterfile(
        dynamic_check_tcl_text, tcl_masterfile_text
    )
    tcl_masterfile_text = add_to_tcl_masterfile(
        thermoelastic_check_tcl_text, tcl_masterfile_text
    )
    tcl_masterfile_text = add_close_hw(tcl_masterfile_text)
    tcl_masterfile_path = Path(Path(tcl_filename).parent / "masterscript.tcl")

    write_tcl_script(tcl_masterfile_path, tcl_masterfile_text)

    launch_hyperview(tcl_masterfile_path)


print("Finished")
