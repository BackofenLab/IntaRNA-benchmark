#!/usr/bin/env python3
# NOTE: python > 3.2 needed
# Author: Rick Gelhausen
import sys, argparse
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


# Run a subprocess with the given call and provide process statistics
def runSubprocess(callArgs):
    with Popen(callArgs) as process:
        # wait for call to finish and get statistics
        ru = os.wait4(process.pid, 0)[2]
    # Return time and memory usage
    return ru.ru_utime, ru.ru_maxrss


def main(argv):
    fastaFileEndings = [".fasta", ".fa"]

    parser = argparse.ArgumentParser(
        description="Call script for benchmarking IntaRNA. IntaRNA commandLineArguments can be added at the end of the call."
                    "python3 calls.py -c <callID>  --<IntaRNA arguments>")
    parser.add_argument("-b", "--intaRNAbinary", action="store", dest="intaRNAbinary",
                        default=os.path.join("..", "..", "IntaRNA", "src", "bin", "IntaRNA")
                        , help="the location of the intaRNA executable. Default: ../../IntaRNA/src/bin .")
    parser.add_argument("-i", "--infile", action="store", dest="inputPath", default=os.path.join("..", "input")
                        , help="input folder containing the required fasta files. Default: ./input")
    parser.add_argument("-o", "--outfile", action="store", dest="outputPath", default=os.path.join("..", "output")
                        , help="location of the output folder.")
    parser.add_argument("-c", "--callID", action="store", dest="callID", default=""
                        , help="a mandatory ID to differentiate between multiple calls of the script.")
    parser.add_argument("-n", "--callsOnly", action="store_true", dest="noJobStart", default=False
                        , help="only generate the calls and store in the logfile but not start processes.")
    parser.add_argument("-e", "--withTargetED", action="store_true", dest="enabledTargetED", default=False
                        , help="Target ED-values will be stored in a data folder and reused for all further computations.")

    #   Warning  Prefix matching rules apply to parse_known_args().
    #  The parser may consume an option even if it’s just a prefix of one of its known options, instead of leaving it in the remaining arguments list.
    args, cmdLineArgs = parser.parse_known_args()

    # Get the path of the executables in order to determine the location of other scripts
    executablePath = os.path.dirname(__file__)

    # Remaining argument options are used for IntaRNA
    cmdLineArgs = " ".join(cmdLineArgs)

    # Check whether a callID was given
    if args.callID == "":
        sys.exit("No callID was specified! Please specify a callID using -c <name> or --callID=<name>")

    # Check whether intaRNA path exists
    if not os.path.exists(args.intaRNAbinary):
        sys.exit("Error!!! IntaRNA filePath does not exist! Please specify it using -b <intaRNAbinary>!")

    # Create outputFolder for this callID if not existing
    if not os.path.exists(os.path.join(args.outputPath, args.callID)):
        os.makedirs(os.path.join(args.outputPath, args.callID))
    else:
        sys.exit("Error!!! A directory for callID %s already exists!" % args.callID)

    # Organisms
    organisms = [x.split(os.path.sep)[-1] for x in glob.glob(os.path.join(args.inputPath, "*")) if os.path.isdir(x)]
    if organisms == []:
        sys.exit("Input folder is empty!")


    # Compute target ED-value files for each organism and option enabled (if not existant)
    if (args.enabledTargetED):
        print("Preprocessing target ED-values!!")
        for organism in organisms:
            target_files = []
            for ending in fastaFileEndings:
                target_files.extend(glob.glob(os.path.join(args.inputPath, organism, "target", "*" + ending)))
            target_files.sort()

            for target in target_files:
                target_name = os.path.basename(os.path.splitext(target)[0])
                edValueFolder = os.path.join("..", "ED-values", organism, target_name)
                if not os.path.exists(edValueFolder):
                    os.makedirs(edValueFolder)
                    call = args.intaRNAbinary + " -q " + "AAAAAAAA" \
                                              + " -t " + target + " --noSeed" \
                                              + " -n 0 --out=/dev/null" \
                                              + " --out=tAcc:" + os.path.join(edValueFolder, "intarna.target.ed")

                    # if user enables threading, also add it to the precomputation of target ED values
                    if "threads " in cmdLineArgs:
                        call += " --threads " + cmdLineArgs.split("threads ")[-1].split(" ")[0]
                    elif "threads=" in cmdLineArgs:
                        call += " --threads=" + cmdLineArgs.split("threads=")[-1].split(" ")[0]

                    # call
                    callArgs = shlex.split(call, posix=False)
                    runSubprocess(callArgs)

        print("Preprocessing completed!")

    # Filepaths
    callLogFilePath = os.path.join(args.outputPath, args.callID, "calls.txt")
    timeLogFilePath = os.path.join(args.outputPath, args.callID, "runTime.csv")
    memoryLogFilePath = os.path.join(args.outputPath, args.callID, "memoryUsage.csv")

    for organism in organisms:
        # check if query and target folder exist
        if not os.path.exists(os.path.join(args.inputPath, organism, "query")):
            sys.exit("Error!!! Could not find query path for %s!" % organism)
        if not os.path.exists(os.path.join(args.inputPath, organism, "target")):
            sys.exit("Error!!! Could not find target path for %s!" % organism)


        srna_files = []
        target_files = []
        for ending in fastaFileEndings:
            srna_files.extend(glob.glob(os.path.join(args.inputPath, organism, "query", "*" + ending)))
            target_files.extend(glob.glob(os.path.join(args.inputPath, organism, "target", "*" + ending)))

        # Sort input
        srna_files.sort()
        target_files.sort()

        # Check whether input exists
        if len(srna_files) == 0:
            sys.exit("Error!!! No srna fasta files found in query folder!")
        if len(target_files) == 0:
            sys.exit("Error!!! No target fasta files found in target folder!")

        for target_file in target_files:
            target_name = os.path.basename(os.path.splitext(target_file)[0])
            # Variables to create the timeLog table
            header = "callID;target_name;Organism"
            timeLine = "%s;%s;%s" % (args.callID, target_name, organism)
            memoryLine = "%s;%s;%s" % (args.callID, target_name, organism)

            for srna_file in srna_files:
                srna_name = srna_file.split(os.path.sep)[-1].split("_")[0]
                header += ";%s" % srna_name

                # Outputfilepath
                out = os.path.join(args.outputPath, args.callID, srna_name + "_" + target_name + ".csv")

                # IntaRNA call
                call = args.intaRNAbinary + " -q " + srna_file \
                                          + " -t " + target_file \
                                          + " --out " + out \
                                          + " --outMode C " \
                                          + cmdLineArgs

                if (args.enabledTargetED):
                    call += " --tAcc=E --tAccFile=" \
                            + os.path.join("..", "ED-values", organism, target_name, "intarna.target.ed") \
                            + " --tIntLenMax 150"

                print(call, file=open(callLogFilePath, "a"))

                if not args.noJobStart:
                    # split call for subprocess creation
                    callArgs = shlex.split(call, posix=False)
                    # do call and get process information
                    timeCall, maxMemory = runSubprocess(callArgs)
                    # store process information
                    # Time in seconds
                    timeLine += ";%.2f" % timeCall
                    # Convert to megabyte (MB)
                    memoryLine += ";%.2f" % (float(maxMemory) / 1000)
                else:
                    # store that process information not available (NA)
                    timeLine += ";NA"
                    memoryLine += ";NA"

            if not os.path.exists(timeLogFilePath):
                # print header if file is empty
                print(header, file=open(timeLogFilePath, "a"))
            print(timeLine, file=open(timeLogFilePath, "a"))

            if not os.path.exists(memoryLogFilePath):
                # print header if file is empty
                print(header, file=open(memoryLogFilePath, "a"))
            print(memoryLine, file=open(memoryLogFilePath, "a"))

    if not args.noJobStart:
        # Start benchmarking for this callID
        callBenchmark = "python3 " + os.path.join(executablePath, benchmark.py) + " -c %s" % (args.callID)
        with Popen(shlex.split(callBenchmark, posix=False), stdout=PIPE) as process:
            print(str(process.stdout.read(), "utf-8"))


if __name__ == "__main__":
    main(sys.argv[1:])
