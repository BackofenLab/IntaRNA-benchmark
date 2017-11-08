#!/usr/bin/python
# Author: Rick Gelhausen
import sys, getopt
import os.path
import glob
import pandas as pd

########################################################################################################################
#                                                                                                                      #
#                              Merge benchmark csv files ending in _benchmark.csv                                      #
#                               Also merges the according memory and time files                                        #
#                                        Merge all or specific callIDs                                                 #
#                                                                                                                      #
########################################################################################################################

# help text
usage = "Call with: python3 mergeBenchmarks.py -a1 <argument1> -a2 ... \n" \
        "The following arguments are available: \n" \
        "--ofile   (-o) : path and name of outputfile. MANDATORY. .\n" \
        "--bdirs   (-d) : path to the benchmark folder. Default: ./output \n" \
        "--benchID (-b) : benchIDs to be merged. benchID1/benchID2/... \n" \
        "--all     (-a) : if parameter is set no benchID needs to be specified. Every ID is used automatically.\n" \
        "--help    (-h) : print usage. \n"


# This method assumes an equal setup of all benchmark files
def mergeBenchmarks(benchList, outputPath):
    resultBenchDF = pd.read_csv(benchList[0], sep=";", header=0)
    for bench in benchList[1:]:
        nextbench = pd.read_csv(bench, sep=";", header=0)
        resultBenchDF = pd.merge(resultBenchDF, nextbench)

    # Order the columns
    preorder = ["srna_name", "target_ltag", "target_name"]
    tags = [x for x in resultBenchDF.columns if x not in preorder]
    neworder = preorder + sorted(tags)
    resultBenchDF.reindex(columns=neworder)

    # Write to csv
    resultBenchDF.to_csv(outputPath, sep=";", index=False)


# Merge method for memory and time files
def mergeLogFiles(benchIDList, benchPath, outputpath):
    timeDF = pd.read_csv(os.path.join(benchPath, benchIDList[0], "runTime.csv"), sep=";", header=0)
    memoryDF = pd.read_csv(os.path.join(benchPath, benchIDList[0], "memoryUsage.csv"), sep=";", header=0)
    for benchID in benchIDList[1:]:
        nextTimeDF = pd.read_csv(os.path.join(benchPath, benchID, "runTime.csv"), sep=";", header=0)
        nextMemoryDF = pd.read_csv(os.path.join(benchPath, benchID, "memoryUsage.csv"), sep=";", header=0)

        # Concatenate next dataframes
        timeDF = pd.concat([timeDF, nextTimeDF]).drop_duplicates().reset_index(drop=True)
        memoryDF = pd.concat([memoryDF, nextMemoryDF]).drop_duplicates().reset_index(drop=True)

    # Sort dataframes according to their benchID
    timeDF = timeDF.sort_values("callID")
    memoryDF = memoryDF.sort_values("callID")

    # Write to csv
    timeDF.to_csv(outputpath[:-len(".csv")] + "_runTimes.csv", sep=";", index=False)
    memoryDF.to_csv(outputpath[:-len(".csv")] + "_MaxMemoryUsage.csv", sep=";", index=False)


def main(argv):
    benchFilePath = os.path.join("..", "output")
    infileName = "benchmark.csv"
    outputfile = ""
    benchID = ""
    all = False
    try:
        opts, args = getopt.getopt(argv, "hi:o:d:b:a", ["ifile=", "ofile=", "bdirs=", "benchID="])
    except getopt.GetoptError:
        print("ERROR! Call <python3 mergeBenchmarks.py -h> for help!")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            infileName = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-d", "--bdirs"):
            benchFilePath = arg
        elif opt in ("-b", "--benchID"):
            benchID = arg
        elif opt in ("-a", "--all"):
            all = True

    # Enforce an outputfile path/name.csv
    if outputfile == "":
        sys.exit("Please use: python3 mergeBenchmarks.py -o <path/name.csv> to specify an output file!")

    # read all benchfiles in folder
    allIDfolders = [x for x in glob.glob(os.path.join(benchFilePath, "*")) if os.path.isdir(x)]
    print(allIDfolders)

    if not all:
        # Check whether a benchID was given
        if benchID == "" or not "/" in benchID:
            sys.exit("Please specify atleast two benchIDs using python3 mergeBenchmarks -b <name1/name2>")

        toBeMerged = []
        existingBenchIDs = []
        benchIDs = benchID.split("/")
        for bID in benchIDs:
            for folder in allIDfolders:
                if bID == folder.split(os.path.sep)[-1]:
                    toBeMerged.append(os.path.join(folder, infileName))
                    existingBenchIDs.append(bID)

        if len(toBeMerged) > 1:
            mergeBenchmarks(toBeMerged, outputfile)
            mergeLogFiles(existingBenchIDs, benchFilePath, outputfile)
        else:
            sys.exit("Not enough files to merge!")

    # Merge all
    else:
        if len(allIDfolders) > 1:
            allIDfolders = [os.path.join(x, infileName) for x in allIDfolders]

            mergeBenchmarks(allIDfolders, outputfile)
            allIDs = [x.split(os.path.sep)[-2] for x in allIDfolders]
            mergeLogFiles(allIDs, benchFilePath, outputfile)
        else:
            sys.exit("Not enough files to merge!")


if __name__ == "__main__":
    main(sys.argv[1:])