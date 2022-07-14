# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 14:26:07 2022

@author: DONIK94
"""

from subprocess import call
import time
from . import unix_process_functions as upf


def create_nastran_launcher(
    filemask="*.dat",
    licenses_thershold=690,
    licenses_for_run=420,
    nastran_path="/opt/msc/nastran_2013.1/bin/nast20131",
    filename="./nastran_launcher.sh",
):
    shell_script_launcher = f"""#!/bin/sh

# PARAMETERS TO ADJUST
licenses_thershold={licenses_thershold} # number of free licenses below which no calculation is started
licenses_for_run={licenses_for_run} # number of licenses for a single nastran run
# also adjust "command" variable below

file='{filemask}'

filename=`basename ${{file}}`
dir=${{file%/*}}
filename_woExt=$(echo "$filename" | cut -f 1 -d '.')

command="{nastran_path} ./$filename mem=8gb buffsize=65537 mode=i4 scr=yes sdir=/expert_scratch bat=no"
licenses=$((2029-$(msclicstat | grep Users | awk -F " " '{{ print $11}}'))) # free nastran licenses

echo "licences: "$licenses
while [ $licenses -le $licenses_thershold ]; do 
	#echo sleeping
	sleep 180 # 3 min to wait for 70 additional Connector licenses to be taken
	
	licenses=$((2029-$(msclicstat | grep Users | awk -F " " '{{ print $11}}')))
done
(cd $dir; $command) &

sleep 5


"""
    with open(filename, "w") as f:
        f.write(shell_script_launcher)


def launch_nastran(launcher_filename, wait=True):
    command = launcher_filename
    initial_nastran_proc = upf.findProcessIdByName("analysis")
    process = call(("sh", command), shell=False)
    time.sleep(5)
    current_nastran_proc = upf.findProcessIdByName("analysis")

    # get process id in linux
    new_nastran_processes = [
        x for x in current_nastran_proc if x not in initial_nastran_proc
    ]

    if len(new_nastran_processes) > 1:
        # should never happen, just a redundance
        print("Warning! more than 1 process was created! Check")

    print("Nastran is running ...")
    time.sleep(5)
    if wait:
        while upf.checkIfProcessRunningByID(int(new_nastran_processes[0]["pid"])):
            # wait while Nastran is running
            time.sleep(5)
