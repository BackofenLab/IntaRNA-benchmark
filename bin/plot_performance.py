#!/usr/bin/python
# Author: Rick Gelhausen

import sys, getopt
import os
import pandas as pd
import matplotlib.pyplot as plt


########################################################################################################################
#                                                                                                                      #
#                                   Plot contents of a given benchmark.csv file                                        #
#                                                                                                                      #
#                                                                                                                      #
########################################################################################################################

# help text
usage = "Call with: python3 plot_performance.py -a1 <argument1> -a2 ..." \
        "The following arguments are available:\n" \
        "--ifile  (-i) : Benchmark file to be used for plotting. MANDATORY . \n" \
        "--ofile  (-o) : outputFilePath. Default: ../output/intaRNA2_benchmark.pdf \n" \
        "--sep    (-s) : specify the separator used by the benchmark file. Default ';'\n" \
        "--end    (-e) : endpoint of the run. Default: 200 \n" \
        "--xlim   (-x) : specify a xlim for the output. x_start/x_end .\n" \
        "--ylim   (-y) : specify a ylim for the output. y_start/y_end .\n" \
        "--help   (-h) : print this usage. \n"


def main(argv):
    benchmarkFile = ""
    outFile = os.path.join("..", "output", "intaRNA2_benchmark.pdf")
    separator = ";"
    end = 200
    xlim = ""
    ylim = ""
    # commandline parsing
    try:
        opts, args = getopt.getopt(argv, "hi:o:s:e:x:y:", ["ifile=","ofile=", "sep=", "end="])
    except getopt.GetoptError:
        print("ERROR! Call <python3 plot_performance.py -h> for help")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            benchmarkFile = arg
        elif opt in ("-o", "--ofile"):
            outFile = arg
        elif opt in ("-s", "--sep"):
            separator = arg
        elif opt in ("-e", "--end"):
            end = arg
        elif opt in ("-x", "--xlim"):
            xlim = arg
        elif opt in ("-y", "--ylim"):
            ylim = arg

    if benchmarkFile == "":
        sys.exit("Please specify a benchmark.csv with: python3 plot_performance.py -i <filename.csv> !")


    if os.path.exists(benchmarkFile):
        benchDF = pd.read_csv(benchmarkFile, sep=separator, header=0)
        prefix = ["srna_name", "target_ltag", "target_name"]
        intarnaIDs = [x for x in benchDF.columns if x not in prefix]
        print(intarnaIDs)

        rankDictionary = dict()
        # Init dictionary
        for entry in intarnaIDs:
            rankDictionary[entry] = []

        # Get the ranks for each callID
        for i in range(1, end):
            for id in intarnaIDs:
                rankDictionary[id].append(len(benchDF[benchDF[id] <= i]))

        # Plot the data
        if bool(rankDictionary):
            # Plot the data
            keys = rankDictionary.keys()
            for key in keys:
                plt.plot(rankDictionary[key], label=key)

            plt.legend(loc="lower right")
            plt.xlabel("# Target predictions per sRNA")
            plt.ylabel("# True positive")

            if xlim != "" and "/" in xlim:
                plt.xlim(int(xlim.split("/")[0]), int(xlim.split("/")[1]))
            if ylim != "" and "/" in ylim:
                plt.ylim(int(ylim.split("/")[0]), int(ylim.split("/")[1]))

            plt.savefig(outFile)
            plt.close()

    else:
        sys.exit("Could not find %s!" % benchmarkFile)

if __name__ == "__main__":
    main(sys.argv[1:])
