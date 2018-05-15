#!/usr/bin/env python3
# Author: Rick Gelhausen

import sys, argparse
import os
import pandas as pd
import matplotlib
import re
import operator
import numpy as np

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

# set axis
def set_axis_style(ax, labels):
    ax.get_xaxis().set_tick_params(direction='out')
    # ax.xaxis.set_ticks_position('bottom')
    ax.set_xticks(np.arange(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    #ax.set_xlim(0.25, len(labels) + 0.75)

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
                        , help="Decide whether to use ROC or Violin plots. Plots can also be merged with 'merged' keyword")
    parser.add_argument("-a", "--additional", action="store_true", dest="additional", default=False
                        , help="Create additional plots for the time and memory consumption.")
    parser.add_argument("-r", "--rotation", action="store", dest="rotation", default=0
                        , help="The rotation of the xticks.")
    args = parser.parse_args()

    if args.benchmarkFile == "":
        sys.exit("Please specify a benchmark.csv with: python3 plot_performance.py -i <filename.csv> !")


    if os.path.exists(args.benchmarkFile):
        benchDF = pd.read_csv(args.benchmarkFile, sep=args.separator, header=0)
        prefix = ["srna_name", "target_ltag", "target_name"]
        intarnaIDs = [x.replace("_intarna_rank", "") for x in benchDF.columns if x not in prefix]

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

            fig, ax = plt.subplots(nrows=1, ncols=1)

            data = []
            for key in keys:
                data.append(list(map(operator.sub, rankDictionary[key], refData)))

            violin_parts = ax.violinplot(data, showextrema=True, showmeans=True, showmedians=True)
            for idx, pc in enumerate(violin_parts['bodies']):
                pc.set_facecolor(colorList[::-1][idx])
                pc.set_edgecolor('black')
                pc.set_alpha(1)

            for part in ("cbars", "cmins", "cmaxes", "cmeans"):
                vp = violin_parts[part]
                vp.set_edgecolor('black')

            vp = violin_parts["cmedians"]
            vp.set_edgecolor("black")
            vp.set_linestyle("--")

            # Set the title, if given
            if args.title != "":
                plt.title(args.title)

            # set_axis_style(ax, keys)

            # Create the legend
            # plt.legend(loc="lower right")
            # plt.xlabel("# Target predictions per sRNA")
            plt.ylabel("difference measure")

            # plt.xticks(rotation=15)
            plt.xticks([])
            plt.tight_layout()
            plt.axhline(y=0, color="red", linestyle="-", zorder=0)
            plt.savefig(args.outFile)
            plt.close()
        elif args.plotType == "merged":
            if args.fixedID == "":
                sys.exit("Please provide a reference curve with --fixedID=<callID> to compute the violin plot.")


            linecycler = cycle(lineList)
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

                if not args.lines:
                    ax1.plot(rankDictionary[key], label=key, color=next(colorcycler))
                else:
                    ax1.plot(rankDictionary[key], label=key, color=next(colorcycler), linestyle=next(linecycler))

            # Create the legend
            ax1.legend(loc="lower right")
            ax1.axes.set_xlabel("# Target predictions per sRNA")
            ax1.axes.set_ylabel("# True positive")

            # Handle user input for the x and y limits
            if args.xlim != "" and "/" in args.xlim:
                ax1.xlim(int(args.xlim.split("/")[0]), int(args.xlim.split("/")[1]))
            if args.ylim != "" and "/" in args.ylim:
                ax1.ylim(int(args.ylim.split("/")[0]), int(args.ylim.split("/")[1]))


            # Data preparations
            refData = rankDictionary[args.fixedID]
            rankDictionary.pop(args.fixedID, None)

            # Keys without reference key
            keys = list(rankDictionary.keys())
            human_sort(keys)

            violinData = []
            for key in keys:
                violinData.append(list(map(operator.sub, rankDictionary[key], refData)))

            violin_parts = ax2.violinplot(violinData, showextrema=True, showmeans=True, showmedians=True)
            for idx, pc in enumerate(violin_parts['bodies']):
                pc.set_facecolor(colorList[::-1][idx])
                pc.set_edgecolor('black')
                pc.set_alpha(1)

            for part in ("cbars", "cmins", "cmaxes", "cmeans"):
                vp = violin_parts[part]
                vp.set_edgecolor('black')

            vp = violin_parts["cmedians"]
            vp.set_edgecolor("black")
            vp.set_linestyle("--")

            ax2.axes.set_ylabel("difference measure")
            ax2.axes.yaxis.set_label_position("right")
            ax2.axes.yaxis.set_ticks_position("right")
            ax2.axes.set_xticks([])

            ax2.axhline(y=0, color="red", linestyle="-", zorder=0)

            # Set the title, if given
            if args.title != "":
                plt.suptitle(args.title, fontsize=15)

            plt.tight_layout(rect=[0,0.03,1,0.95])
            plt.savefig(args.outFile)
            plt.close()

        else:
            sys.exit("Please specify a plot type: -p<'roc' / 'violin' / 'merged'>")

        # Time and Memory plots
        if (args.additional):
            runTimeFile = os.path.splitext(args.benchmarkFile)[0] + "_runTimes.csv"
            memoryFile = os.path.splitext(args.benchmarkFile)[0] + "_MaxMemoryUsage.csv"

            if not os.path.exists(runTimeFile):
                sys.exit("no runTimeFile found!!")
            if not os.path.exists(memoryFile):
                sys.exit("no MaxMemoryUsage file found!!")

            timeDF = pd.read_csv(runTimeFile, sep=args.separator, header=0)
            memoryDF = pd.read_csv(memoryFile, sep=args.separator, header=0)

            human_sort(intarnaIDs)

            prefix = ["srna_name", "target_ltag", "target_name"]
            intarnaIDs = [x.replace("_intarna_rank", "") for x in benchDF.columns if x not in prefix]

            # Create a subplot
            fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14,6))

            # Time
            timeDict = dict()
            for id in intarnaIDs:
                timeDict[id] = []

            for row in timeDF.iterrows():
                index, data = row
                timeDict[timeDF.get_value(index, "callID")] += data.tolist()[3:]

            keys = list(timeDict.keys())
            human_sort(keys)

            timeData = []
            keys.remove(args.fixedID)
            for key in keys:
                timeData.append(timeDict[key])

            timeData = [timeDict[args.fixedID]] + timeData
            # Convert time from sec to min
            timeData = [[y/60 for y in x] for x in timeData]
            colorList.append("red")

            violin_parts = ax1.violinplot(timeData, showextrema=True, showmeans=True, showmedians=True)
            for idx, pc in enumerate(violin_parts['bodies']):
                pc.set_facecolor(colorList[::-1][idx])
                pc.set_edgecolor('black')
                pc.set_alpha(1)

            for part in ("cbars", "cmins", "cmaxes", "cmeans"):
                vp = violin_parts[part]
                vp.set_edgecolor('black')

            vp = violin_parts["cmedians"]
            vp.set_edgecolor("black")
            vp.set_linestyle("--")

            ax1.axes.set_ylabel("time (in minutes)")
            ax1.axes.set_xticks([])


            # Memory
            memoryDict = dict()
            for id in intarnaIDs:
                memoryDict[id] = []

            for row in memoryDF.iterrows():
                index, data = row
                memoryDict[memoryDF.get_value(index, "callID")] += data.tolist()[3:]

            keys = list(memoryDict.keys())
            human_sort(keys)

            memoryData = []
            keys.remove(args.fixedID)
            for key in keys:
                memoryData.append(memoryDict[key])

            memoryData = [memoryDict[args.fixedID]] + memoryData

            violin_parts = ax2.violinplot(memoryData, showextrema=True, showmeans=True, showmedians=True)
            for idx, pc in enumerate(violin_parts['bodies']):
                pc.set_facecolor(colorList[::-1][idx])
                pc.set_edgecolor('black')
                pc.set_alpha(1)

            for part in ("cbars", "cmins", "cmaxes", "cmeans"):
                vp = violin_parts[part]
                vp.set_edgecolor('black')

            vp = violin_parts["cmedians"]
            vp.set_edgecolor("black")
            vp.set_linestyle("--")

            ax2.axes.set_ylabel("memory (in megabytes)")
            ax2.axes.yaxis.set_label_position("right")
            ax2.axes.yaxis.set_ticks_position("right")
            ax2.axes.set_xticks([])

            keys = [args.fixedID] + keys

            set_axis_style(ax1, keys)
            set_axis_style(ax2, keys)

            plt.suptitle("Time and memory consumption", fontsize=15)
            # plt.legend(handles=ax2, labels=keys)
            # print(handles, labels)
            for tick in ax1.get_xticklabels():
                tick.set_rotation(args.rotation)
            for tick in ax2.get_xticklabels():
                tick.set_rotation(args.rotation)

            plt.tight_layout(rect=[0,0.03,1,0.95])
            plt.show()
            plt.savefig(os.path.splitext(args.outFile)[0] + "_info.pdf")
            plt.close()

    else:
        sys.exit("Could not find %s!" % args.benchmarkFile)


if __name__ == "__main__":
    main(sys.argv[1:])
