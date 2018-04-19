#!/usr/bin/env python3
# Author: Rick Gelhausen
import sys, argparse
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
    parser = argparse.ArgumentParser(description="Script to merge multiple benchmarks")
    parser.add_argument("-i", "--ifile", action="store", dest="infileName", default=os.path.join("benchmark.csv")
                        , help="The default name of the result file of the benchmarking script")
    parser.add_argument("-o", "--ofile", action="store", dest="outputfile", default=os.path.join("")
                        , help="Mandatory path and name for the outputfile.")
    parser.add_argument("-d", "--bdirs", action="store", dest="benchFilePath", default=os.path.join("..", "output")
                        , help=" path to the benchmark folders.")
    parser.add_argument("-b", "--benchID", action="store", dest="benchID", default=""
                        , help="a mandatory ID to differentiate between multiple calls of the script. Specify multiple ones by using benchID1/benchID2/...")
    parser.add_argument("-a", "--all", action="store_true", dest="all", default=False
                        , help="When set all available benchmark folders will be merged.")
    args = parser.parse_args();

    # Enforce an outputfile path/name.csv
    if args.outputfile == "":
        sys.exit("Please use: python3 mergeBenchmarks.py -o <path/name.csv> to specify an output file!")

    # read all benchfiles in folder
    allIDfolders = [x for x in glob.glob(os.path.join(args.benchFilePath, "*")) if os.path.isdir(x)]
    print(allIDfolders)

    if not args.all:
        # Check whether a benchID was given
        if args.benchID == "" or not "/" in args.benchID:
            sys.exit("Please specify atleast two benchIDs using python3 mergeBenchmarks -b <name1/name2>")

        toBeMerged = []
        existingBenchIDs = []
        benchIDs = args.benchID.split("/")
        for bID in benchIDs:
            for folder in allIDfolders:
                if bID == folder.split(os.path.sep)[-1]:
                    toBeMerged.append(os.path.join(folder, args.infileName))
                    existingBenchIDs.append(bID)

        if len(toBeMerged) > 1:
            mergeBenchmarks(toBeMerged, args.outputfile)
            mergeLogFiles(existingBenchIDs, args.benchFilePath, args.outputfile)
        else:
            sys.exit("Not enough files to merge!")

    # Merge all
    else:
        if len(allIDfolders) > 1:
            allIDfolders = [os.path.join(x, args.infileName) for x in allIDfolders]

            mergeBenchmarks(allIDfolders, args.outputfile)
            allIDs = [x.split(os.path.sep)[-2] for x in allIDfolders]
            mergeLogFiles(allIDs, args.benchFilePath, args.outputfile)
        else:
            sys.exit("Not enough files to merge!")


if __name__ == "__main__":
    main(sys.argv[1:])
