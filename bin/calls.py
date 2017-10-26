#!/usr/bin/python
# Author: Rick Gelhausen
import sys, getopt
import os
import glob
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
       "--ffile  (-f) : location where the folders containing the fasta files lie. Default: ./input .\n" \
       "--ofile  (-o) : output folder\n" \
       "--arg    (-a) : command line arguments applied to the intaRNA query. \n" \
       "--callID (-c) : mandatory callID used to identify call. \n" \
       "--help   (-h) : print this usage. \n"


# Run a subprocess with the given call
def runSubprocess(call_, outputPath):
    with Popen(call_, shell=True, stdout=PIPE) as process:
        sys.stdout = open(outputPath, "w")
        print(str(process.stdout.read(),"utf-8"))
        sys.stdout = sys.__stdout__
        ru = os.wait4(process.pid, 0)[2]
        # Return time and memory usage
    return ru.ru_utime, ru.ru_maxrss


def main(argv):
    intaRNAPath = os.path.join("..", "..", "IntaRNA", "src", "bin", "")
    outputPath = os.path.join("..", "output")
    fastaFilePath = os.path.join("..", "input")
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
            fastaFilePath = arg
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
    organisms = [x.split(os.path.sep)[-1] for x in glob.glob(os.path.join(fastaFilePath,"*"))]
    if organisms == []:
        sys.exit("Input folder is empty!")

    # Filepaths
    callLogFilePath = os.path.join(outputPath, callID, "calls.txt")
    timeLogFilePath = os.path.join(outputPath, callID, "runTime.csv")
    memoryLogFilePath = os.path.join(outputPath, callID, "memoryUsage.csv")

    for organism in organisms:
        # check if query and target folder exist
        if not os.path.exists(os.path.join(fastaFilePath, organism, "query")):
            sys.exit("Error!!! Could not find query path for %s!" % organism)
        if not os.path.exists(os.path.join(fastaFilePath, organism, "target")):
            sys.exit("Error!!! Could not find target path for %s!" % organism)

        fastaFileEndings = [".fasta", ".fa"]

        srna_files = []
        target_files = []
        for ending in fastaFileEndings:
            srna_files.extend(glob.glob(os.path.join(fastaFilePath, organism, "query", "*" + ending)))
            target_files.extend(glob.glob(os.path.join(fastaFilePath, organism, "target", "*" + ending)))

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
            header = "target_name;Organism"
            timeLine = "%s;%s" % (target_name, organism)
            memoryLine = "%s;%s" % (target_name, organism)

            for srna_file in srna_files:
                srna_name = srna_file.split(os.path.sep)[-1].split("_")[0]
                header += ";%s" % srna_name

                # Adding column
                timeLine += ";"
                memoryLine += ";"

                # IntaRNA call
                call = intaRNAPath + "IntaRNA" + " -q " + srna_file \
                                               + " -t " + target_file \
                                               + " --out=stdout --outMode=C "  \
                                               + commandLineArguments
                print(call)
                print("%s\n" % call, file=open(callLogFilePath,"a"))

                # Outputfilepath
                out = os.path.join(outputPath, callID, srna_name + "_" + target_name + ".csv")

                # record time in seconds and memory in KB of this call
                timeCall, maxMemory = runSubprocess(call, out)

                # Time in seconds
                timeLine += "%.2f" % timeCall
                # Convert to megabyte (MB)
                memoryLine += "%.2f" % (float(maxMemory) / 1000)

            # print header if file is empty
            if not os.path.exists(timeLogFilePath):
                print(header, file=open(timeLogFilePath, "a"))
            if not os.path.exists(memoryLogFilePath):
                print(header, file=open(memoryLogFilePath, "a"))
            print(timeLine, file=open(timeLogFilePath, "a"))
            print(memoryLine, file=open(memoryLogFilePath, "a"))



    # Start benchmarking for this callID
    callBenchmark = "python3 benchmark.py -b %s" % (callID)
    with Popen(callBenchmark, shell=True, stdout=PIPE) as process:
        print(str(process.stdout.read(), "utf-8"))

if __name__ == "__main__":
   main(sys.argv[1:])
