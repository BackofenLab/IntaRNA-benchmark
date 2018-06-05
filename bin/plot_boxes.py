#!/usr/bin/env python3
# Author: Rick Gelhausen

import sys, argparse
import os
import re
import operator

import pandas as pd
import numpy as np

from itertools import cycle
import matplotlib.pyplot as plt
import seaborn as sns

########################################################################################################################
#                                                                                                                      #
#                                   Plot contents of a given benchmark.csv file                                        #
#                                                                                                                      #
#                                                                                                                      #
########################################################################################################################

# List of easily differentiable color codes
colorList = ['#f032e6', '#808080', '#000080', '#808000', '#aaffc3', '#ffe119', '#800000', '#aa6e28', '#e6beff', '#008080',
             '#fabebe', '#d2f53c', '#46f0f0', '#911eb4', '#f58231', '#0082c8', '#3cb44b']

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

# set axis
def set_axis_style(ax, labels):
    ax.get_xaxis().set_tick_params(direction='out')
    # ax.xaxis.set_ticks_position('bottom')
    ax.set_xticks(np.arange(1, len(labels) + 1))
    ax.set_xticklabels(labels, fontsize=12)
    #ax.set_xlim(0.25, len(labels) + 0.75)

def main(argv):
    parser = argparse.ArgumentParser(description="Script for plotting the benchmark results")
    parser.add_argument("-i", "--ifile", action="store", dest="benchmarkFile", required=True
                        , help="benchmark file to be used for plotting.")
    parser.add_argument("-o", "--ofile", action="store", dest="outFile", required=True
                        , help="the path of the output pdf.")
    parser.add_argument("-f", "--fixed", action="store", dest="fixedID", required=True
                        , help="callID that gets a fixed color (red)")
    parser.add_argument("-t", "--title", action="store", dest="title", default=""
                        , help="the title of the plot.")
    parser.add_argument("-r", "--rankThreshold", action="store", dest="ranks", nargs="+", type=int
                        , default=[5,10,50,100,200], help="list of thresholds for the violin plots.")
    parser.add_argument("--sep", action="store", dest="separator", default=";"
                        , help="the separator used in the benchmarkFile")

    args = parser.parse_args()

    # if Benchmark file exists plot the data
    if os.path.exists(args.benchmarkFile):
        # Ensure that the ranks are sorted and set targetEnd
        thresholds = sorted(args.ranks)
        targetEnd = thresholds[-1]

        # Handle the input and build a dictionary for the ranks up to targetEnd (200)
        benchDF = pd.read_csv(args.benchmarkFile, sep=args.separator, header=0)
        prefix = ["srna_name", "target_ltag", "target_name"]
        intarnaIDs = [x.replace("_intarna_rank", "") for x in benchDF.columns if x not in prefix]

        rankDictionary = dict()
        # Init dictionary
        for entry in intarnaIDs:
            rankDictionary[entry] = []

        # Get the ranks for each callID
        for i in range(0, targetEnd):
            for id in intarnaIDs:
                rankDictionary[id].append(len(benchDF[benchDF[id + "_intarna_rank"] <= i]))

        # Create merged plots
        colorcycler = cycle(colorList[::-1])
        keys = list(rankDictionary.keys())
        human_sort(keys)

        # Create a subplot
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14,6))

        # PLOT 1 (ROC)
        for key in keys:
            if key == args.fixedID:
                ax1.plot(rankDictionary[args.fixedID], label=args.fixedID, color="red", zorder=30)
                continue

            ax1.plot(rankDictionary[key], label=key, color=next(colorcycler))

        # Create the legend
        ax1.legend(loc="lower right", fontsize=14)
        ax1.axes.set_xlabel("# Target predictions per sRNA", fontsize=16)
        ax1.axes.set_ylabel("# True positive", fontsize=16)


        # Data preparations
        refData = rankDictionary[args.fixedID]
        rankDictionary.pop(args.fixedID, None)

        # Keys without reference key
        keys = list(rankDictionary.keys())
        human_sort(keys)

        # Create dataframe to use seaborn boxplot
        boxDataFrame = pd.DataFrame(index=np.arange(0, sum(thresholds)*len(keys)),columns=["key", "threshold", "value"])

        idx = 0
        # one idx per future row (avoid append function as it copys the dataframe every time a row is appended)
        for key in keys:
            boxData = list(map(operator.sub, rankDictionary[key], refData))
            for threshold in thresholds:
                for value in boxData[:threshold]:
                    boxDataFrame.loc[idx] = [key, threshold, value]
                    idx+=1

        # ensure values are integer
        boxDataFrame["value"] = boxDataFrame["value"].astype(int)

        # Plot the boxplots
        sns.boxplot(x="threshold", y="value", hue="key", data=boxDataFrame, ax=ax2, palette=colorList[::-1][:len(keys)])
        ax2.set_xlabel("thresholds", fontsize="16")
        ax2.set_ylabel("difference measure", fontsize="16")
        ax2.axes.yaxis.set_label_position("right")
        ax2.axes.yaxis.set_ticks_position("right")

        # Remove legend if wanted
        ax2.legend_.remove()

        ax2.axhline(y=0, color="red", linestyle="-", zorder=0)

        # Set the title, if given
        if args.title != "":
            plt.suptitle(args.title, fontsize=20)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(args.outFile)
        plt.close()

    else:
        sys.exit("No valid benchmark file given!!!")

if __name__ == "__main__":
    main(sys.argv[1:])
