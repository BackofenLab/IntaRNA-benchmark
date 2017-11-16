#!/usr/bin/env python
# NOTE: python-2 script
# Author: Rick Gelhausen
import sys, getopt
import os
import glob
import shlex
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
       "--ffile  (-f) : input folder containing the faster files required. Default: ./input .\n" \
       "--ofile  (-o) : output folder.\n" \
       "--arg    (-a) : command line arguments applied to the intaRNA query. \n" \
       "--callID (-c) : mandatory callID used to identify call. \n" \
       "--help   (-h) : print this usage. \n"


# Run a subprocess with the given call and provide process statistics
def runSubprocess(callArgs):
    # trigger call as subprocess
    process = Popen(callArgs)
    # wait for call to finish and get statistics
    ru = os.wait4(process.pid, 0)[2]
    # Return time and memory usage
    return ru.ru_utime, ru.ru_maxrss

def main(argv):
    intaRNAPath = os.path.join("..", "..", "IntaRNA", "src", "bin", "")
    outputPath = os.path.join("..", "output")
    inputPath = os.path.join("..", "input")
    commandLineArguments = ""
    callID = ""

    # commandline parsing
    try:
        opts, args = getopt.getopt(argv,"hi:o:f:a:c:",["ifile=", "ofile=", "ffile=", "arg=", "callID="])
    except getopt.GetoptError:
        print("ERROR! Call <python3 calls.py -h> for help")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            intaRNAPath = arg
        elif opt in ("-o", "--ofile"):
            outputPath = arg
        elif opt in ("-f", "--ffile"):
            inputPath = arg
        elif opt in ("-a", "--arg"):
            commandLineArguments = arg
        elif opt in ("-c", "--callID"):
            callID = arg

    # Check whether a callID was given
    if callID == "":
        sys.exit("No callID was specified! Please specify a callID using -c <name> or --callID=<name>")

    # Check whether intaRNA path exists
    if not os.path.exists(intaRNAPath):
        sys.exit("Error!!! IntaRNA filePath does not exist! Please specify it using python3 calls.py -i <intaRNApath>!")

    # Create outputFolder for this callID if not existing
    if not os.path.exists(os.path.join(outputPath, callID)):
        os.makedirs(os.path.join(outputPath, callID))
    else:
        sys.exit("Error!!! A directory for callID %s already exists!" % callID)

    # Organisms
    organisms = [x.split(os.path.sep)[-1] for x in glob.glob(os.path.join(inputPath,"*")) if os.path.isdir(x)]
    if organisms == []:
        sys.exit("Input folder is empty!")

    # Filepaths
    callLogFilePath = os.path.join(outputPath, callID, "calls.txt")
    timeLogFilePath = os.path.join(outputPath, callID, "runTime.csv")
    memoryLogFilePath = os.path.join(outputPath, callID, "memoryUsage.csv")

    for organism in organisms:
        # check if query and target folder exist
        if not os.path.exists(os.path.join(inputPath, organism, "query")):
            sys.exit("Error!!! Could not find query path for %s!" % organism)
        if not os.path.exists(os.path.join(inputPath, organism, "target")):
            sys.exit("Error!!! Could not find target path for %s!" % organism)

        fastaFileEndings = [".fasta", ".fa"]

        srna_files = []
        target_files = []
        for ending in fastaFileEndings:
            srna_files.extend(glob.glob(os.path.join(inputPath, organism, "query", "*" + ending)))
            target_files.extend(glob.glob(os.path.join(inputPath, organism, "target", "*" + ending)))

        # Sort input
        srna_files.sort()
        target_files.sort()

        # Check whether input exists
        if len(srna_files) == 0:
            sys.exit("Error!!! No srna fasta files found in query folder!")
        if len(target_files) == 0:
            sys.exit("Error!!! No target fasta files found in target folder!")


        for target_file in target_files:
            target_name = target_file.split(os.path.sep)[-1].split(".")[0]
            # Variables to create the timeLog table
            header = "callID;target_name;Organism"
            timeLine = "%s;%s;%s" % (callID, target_name, organism)
            memoryLine = "%s;%s;%s" % (callID, target_name, organism)

            for srna_file in srna_files:
                srna_name = srna_file.split(os.path.sep)[-1].split("_")[0]
                header += ";%s" % srna_name

                # Adding column
                timeLine += ";"
                memoryLine += ";"

                # Outputfilepath
                out = os.path.join(outputPath, callID, srna_name + "_" + target_name + ".csv")

                # IntaRNA call
                call = intaRNAPath +"/"+ "IntaRNA" + " -q " + srna_file \
                                               + " -t " + target_file \
                                               + " --out " + out \
                                               + " --outMode C"  \
                                               + " " + commandLineArguments

                print(call)
                # split call for subprocess creation
                callArgs = shlex.split(call)

                with open(callLogFilePath, 'a') as callLogFile:
                    print >>callLogFile, "%s\n" % call

                timeCall, maxMemory = runSubprocess(callArgs)

                # Time in seconds
                timeLine += "%.2f" % timeCall
                # Convert to megabyte (MB)
                memoryLine += "%.2f" % (float(maxMemory) / 1000)

            # print header if file is empty
            if not os.path.exists(timeLogFilePath):
                with open(timeLogFilePath, 'a') as timeLogFile:
                    print >>timeLogFile, header
            if not os.path.exists(memoryLogFilePath):
                with open(memoryLogFilePath, 'a') as memoryLogFile:
                    print >>memoryLogFile, header
            with open(timeLogFilePath, 'a') as timeLogFile:
                print >>timeLogFile, timeLine
            with open(memoryLogFilePath, 'a') as memoryLogFile:
                print >>memoryLogFile, memoryLine



    # Start benchmarking for this callID
    callBenchmark = "python3 benchmark.py -b %s" % (callID)
    with Popen(callBenchmark, shell=True, stdout=PIPE) as process:
        print(str(process.stdout.read(), "utf-8"))

if __name__ == "__main__":
   main(sys.argv[1:])
