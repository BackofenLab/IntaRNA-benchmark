#!/usr/bin/env python3
# Author: Rick Gelhausen

import sys, argparse
import os
import pandas as pd
import matplotlib
import re
import operator

matplotlib.use('Agg')
from itertools import cycle
import matplotlib.pyplot as plt

########################################################################################################################
#                                                                                                                      #
#                                   Plot contents of a given benchmark.csv file                                        #
#                                                                                                                      #
#                                                                                                                      #
########################################################################################################################

# List of easily differentiable color codes
colorList = ['#f032e6', '#808080', '#000080', '#808000', '#aaffc3', '#800000', '#aa6e28', '#e6beff', '#008080',
             '#fabebe', '#d2f53c', '#46f0f0', '#911eb4', '#f58231', '#0082c8', '#ffe119', '#3cb44b']

lineList = ["--", "-"]

# Differentiate between ints and other chars/strings
def isInt(i):
    try:
        return int(i)
    except:
        return i

# Split strings into lists of strings and numbers
def alphanumeric_key(s):
    return [isInt(c) for c in re.split('([0-9]+)', s)]

# Sort the way a human expects it
def human_sort(l):
    l.sort(key=alphanumeric_key)


def main(argv):
    parser = argparse.ArgumentParser(description="Script for plotting the benchmark results")
    parser.add_argument("-i", "--ifile", action="store", dest="benchmarkFile", default=os.path.join("")
                        , help="Mandatory benchmark file to be used for plotting.")
    parser.add_argument("-o", "--ofile", action="store", dest="outFile", default=os.path.join("..", "output", "intaRNA2_benchmark.pdf")
                        , help="the path of the outputFilePath.")
    parser.add_argument("-s", "--sep", action="store", dest="separator", default=";"
                        , help="specify the separator used by the benchmark file.")
    parser.add_argument("-e", "--end", action="store", dest="end", default=200, type=int
                        , help="The amount of predictions considered for plotting.")
    parser.add_argument("-x", "--xlim", action="store", dest="xlim", default=""
                        , help="specify a xlim for the output.")
    parser.add_argument("-y", "--ylim", action="store", dest="ylim", default=""
                        , help="specify a ylim for the output.")
    parser.add_argument("-f", "--fixed", action="store", dest="fixedID", default=""
                        , help="callID that gets a fixed color (red)")
    parser.add_argument("-t", "--title", action="store", dest="title", default=""
                        , help="the title of the plot.")
    parser.add_argument("--lines", action="store_true", dest="lines", default=False
                        , help="use different line types, evenly distributed")
    parser.add_argument("-p", "--plotType", action="store", dest="plotType", default="roc"
                        , help="Decide whether to use ROC or Violin plots.")
    args = parser.parse_args()

    if args.benchmarkFile == "":
        sys.exit("Please specify a benchmark.csv with: python3 plot_performance.py -i <filename.csv> !")


    if os.path.exists(args.benchmarkFile):
        benchDF = pd.read_csv(args.benchmarkFile, sep=args.separator, header=0)
        prefix = ["srna_name", "target_ltag", "target_name"]
        intarnaIDs = [x.replace("_intarna_rank", "") for x in benchDF.columns if x not in prefix]
        print(intarnaIDs)


        rankDictionary = dict()
        # Init dictionary
        for entry in intarnaIDs:
            rankDictionary[entry] = []

        # Get the ranks for each callID
        for i in range(1, args.end):
            for id in intarnaIDs:
                rankDictionary[id].append(len(benchDF[benchDF[id+"_intarna_rank"] <= i]))

        # plot type roc
        if args.plotType == "roc":
            # Plot the data
            if bool(rankDictionary):
                # Plot the data
                keys = list(rankDictionary.keys())
                human_sort(keys)

                linecycler = cycle(lineList)
                # Plot all wanted callIDs
                for key in keys:
                    # If fixedID is given plot it in red
                    if args.fixedID != "":
                        if key == args.fixedID:
                            plt.plot(rankDictionary[args.fixedID], label=args.fixedID, color="red", zorder=30)
                            continue

                    # Plot rest
                    if not args.lines:
                        if (len(keys) > 17):
                            plt.plot(rankDictionary[key], label=key)
                        else:
                            plt.plot(rankDictionary[key], label=key, color=colorList.pop())
                    else:
                        if (len(keys) > 17):
                            plt.plot(rankDictionary[key], label=key, linestyle=next(linecycler))
                        else:
                            plt.plot(rankDictionary[key], label=key, color=colorList.pop(), linestyle=next(linecycler))

                # Set the title, if given
                if args.title != "":
                    plt.title(args.title)

                # Create the legend
                plt.legend(loc="lower right")
                plt.xlabel("# Target predictions per sRNA")
                plt.ylabel("# True positive")

                # Handle user input for the x and y limits
                if args.xlim != "" and "/" in args.xlim:
                    plt.xlim(int(args.xlim.split("/")[0]), int(args.xlim.split("/")[1]))
                if args.ylim != "" and "/" in args.ylim:
                    plt.ylim(int(args.ylim.split("/")[0]), int(args.ylim.split("/")[1]))

                plt.savefig(args.outFile)
                plt.close()

        elif args.plotType == "violin":

            if args.fixedID == "":
                sys.exit("Please provide a reference curve with --fixedID=<callID> to compute the violin plot.")

            refData = rankDictionary[args.fixedID]
            rankDictionary.pop(args.fixedID, None)

            keys = list(rankDictionary.keys())
            human_sort(keys)

            data = []
            for key in keys:
                data.append(list(map(operator.sub, rankDictionary[key], refData)))

            parts = plt.violinplot(data, showextrema=True, showmeans=True, showmedians=True)
            for idx, pc in enumerate(parts['bodies']):
                pc.set_facecolor(colorList[::-1][idx])
                pc.set_edgecolor('black')
                pc.set_alpha(1)

            # Set the title, if given
            if args.title != "":
                plt.title(args.title)

            # Create the legend
            # plt.legend(loc="lower right")
            # plt.xlabel("# Target predictions per sRNA")
            # plt.ylabel("# True positive")

            plt.savefig(args.outFile)
            plt.close()
        else:
            sys.exit("Please specify a plot type: -p<'roc' / 'violin'>")

    else:
        sys.exit("Could not find %s!" % args.benchmarkFile)

if __name__ == "__main__":
    main(sys.argv[1:])
