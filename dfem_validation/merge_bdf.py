# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 14:49:20 2022

@author: DONIK94
"""

from pathlib import Path
import os
from tqdm import tqdm
import traceback
import sys
import tkinter as tk
from tkinter import filedialog


def get_merged_text(filename, level=0):
    # Check if path exists
    if Path(filename).exists():
        filename_abs = Path(filename).resolve()
    else:
        print(filename, "could not be found")

    merged_text = []
    relative_path = filename_abs.relative_to(filename_abs.parents[level])
    line = f"$ >>> Level   {int(level)}   ./{str(relative_path).replace(os.path.sep, '/')}\n"

    merged_text.append(line)

    with open(filename_abs, "r") as original_file:
        multiline = False
        for line in tqdm(original_file, position=0, leave=True, desc=filename_abs.name):
            if not line.startswith("INCLUDE") and multiline == False:
                merged_text.append(f"{line.rstrip()}\n")
            elif not line.startswith("INCLUDE") and multiline == True:
                second_part = line[:-2]
                include_file = first_part + second_part

                if Path(filename.parent / Path(include_file)).exists():
                    include_filename = Path(
                        filename.parent / Path(include_file)
                    ).resolve()
                else:
                    print(
                        Path(filename.parent / Path(include_file)), "could not be found"
                    )
                    input("press any key to exit")
                    exit
                merged_text.append(f"$ Original include statement:\n")

                line = f"$    INCLUDE '{include_file}'\n"

                merged_text.append(line)
                merged_text += get_merged_text(include_filename, level=level + 1)
                multiline = False
            else:

                if "'\n" in line[9:]:
                    include_file = line[9:-2]  #  extract filename
                else:
                    first_part = line[9:-1]  #  first part of the include
                    multiline = True  #  if include is written on two lines
                    continue  #  skip the rest if include is written on two lines
                if Path(filename.parent / Path(include_file)).exists():
                    include_filename = Path(
                        filename.parent / Path(include_file)
                    ).resolve()
                else:
                    print(
                        Path(filename.parent / Path(include_file)), "could not be found"
                    )
                    input("press any key to exit")
                    exit

                merged_text.append(f"$ Original include statement:\n")

                line = f"$    INCLUDE '{include_file}'\n"
                merged_text.append(line)

                merged_text += get_merged_text(include_filename, level=level + 1)

    line = f"$ <<< Level   {int(level)}   ./{str(relative_path).replace(os.path.sep, '/')}\n"

    merged_text.append(line)
    return merged_text


def merge_bdf(filename):
    if Path(filename).exists():
        filename_abs = Path(filename).resolve()
    else:
        print(filename, "could not be found")

    merged_file_name = Path(
        filename_abs.parent / Path(f"{filename_abs.stem}_merged{filename_abs.suffix}")
    )
    merged_lines = get_merged_text(filename_abs)

    with open(merged_file_name, mode="w", encoding="utf-8") as f:
        f.write("".join(merged_lines))
    return merged_file_name


if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)

        input_file_path = filedialog.askopenfilename(
            parent=root,
            initialdir=os.getcwd(),
            title="Please select root file:",
            filetypes=[("Nastran bulk data file", ".bdf" ".dat")],
        )
        merged_file_name = merge_bdf(input_file_path)
        print(f"File {Path(merged_file_name).name} was sucessfully created")
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
