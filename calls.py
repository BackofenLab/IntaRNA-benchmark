#!/usr/bin/python
# Author: Rick Gelhausen
import sys, getopt
import os.path
import time
from subprocess import Popen
from subprocess import PIPE

########################################################################################################################
#                                                                                                                      #
#            This script calls intaRNA with custom parameters on a set of sRNA queries and mRNA targets.               #
#            The script requires a callID to identify the call and to allow parallel runs of the script.               #
#                   The benchmark.py script is called after building the result files.                                 #
#                                                                                                                      #
########################################################################################################################

# help text
usage= "Call with: python3 calls.py -a1 <argument1> -a2 ..." \
       "The following arguments are available:\n" \
       "--ifile  (-i) : path where the intaRNA executable lies. Default: ../IntaRNA/src/bin . \n" \
       "--ffile  (-f) : location where the folders containing the fasta files lie. Default: ./predictions .\n" \
       "--arg    (-a) : command line arguments applied to the intaRNA query. \n" \
       "--callID (-c) : mandatory callID used to identify call. \n" \
       "--help   (-h) : print this usage. \n"

def main(argv):
    intaRNAPath = os.path.join("..", "IntaRNA", "src", "bin","")
    fastaFilePath = os.path.join(".", "predictions")
    commandLineArguments = ""
    callID = ""

    # commandline parsing
    try:
        opts, args = getopt.getopt(argv,"hi:f:a:c:",["ifile=","ffile=","arg=","callID="])
    except getopt.GetoptError:
        print("ERROR! Call <python3 calls.py -h> for help")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            intaRNAPath = arg
        elif opt in ("-f", "--ffile"):
            fastaFilePath = arg
        elif opt in ("-a", "--arg"):
            commandLineArguments = arg
        elif opt in ("-c", "--callID"):
            callID = arg

    # Check whether a callID was given
    if callID == "":
        sys.exit("No callID was specified! Please specify a callID using -c <name> or --callID=<name>")

    # get all relevant folder names
    directories = ([x[0] for x in os.walk(fastaFilePath)])[1:]
    directories.sort()

    # declare file names of target fasta files
    targetFastaB = "NC_000913_upfromstartpos_200_down_100.fa"
    targetFastaSTM = "NC_003197_upfromstartpos_200_down_100.fa"

    # Logging files
    callLogFilePath = os.path.join(".", "logs", callID + "_calls.txt")
    timeLogFilePath = os.path.join(".", "benchmarks", callID + "_runTimes.csv")

    # open file
    callLogFile = open(callLogFilePath, "w")
    # Variables to create the timeLog table
    header = "callID;Organism"
    stmLine = "%s;Salmonella" % callID
    bLine = "%s;E.coli" % callID
    for dir in directories:
        # declaring file names of query fasta files
        srna_name = dir.split(os.path.sep)[-1]
        queryFastaB = os.path.join(dir, srna_name + "_NC_000913.fasta")
        queryFastaSTM = os.path.join(dir, srna_name + "_NC_003197.fasta")

        # outputFile paths
        outSTM = os.path.join(dir, callID + "_" + srna_name + "_NC_003197.csv")
        outB = os.path.join(dir, callID + "_" + srna_name + "_NC_000913.csv")

        # Adding column
        header += ";%s" % srna_name
        stmLine += ";"
        bLine += ";"
        # check whether the outputfiles already exist
        if not os.path.exists(outSTM):
            if os.path.exists(queryFastaSTM):
                # IntaRNA call
                # Salmonella
                call = intaRNAPath + "IntaRNA" + " -q " + queryFastaSTM \
                                               + " -t " + os.path.join(fastaFilePath, targetFastaSTM) \
                                               + " --out " + outSTM + " --outMode=C "  \
                                               + commandLineArguments
                print(call)
                print("%s\n" % call, file=callLogFile)
                # record time of this call
                startCallSTM = time.time()
                with Popen(call, shell=True, stdout=PIPE) as process:
                    print(process.stdout.read())
                endCallSTM = time.time()
                timeCallSTM = endCallSTM - startCallSTM
                stmLine += "%s" % timeCallSTM
            else:
                print("%s missing!" % queryFastaSTM)
        else:
            print("%s already exists!" % (outSTM.split(os.path.sep)[-1]))

        if not os.path.exists(outB):
            if os.path.exists(queryFastaB):
                # Echoli
                call = intaRNAPath + "IntaRNA" + " -q " + queryFastaB \
                                               + " -t " + os.path.join(fastaFilePath, targetFastaB) \
                                               + " --out " + outB + " --outMode=C " \
                                               + commandLineArguments
                print(call)
                print("%s\n" % call, file=callLogFile)
                # record time of this call
                startCallb = time.time()
                with Popen(call, shell=True, stdout=PIPE) as process:
                    print(process.stdout.read())
                endCallb = time.time()
                timeCallb = endCallb - startCallb
                bLine +="%s" % timeCallb
            else:
                print("%s missing!" % queryFastaB)
        else:
            print("%s already exists!" % (outB.split(os.path.sep)[-1]))

    # close files
    callLogFile.close()

    # Write timeLogFile
    csv_file = open(timeLogFilePath, "w")
    csv_file.write("%s\n%s\n%s\n" % (header, stmLine, bLine))
    csv_file.close()

    # Start benchmarking for this callID
    callBenchmark = "python3 benchmark.py -b %s" % (callID)
    with Popen(callBenchmark, shell=True, stdout=PIPE) as process:
        print(process.stdout.read())

if __name__ == "__main__":
   main(sys.argv[1:])
