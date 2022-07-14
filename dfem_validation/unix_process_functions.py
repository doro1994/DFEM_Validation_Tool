# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 14:18:36 2022

@author: DONIK94
"""
import psutil
import getpass
from sys import platform


def checkIfProcessRunning(processName):
    """
    Check if there is any running process that contains the given name processName.
    """
    if platform == "linux":
        # Iterate over the all the running process
        user_name = getpass.getuser()
        for proc in psutil.process_iter():
            if proc.username() == user_name:
                try:
                    # Check if process name contains the given name string.
                    if processName.lower() in proc.name().lower():
                        #                       print(f"Process found! {findProcessIdByName(processName)}")
                        return True
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    pass
    return False


def checkIfProcessRunningByID(processID):
    """
    Check if there is any running process that contains the given name processName.
    """
    if platform == "linux":
        # Iterate over the all the running process
        user_name = getpass.getuser()
        for proc in psutil.process_iter():
            if proc.username() == user_name:
                try:
                    # Check if process name contains the given name string.
                    if int(processID) == int(proc.pid):
                        #                       print(f"Process found! {findProcessIdByName(processName)}")
                        return True
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    pass
    return False


def findProcessIdByName(processName):
    """
    Get a list of all the PIDs of a all the running process whose name contains
    the given string processName
    """
    listOfProcessObjects = []
    if platform == "linux":
        user_name = getpass.getuser()

        # Iterate over the all the running process
        for proc in psutil.process_iter():
            if proc.username() == user_name:
                try:
                    pinfo = proc.as_dict(attrs=["pid", "name", "create_time"])
                    # Check if process name contains the given name string.
                    if processName.lower() in pinfo["name"].lower():
                        listOfProcessObjects.append(pinfo)
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    pass
    return listOfProcessObjects
