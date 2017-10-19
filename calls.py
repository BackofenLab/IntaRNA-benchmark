#!/usr/bin/python
# Author: Rick Gelhausen
import sys, getopt
import os.path
import time
from subprocess import Popen
from subprocess import PIPE

# help text
usage= "Call with: python3 calls.py -a1 <argument1> -a2 ..." \
       "The following arguments are available:\n" \
       "intaRNAPath (-i) : path where the intaRNA executable lies. Default: ../IntaRNA/src/bin . \n" \
       "fastaPath (-f)   : location where the folders containing the fasta files lie. Default: ./predictions .\n" \
       "arg (-a)         : command line arguments applied to the intaRNA query. \n" \
       "help (-h)        : print this usage. \n"

def main(argv):
    intaRNAPath = os.path.join("..", "IntaRNA", "src", "bin",)
    fastaFilePath = os.path.join(".", "predictions")
    commandLineArguments = ""
    outName = ""

    # commandline parsing
    try:
        opts, args = getopt.getopt(argv,"hi:f:o:a:",["ifile=","ffile=","ofile","arg="])
    except getopt.GetoptError:
        print("ERROR! Call <python3 calls.py -h> for help")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print(usage)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            intaRNAPath = arg
        elif opt in ("-f", "--ffile"):
            fastaFilePath = arg
        elif opt in ("-o", "--ofile"):
            outName = arg
        elif opt in ("-a", "--arg"):
            commandLineArguments = arg


    # get all relevant folder names
    directories = ([x[0] for x in os.walk(fastaFilePath)])[1:]
    directories.sort()

    # declare file names of target fasta files
    targetFastaB = "NC_000913_upfromstartpos_200_down_100.fa"
    targetFastaSTM = "NC_003197_upfromstartpos_200_down_100.fa"


    for dir in directories:
        # declaring file names of query fasta files
        srna_name = dir.split(os.path.sep)[-1]
        queryFastaB = srna_name + "_NC_000913.fasta"
        queryFastaSTM = srna_name + "_NC_003197.fasta"


        # IntaRNA call
        # Salmonella
        call = intaRNAPath + "IntaRNA" + " -q " + os.path.join(dir, queryFastaSTM) \
               + " -t " + os.path.join(fastaFilePath, targetFastaSTM) \
               + " --out " + os.path.join(dir, srna_name+"_NC_003197.csv") \
               + " --outMode=C " + commandLineArguments
        print(call)
        # record time of this call
        startCallb = time.time()
        with Popen(call, shell=True, stdout=PIPE) as process:
            print(process.stdout.read())
        endCallb = time.time()

        # Echoli
        call = intaRNAPath + "IntaRNA" + " -q " + os.path.join(dir, queryFastaB) \
                                       + " -t " + os.path.join(fastaFilePath, targetFastaB) \
                                       + " --out " + os.path.join(dir,srna_name+"_NC_000913.csv") \
                                       + " --outMode=C " + commandLineArguments
        print(call)
        # record time of this call
        startCallSTM = time.time()
        with Popen(call, shell=True, stdout=PIPE) as process:
            print(process.stdout.read())
        endCallSTM = time.time()



if __name__ == "__main__":
   main(sys.argv[1:])