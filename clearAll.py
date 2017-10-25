#!/usr/bin/python
# Author: Rick Gelhausen
import sys, getopt
import os
import glob

########################################################################################################################
#                                                                                                                      #
#                            Clear folders, allows clearing only certain callIDs                                       #
#                                 Removes log, benchmark and call CSV files                                            #
#                                                                                                                      #
########################################################################################################################

# help text
usage= "Call with: python3 calls.py -a1 <argument1> -a2 ..." \
       "The following arguments are available:\n" \
       "--ffile  (-f) : location where the folders containing the fasta files lie. Default: ./predictions .\n" \
       "--callID (-c) : Allows clearing only certain callIDs. Specify multiple callIDs with callID1|callID2|... \n" \
       "--help   (-h) : print this usage. \n"

def deleteFiles(filesToDeleteList):
    for file in filesToDeleteList:
        try:
            if os.path.isfile(file):
                os.unlink(file)
        except Exception as e:
            print(e)

def main(argv):
    fastaFilePath = os.path.join(".", "predictions")
    benchmarkFilePath = os.path.join(".", "benchmarks")
    logFilePath = os.path.join(".", "logs")
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
            fastaFilePath = arg
        elif opt in ("-c", "--callID"):
            callID = arg

    # read all files
    allFiles = []
    allFiles += glob.glob(os.path.join(fastaFilePath,"**","*.csv"))
    allFiles += glob.glob(os.path.join(benchmarkFilePath,"*.csv"))
    allFiles += glob.glob(os.path.join(logFilePath,"*.txt"))

    # clear all create files
    if callID == "":
        for file in allFiles:
            print("File: %s flagged for delete!" % (file))

        sys.stdout.write("Do you want to delete all files? [y/n]")
        choice = input().lower()
        if choice in ["y","yes"]:
            deleteFiles(allFiles)
        else:
            sys.exit("Aborting!!!")
    else:
        callIDs = []
        if "|" in callID:
            callIDs = callID.split("|")
        else:
            callIDs.append(callID)

        filesToDelete = []
        for c in callIDs:
            _inCallID = c.count("_")
            for file in allFiles:
                if c == "_".join(file.split(os.path.sep)[-1].split("_")[:_inCallID+1]):
                    print("File: %s flagged for delete!" % (file))
                    filesToDelete.append(file)

        sys.stdout.write("Do you want to delete the specified files? [y/n]")
        choice = input().lower()
        if choice in ["y", "yes"]:
            deleteFiles(filesToDelete)
        else:
            sys.exit("Aborting!!!")

if __name__ == "__main__":
    main(sys.argv[1:])
