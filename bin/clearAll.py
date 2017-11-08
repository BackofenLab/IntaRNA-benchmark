#!/usr/bin/python
# Author: Rick Gelhausen
import sys, getopt
import os
import glob
import shutil

########################################################################################################################
#                                                                                                                      #
#                            Clear folders, allows clearing only certain callIDs                                       #
#                                 Removes log, benchmark and call CSV files                                            #
#                                                                                                                      #
########################################################################################################################

# help text
usage= "Call with: python3 calls.py -a1 <argument1> -a2 ..." \
       "The following arguments are available:\n" \
       "--ffile  (-f) : location of the output folder. Default: ../output/ .\n" \
       "--callID (-c) : Allows clearing only certain callIDs. Specify multiple callIDs with callID1/callID2/... \n" \
       "--help   (-h) : print this usage. \n"

def deleteFolders(foldersToDeleteList):
    for folder in foldersToDeleteList:
        try:
            if os.path.isdir(folder):
                shutil.rmtree(folder)
        except Exception as e:
            print(e)

def main(argv):
    inFilePath = os.path.join("..", "output")
    callID = ""

    # commandline parsing
    try:
        opts, args = getopt.getopt(argv,"hf:c:",["ffile=","callID="])
    except getopt.GetoptError:
        print("ERROR! Call <python3 clearAll.py -h> for help")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit()
        elif opt in ("-f", "--ffile"):
            inFilePath = arg
        elif opt in ("-c", "--callID"):
            callID = arg

    # read all files
    allFolders = glob.glob(os.path.join(inFilePath, "*"))

    # clear all created files
    if callID == "":
        for benchFolder in allFolders:
            print("File: %s flagged for delete!" % (benchFolder))

        sys.stdout.write("Do you want to delete all folders? [y/n]")
        choice = input().lower()
        if choice in ["y","yes"]:
            deleteFolders(allFolders)
        else:
            sys.exit("Aborting!!!")
    else:
        callIDs = []
        if "/" in callID:
            callIDs = callID.split("/")
        else:
            callIDs.append(callID)

        foldersToDelete = []
        for c in callIDs:
            for folder in allFolders:
                if c == folder.split(os.path.sep)[-1]:
                    print("Folder: %s flagged for delete!" % (folder))
                    foldersToDelete.append(folder)

        sys.stdout.write("Do you want to delete the specified folders? [y/n]")
        choice = input().lower()
        if choice in ["y", "yes"]:
            deleteFolders(foldersToDelete)
        else:
            sys.exit("Aborting!!!")

if __name__ == "__main__":
    main(sys.argv[1:])