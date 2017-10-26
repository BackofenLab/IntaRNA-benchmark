#!/usr/bin/python
# Author: Rick Gelhausen, adapted from perl script by Patrick Wright
import sys, getopt
import os.path
import pandas as pd

# help text
usage= "Call with: python3 benchmark.py -a1 <argument1> -a2 ... \n" \
       "The following arguments are available: \n" \
       "--ifile   (-i) : path of the file containing the verified interactions lies. Default: verified_interactions.csv . \n" \
       "--ofile   (-o) : path of the benchmark outputfile. Default: ./<benchID>_benchmark.csv .\n" \
       "--pdirs   (-p) : path to directory containing srna folders. Default: ./predictions \n" \
       "--benchID (-b) : mandatory benchID used to identify benchmarking. \n" \
       "--help    (-h) : print usage. \n"

def main(argv):
    verified_interactions = "verified_interactions.csv"
    directoryPath = os.path.join(".","predictions")
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

    # check whether the benchID is valid (no file with that name exists)
    outputPath = os.path.join(".","benchmarks")
    if os.path.exists(os.path.join(outputPath, benchID + "_" + outputfile)):
        sys.exit("A file for this benchID already exists! Exiting...")

    # read verified interactions
    if os.path.exists(verified_interactions) == True:
        with open(verified_interactions) as data:
            tempHybrid = [line.strip() for line in data]
    else:
        sys.exit("Error: %s! File not found!" % (verified_interactions))

    print("Starting benchmarking: %s" % benchID)
    # Get all directories with needed files and sort them
    dirs = ([x[0] for x in os.walk(directoryPath)])[1:]
    dirs.sort()

    # Create a dictionary for better accessibility of srna data
    confirmed_hybrids = dict()
    for line in tempHybrid:
        spl = line.split(";")

        if "STM" in spl[1]:
            if (spl[0],"STM") in confirmed_hybrids:
                confirmed_hybrids[(spl[0],"STM")].append((spl[1], spl[2]))
            else:
                confirmed_hybrids[(spl[0],"STM")] = [(spl[1], spl[2])]
        else:
            if (spl[0],"b") in confirmed_hybrids:
                confirmed_hybrids[(spl[0],"b")].append((spl[1], spl[2]))
            else:
                confirmed_hybrids[(spl[0],"b")] = [(spl[1], spl[2])]



    # TODO: FIX this to always point at the right (b or STM) directory by calling benchmark.py in calls.py

    outputText= "srna_name;target_ltag;target_name;%s_intarna_rank\n" % benchID

    # determine the rank of intaRNA given the confirmed hybrids
    for dir in dirs:
        srna_name = dir.split(os.path.sep)[-1]

        # STM file
        stmFile = os.path.join(dir, benchID+"_"+srna_name+"_NC_003197.csv")
        # b file
        bFile = os.path.join(dir, benchID+"_"+srna_name+"_NC_000913.csv")

        # Check whether the requiered files for the benchmarking exists
        if not os.path.exists(stmFile) or not os.path.exists(bFile):
            print("CSV files not found for %s! Continuing with next srna!" % srna_name)
            continue

        # Salmonella case
        if (srna_name,"STM") in confirmed_hybrids:
            df = pd.read_csv(os.path.join(dir, benchID+"_"+srna_name+"_NC_003197.csv"), sep=";", header=0)
            df = df.sort_values("E")
            for confirmed_hybrid in confirmed_hybrids[(srna_name, "STM")]:
                target_ltag = confirmed_hybrid[0]
                target_name = confirmed_hybrid[1]

                try:
                    # Uses first column, maybe use id1 instead
                    # Adding 1 because df.ix[:,0] ignores the header and list starts with 0. Adding 1 fixes it.
                    intaRNA_rank = list(df.ix[:,0]).index(target_ltag) + 1

                    outputText += "%s,%s,%s,%s\n" % (srna_name, target_ltag, target_name, intaRNA_rank)
                except ValueError:
                    print("Could not find %s in file." % (target_ltag))

        # Echoli case
        if (srna_name,"b") in confirmed_hybrids:
            df = pd.read_csv(os.path.join(dir, benchID+"_"+srna_name+"_NC_000913.csv"), sep=";", header=0)
            df = df.sort_values("E")
            for confirmed_hybrid in confirmed_hybrids[(srna_name, "b")]:
                target_ltag = confirmed_hybrid[0]
                target_name = confirmed_hybrid[1]

                try:
                    # Uses first column, maybe use id1 instead
                    intaRNA_rank = list(df.ix[:, 0]).index(target_ltag) + 1

                    outputText += "%s,%s,%s,%s\n" % (srna_name, target_ltag, target_name, intaRNA_rank)
                except ValueError:
                    print("Could not find %s in file." % (target_ltag))


    # Check whether the outputFile is empty
    if outputText == "srna_name;target_ltag;target_name;intarna_rank\n":
        sys.exit("No reasonable output found!")

    # write csv file
    csv_file = open(os.path.join(outputPath, benchID + "_" + outputfile), "w")
    csv_file.write(outputText)
    csv_file.close()

    print("Finished benchmarking: %s" % benchID)

if __name__ == "__main__":
   main(sys.argv[1:])