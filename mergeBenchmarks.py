#!/usr/bin/python
# Author: Rick Gelhausen
import sys, getopt
import os.path
import glob
import pandas as pd

# help text
usage= "Call with: python3 mergeBenchmarks.py -a1 <argument1> -a2 ... \n" \
       "The following arguments are available: \n" \
       "--ofile   (-o) : path and name of outputfile. MANDATORY. .\n" \
       "--bdirs   (-d) : path to the benchmark folder. Default: ./benchmarks \n" \
       "--benchID (-b) : benchIDs to be merged. benchID1/benchID2|... \n" \
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

def main(argv):
    benchFilePath = os.path.join(".","benchmarks")
    outputfile = ""
    benchID = ""
    all = False
    try:
        opts, args = getopt.getopt(argv,"ho:d:b:a",["ofile=","bdirs=","benchID="])
    except getopt.GetoptError:
        print("ERROR! Call <python3 mergeBenchmarks.py -h> for help!")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit()
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
    allFiles = glob.glob(os.path.join(benchFilePath,"*_benchmark.csv"))
    print(allFiles)

    if not all:
        # Check whether a benchID was given
        if benchID == "" or not "/" in benchID:
            sys.exit("Please specify atleast two benchIDs using python3 mergeBenchmarks -b <name1/name2>")

        toBeMerged = []
        benchIDs = benchID.split("/")
        for bID in benchIDs:
            for file in allFiles:
                if bID == file.split(os.path.sep)[-1].split("_")[0]:
                    toBeMerged.append(file)

        if len(toBeMerged) > 1:
            mergeBenchmarks(toBeMerged, outputfile)
        else:
            sys.exit("Not enough files to merge!")

    # Merge all
    else:
        if len(allFiles) > 1:
            mergeBenchmarks(allFiles, outputfile)
        else:
            sys.exit("Not enough files to merge!")

if __name__ == "__main__":
   main(sys.argv[1:])