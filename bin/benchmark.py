#!/usr/bin/env python3
# Author: Rick Gelhausen, adapted from perl script by Patrick Wright
import sys, argparse
import os.path
import pandas as pd
import glob

def main(argv):
    parser = argparse.ArgumentParser(description="Benchmark IntaRNA")
    parser.add_argument("-i", "--infile", action="store", dest="verified_interactions", default=os.path.join("..", "verified_interactions.csv")
                        , help= "location of the file containing the verified interactions.")
    parser.add_argument("-o", "--outfile", action="store", dest="outputfile", default=os.path.join(".", "benchmark.csv")
                        , help="path of the benchmark outputfile.")
    parser.add_argument("-p", "--callDirs", action="store", dest="directoryPath", default=os.path.join("..", "output")
                        , help="path to directory containing the output of the calls script. ")
    parser.add_argument("-c", "--callID", action="store", dest="callID", default=""
                        , help="a mandatory ID to differentiate between multiple calls of the script.")
    args = parser.parse_args()

    # Check whether a callID was given
    if args.callID == "":
        sys.exit("No callID was specified! Please specify a callID using -c <name> or --callID=<name>")

    # read verified interactions
    if os.path.exists(args.verified_interactions) == True:
        with open(args.verified_interactions) as data:
            tempHybrid = [line.strip() for line in data]
    else:
        sys.exit("Error: %s! File not found!" % (args.verified_interactions))

    # check whether the callID is valid (no file with that name exists)
    outputPath = os.path.join(args.directoryPath, args.callID, args.outputfile)
    if os.path.exists(outputPath):
        sys.exit("A file for this callID already exists! Exiting...")

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

    # Get all directories with needed files and sort them
    srna_files = [x for x in glob.glob(os.path.join(args.directoryPath, args.callID, "*.csv")) if x.split(os.path.sep)[-1].split("_")[0] in srnaList]
    srna_files.sort()

    # Check whether the needed files for the benchmarking exist
    if srna_files == []:
        sys.exit("Error!!! No files found for benchmarking ID %s" % args.callID)

    # Create a dictionary from the srna_files for better access
    srnaDict = dict()
    for srna in srnaList:
        for organism in organisms:
            if (srna, organism) in srnaDict:
                srnaDict[(srna, organism)].insert([x for x in srna_files if srna in x and organism in x])
            else:
                srnaDict[(srna, organism)] = [x for x in srna_files if srna in x and organism in x]

    outputText= "srna_name;target_ltag;target_name;%s_intarna_rank\n" % args.callID

    # determine the rank of intaRNA given the confirmed hybrids
    for srna_name in srnaList:
        for organism in organisms:
            if (srna_name, organism) in confirmed_hybrids:
                for confirmed_hybrid in confirmed_hybrids[(srna_name, organism)]:

                    for file in srnaDict[(srna_name, organism)]:
                        try:
                            df = pd.read_csv(file, sep=";", header=0)
                        except pd.errors.ParserError as err:
                            errorMessage = "%s      in file %s \n\nPlease contact the IntaRNA development team." % (err, file)
                            sys.exit(errorMessage)
                        df = df.sort_values("E")

                        target_ltag = confirmed_hybrid[0]
                        target_name = confirmed_hybrid[1]

                        try:
                            # Uses first column, maybe use id1 instead
                            # Adding 1 because df.ix[:,0] ignores the header and list starts with 0. Adding 1 fixes it.
                            intaRNA_rank = list(df.ix[:,0]).index(target_ltag) + 1

                            outputText += "%s;%s;%s;%s\n" % (srna_name, target_ltag, target_name, intaRNA_rank)
                        except ValueError:
                            outputText += "%s;%s;%s;%s\n" % (srna_name, target_ltag, target_name, 99999)

    # Check whether the outputFile is empty
    if outputText == "srna_name;target_ltag;target_name;intarna_rank\n":
        sys.exit("No reasonable output found!")

    # write csv file
    csv_file = open(os.path.join(outputPath), "w")
    csv_file.write(outputText)
    csv_file.close()

    print("Finished benchmarking: %s" % args.callID)

if __name__ == "__main__":
   main(sys.argv[1:])
