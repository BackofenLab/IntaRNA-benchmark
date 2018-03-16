#!/usr/bin/env python3
# Author: Rick Gelhausen

import sys, argparse
import os
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

########################################################################################################################
#                                                                                                                      #
#                                   Plot contents of a given benchmark.csv file                                        #
#                                                                                                                      #
#                                                                                                                      #
########################################################################################################################

def main(argv):
    parser = argparse.ArgumentParser(description="Script for plotting the benchmark results")
    parser.add_argument("-i", "--ifile", action="store", dest="benchmarkFile", default=os.path.join("")
                        , help="Mandatory benchmark file to be used for plotting.")
    parser.add_argument("-o", "--ofile", action="store", dest="outFile", default=os.path.join("", "output", "intaRNA2_benchmark.pdf")
                        , help="the path of the outputFilePath.")
    parser.add_argument("-s", "--sep", action="store", dest="separator", default=";"
                        , help="specify the separator used by the benchmark file.")
    parser.add_argument("-e", "--end", action="store", dest="end", default=200
                        , help="The amount of predictions considered for plotting.")
    parser.add_argument("-x", "--xlim", action="store", dest="xlim", default=""
                        , help="specify a xlim for the output.")
    parser.add_argument("-y", "--ylim", action="store", dest="ylim", default=""
                        , help="specify a ylim for the output.")
    args = parser.parse_args()

    if args.benchmarkFile == "":
        sys.exit("Please specify a benchmark.csv with: python3 plot_performance.py -i <filename.csv> !")


    if os.path.exists(args.benchmarkFile):
        benchDF = pd.read_csv(args.benchmarkFile, sep=args.separator, header=0)
        prefix = ["srna_name", "target_ltag", "target_name"]
        intarnaIDs = [x for x in benchDF.columns if x not in prefix]
        print(intarnaIDs)

        rankDictionary = dict()
        # Init dictionary
        for entry in intarnaIDs:
            rankDictionary[entry] = []

        # Get the ranks for each callID
        for i in range(1, args.end):
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

            if args.xlim != "" and "/" in args.xlim:
                plt.xlim(int(args.xlim.split("/")[0]), int(args.xlim.split("/")[1]))
            if args.ylim != "" and "/" in args.ylim:
                plt.ylim(int(args.ylim.split("/")[0]), int(args.ylim.split("/")[1]))

            plt.savefig(args.outFile)
            plt.close()

    else:
        sys.exit("Could not find %s!" % args.benchmarkFile)

if __name__ == "__main__":
    main(sys.argv[1:])
