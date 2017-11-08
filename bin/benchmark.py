#!/usr/bin/python
# Author: Rick Gelhausen, adapted from perl script by Patrick Wright
import sys, getopt
import os.path
import pandas as pd
import glob

# help text
usage= "Call with: python3 benchmark.py -a1 <argument1> -a2 ... \n" \
       "The following arguments are available: \n" \
       "--ifile   (-i) : path of the file containing the verified interactions. Default: ../verified_interactions.csv . \n" \
       "--ofile   (-o) : path of the benchmark outputfile. Default: ./benchmark.csv .\n" \
       "--pdirs   (-p) : path to directory containing the output of the calls script. Default: ../output \n" \
       "--benchID (-b) : mandatory benchID used to identify benchmarking. \n" \
       "--help    (-h) : print usage. \n"

def main(argv):
    verified_interactions = os.path.join("..", "verified_interactions.csv")
    directoryPath = os.path.join("..", "output")
    outputfile = "benchmark.csv"
    benchID = ""
    try:
        opts, args = getopt.getopt(argv,"hi:o:p:b:",["ifile=","ofile=","pdirs=","benchID="])
    except getopt.GetoptError:
        print("ERROR! Call <python3 benchmark.py -h> for help!")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            verified_interactions = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-p", "--pdirs"):
            directoryPath = arg
        elif opt in ("-b", "--benchID"):
            benchID = arg

    # Check whether a benchID was given
    if benchID == "":
        sys.exit("No benchID was specified! Please specify a benchID using -b <name> or --benchID=<name>")

    # read verified interactions
    if os.path.exists(verified_interactions) == True:
        with open(verified_interactions) as data:
            tempHybrid = [line.strip() for line in data]
    else:
        sys.exit("Error: %s! File not found!" % (verified_interactions))

    # check whether the benchID is valid (no file with that name exists)
    outputPath = os.path.join("..", "output", benchID, outputfile)
    if os.path.exists(outputPath):
        sys.exit("A file for this benchID already exists! Exiting...")


    # Create a dictionary for better accessibility of srna data
    confirmed_hybrids = dict()
    srnaList = []
    organisms = []
    for line in tempHybrid:
        spl = line.split(";")
        # create an list of srnas in the verified_interactions
        if not spl[0] in srnaList:
            srnaList.append(spl[0])

        if not spl[3] in organisms:
            organisms.append(spl[3])

        if (spl[0], spl[3]) in confirmed_hybrids:
            confirmed_hybrids[(spl[0], spl[3])].append((spl[1], spl[2]))
        else:
            confirmed_hybrids[(spl[0], spl[3])] = [(spl[1], spl[2])]

    print("Starting benchmarking: %s" % benchID)
    # Get all directories with needed files and sort them
    srna_files = [x for x in glob.glob(os.path.join(directoryPath, benchID, "*.csv")) if x.split(os.path.sep)[-1].split("_")[0] in srnaList]
    srna_files.sort()

    # Check whether the needed files for the benchmarking exist
    if srna_files == []:
        sys.exit("Error!!! No files found for benchmarking ID %s" % benchID)

    # Create a dictionary from the srna_files for better access
    srnaDict = dict()
    for srna in srnaList:
        if srna in srnaDict:
            srnaDict[srna].insert([x for x in srna_files if srna in x])
        else:
            srnaDict[srna] = [x for x in srna_files if srna in x]

    outputText= "srna_name;target_ltag;target_name;%s_intarna_rank\n" % benchID

    # determine the rank of intaRNA given the confirmed hybrids
    for srna_name in srnaList:
        for organism in organisms:
            if (srna_name, organism) in confirmed_hybrids:
                for confirmed_hybrid in confirmed_hybrids[(srna_name, organism)]:
                    for file in srnaDict[srna_name]:
                        df = pd.read_csv(file, sep=";", header=0)
                        df = df.sort_values("E")

                        target_ltag = confirmed_hybrid[0]
                        target_name = confirmed_hybrid[1]

                        try:
                            # Uses first column, maybe use id1 instead
                            # Adding 1 because df.ix[:,0] ignores the header and list starts with 0. Adding 1 fixes it.
                            intaRNA_rank = list(df.ix[:,0]).index(target_ltag) + 1

                            outputText += "%s;%s;%s;%s\n" % (srna_name, target_ltag, target_name, intaRNA_rank)
                        except ValueError:
                            continue



    # Check whether the outputFile is empty
    if outputText == "srna_name;target_ltag;target_name;intarna_rank\n":
        sys.exit("No reasonable output found!")

    # write csv file
    csv_file = open(os.path.join(outputPath), "w")
    csv_file.write(outputText)
    csv_file.close()

    print("Finished benchmarking: %s" % benchID)

if __name__ == "__main__":
   main(sys.argv[1:])