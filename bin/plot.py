#!/usr/bin/env python3
# Author: Rick Gelhausen

import sys, argparse
import os
import pandas as pd
import re
import operator
import numpy as np
import configparser
import matplotlib

matplotlib.use('Agg')
from itertools import cycle
import matplotlib.pyplot as plt

########################################################################################################################
#                                                                                                                      #
#                                   Plot contents of a given benchmark.csv file                                        #
#                                                                                                                      #
#                                                                                                                      #
########################################################################################################################

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

#  set axis style
def set_axis_style(ax, labels, config):
    ax.get_xaxis().set_tick_params(direction='out')
    ax.xaxis.set_ticks_position(config["axisstyle"]["xticksPos"])
    ax.set_xticks(np.arange(1, len(labels) + 1))
    ax.set_xticklabels(labels, fontsize=int(config["axisstyle"]["xticksFontsize"]))

def set_axis_limits(ax, config):
    # Handle user input for the x and y limits
    if config["body"]["limtypeX"] == "range":
        ax.axes.set_xlim(int(config["body"]["minX"]), int(config["body"]["maxX"]))
    elif config["body"]["limtypeX"] == "min":
        ax.axes.set_xlim(left=int(config["body"]["minX"]))
    elif config["body"]["limtypeX"] == "max":
        ax.axes.set_xlim(right=int(config["body"]["maxX"]))

    if config["body"]["limtypeY"] == "range":
        ax.axes.set_ylim(int(config["body"]["minY"]), int(config["body"]["maxY"]))
    elif config["body"]["limtypeY"] == "min":
        ax.axes.set_ylim(bottom=int(config["body"]["minY"]))
    elif config["body"]["limtypeY"] == "max":
        ax.axes.set_ylim(top=int(config["body"]["maxY"]))

def set_violin_limits(ax, config):
    if config["violin"]["limtypeY"] == "range":
        ax.axes.set_ylim(int(config["violin"]["minY"]), int(config["violin"]["maxY"]))
    elif config["violin"]["limtypeY"] == "min":
        ax.axes.set_ylim(bottom=int(config["violin"]["minY"]))
    elif config["violin"]["limtypeY"] == "max":
        ax.axes.set_ylim(top=int(config["violin"]["maxY"]))

def determine_ranks(args, config):
    benchDF = pd.read_csv(args.inputFile, sep=args.separator, header=0)
    prefix = ["srna_name", "target_ltag", "target_name"]
    intarnaIDs = [x.replace("_intarna_rank", "") for x in benchDF.columns if x not in prefix]

    rankDictionary = dict()
    # Init dictionary
    for entry in intarnaIDs:
        rankDictionary[entry] = []

    # Get the ranks for each callID
    for i in range(1, int(config["general"]["end"])):
        for id in intarnaIDs:
            rankDictionary[id].append(len(benchDF[benchDF[id+"_intarna_rank"] <= i]))
    return rankDictionary

def plot_merged(args, config):
    rankDictionary = determine_ranks(args, config)

    colorcycler = cycle(config["general"]["colorList"].split(", "))
    keys = list(rankDictionary.keys())
    human_sort(keys)

    # Create a subplot
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, \
                        figsize=(int(config["body"]["subplotsizeX"]), \
                                 int(config["body"]["subplotsizeY"])))

    if args.referenceID == "":
        sys.exit("A reference ID is required for the violin plot. Specify it using -r or --referenceID")

    #####################################################################################################
    #                                             ROC PLOT                                              #
    #####################################################################################################

    # Check keys and plot the referenceID in red.
    # The other keys are colored according to the given color list.
    for key in keys:
        if key == args.referenceID:
            ax1.plot(rankDictionary[args.referenceID], label=args.referenceID, color="red", zorder=30)
            continue

        ax1.plot(rankDictionary[key], label=key, color=next(colorcycler))

    # Create the legend
    ax1.legend(loc=config["legend"]["loc"], fontsize=int(config["legend"]["fontsize"]))
    ax1.axes.set_xlabel(config["body"]["xlabel"], fontsize=int(config["body"]["fontsize"]))
    ax1.axes.set_ylabel(config["body"]["ylabel"], fontsize=int(config["body"]["fontsize"]))

    set_axis_limits(ax1, config)

    # scale
    if config["body"]["xscale"] != "":
        ax1.axes.set_xscale(config["body"]["xscale"])
    if config["body"]["yscale"] != "":
        ax1.axes.set_xscale(config["body"]["yscale"])


    #####################################################################################################
    #                                          VIOLIN PLOT                                              #
    #####################################################################################################

    # Data preparations
    refData = rankDictionary[args.referenceID]
    rankDictionary.pop(args.referenceID, None)

    # Keys without reference key
    keys = list(rankDictionary.keys())
    human_sort(keys)

    violinData = []
    for key in keys:
        violinData.append(list(map(operator.sub, rankDictionary[key], refData)))

    violin_parts = ax2.violinplot(violinData, showextrema=True, showmeans=True, showmedians=True)
    for idx, pc in enumerate(violin_parts['bodies']):
        pc.set_facecolor(config["general"]["colorList"].split(", ")[idx])
        pc.set_edgecolor(config["violin"]["edgecolor"])
        pc.set_alpha(float(config["violin"]["alpha"]))

    #cbars
    violin_parts["cbars"].set_edgecolor(config["violin"]["cbars_edgecolor"])
    violin_parts["cbars"].set_linestyle(config["violin"]["cbars_linestyle"])

    # cmins
    violin_parts["cmins"].set_edgecolor(config["violin"]["cmins_edgecolor"])
    violin_parts["cmins"].set_linestyle(config["violin"]["cmins_linestyle"])

    # cmaxes
    violin_parts["cmaxes"].set_edgecolor(config["violin"]["cmaxes_edgecolor"])
    violin_parts["cmaxes"].set_linestyle(config["violin"]["cmaxes_linestyle"])

    # cmeans
    violin_parts["cmeans"].set_edgecolor(config["violin"]["cmeans_edgecolor"])
    violin_parts["cmeans"].set_linestyle(config["violin"]["cmeans_linestyle"])

    # cmedians
    violin_parts["cmedians"].set_edgecolor(config["violin"]["cmedians_edgecolor"])
    violin_parts["cmedians"].set_linestyle(config["violin"]["cmedians_linestyle"])

    # label positioning
    ax2.axes.set_xlabel(config["violin"]["xlabel"], fontsize=int(config["violin"]["fontsize"]))
    ax2.axes.xaxis.set_label_position(config["violin"]["xlabelpos"])
    ax2.axes.xaxis.set_ticks_position(config["violin"]["xtickspos"])

    ax2.axes.set_ylabel(config["violin"]["ylabel"], fontsize=int(config["violin"]["fontsize"]))
    ax2.axes.yaxis.set_label_position(config["violin"]["ylabelpos"])
    ax2.axes.yaxis.set_ticks_position(config["violin"]["ytickspos"])
    ax2.axes.set_xticks([])

    set_violin_limits(ax2, config)

    ax2.axhline(y=0, color="red", linestyle="-", zorder=0)

    # Set the title, if given
    if args.title != "":
        plt.suptitle(args.title, fontsize=config["title"]["fontsize"])

    plt.tight_layout(rect=[float(x) for x in config["title"]["tight_layout"].split(" ")])
    plt.savefig(args.outputFile)
    plt.close()

def plot_time_and_memory(args, config):
    runTimeFile = os.path.splitext(args.inputFile)[0] + "_runTimes.csv"
    memoryFile = os.path.splitext(args.inputFile)[0] + "_MaxMemoryUsage.csv"

    if not os.path.exists(runTimeFile):
        sys.exit("no runTimeFile found!!")
    if not os.path.exists(memoryFile):
        sys.exit("no maxMemoryUsage file found!!")

    # Read the csv files
    timeDF = pd.read_csv(runTimeFile, sep=args.separator, header=0)
    memoryDF = pd.read_csv(memoryFile, sep=args.separator, header=0)
    benchDF = pd.read_csv(args.inputFile, sep=args.separator, header=0)

    prefix = ["srna_name", "target_ltag", "target_name"]
    # remove the _intarna_rank suffixes
    intarnaIDs = [x.replace("_intarna_rank", "") for x in benchDF.columns if x not in prefix]
    # Sort ids in a human readable form
    human_sort(intarnaIDs)

    # Create a subplot
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14,6))

    #####################################################################################################
    #                                            TIME PLOT                                              #
    #####################################################################################################

    timeDict = dict()
    for id in intarnaIDs:
        timeDict[id] = []

    # Read the values into the time dictionary
    for row in timeDF.iterrows():
        index, data = row
        timeDict[timeDF.iloc[index]["callID"]] += data.tolist()[3:]

    # Handle the reference ID
    timeData = []
    refData = timeDict[args.referenceID]
    timeDict.pop(args.referenceID, None)

    keys = list(timeDict.keys())
    # sort the list on keys in a human readable form
    human_sort(keys)

    # Convert time from sec to min
    for key in keys:
        timeIncrease = list(map(operator.sub, timeDict[key], refData))
        timeIncreasePercentage= [x/y for x,y in zip(timeIncrease,timeDict[key])] #(timeIncrease / timeDict) *100
        timeData.append([x*100 for x in timeIncreasePercentage])

    #timeData = [[y/(60) for y in x] for x in timeData]
    #print(timeData)

    violin_parts = ax1.violinplot(timeData, showextrema=True, showmeans=True, showmedians=True)
    for idx, pc in enumerate(violin_parts['bodies']):
        pc.set_facecolor(config["general"]["colorList"].split(", ")[idx])
        pc.set_edgecolor(config["violin"]["edgecolor"])
        pc.set_alpha(float(config["violin"]["alpha"]))

    # cbars
    violin_parts["cbars"].set_edgecolor(config["violin"]["cbars_edgecolor"])
    violin_parts["cbars"].set_linestyle(config["violin"]["cbars_linestyle"])

    # cmins
    violin_parts["cmins"].set_edgecolor(config["violin"]["cmins_edgecolor"])
    violin_parts["cmins"].set_linestyle(config["violin"]["cmins_linestyle"])

    # cmaxes
    violin_parts["cmaxes"].set_edgecolor(config["violin"]["cmaxes_edgecolor"])
    violin_parts["cmaxes"].set_linestyle(config["violin"]["cmaxes_linestyle"])

    # cmeans
    violin_parts["cmeans"].set_edgecolor(config["violin"]["cmeans_edgecolor"])
    violin_parts["cmeans"].set_linestyle(config["violin"]["cmeans_linestyle"])

    # cmedians
    violin_parts["cmedians"].set_edgecolor(config["violin"]["cmedians_edgecolor"])
    violin_parts["cmedians"].set_linestyle(config["violin"]["cmedians_linestyle"])

    ax1.axhline(y=0, color="red", linestyle="-", zorder=0)

    # label positioning
    ax1.axes.set_ylabel(config["time"]["ylabel"], fontsize=int(config["time"]["fontsize"]))
    ax1.axes.yaxis.set_label_position(config["time"]["ylabelpos"])
    ax1.axes.yaxis.set_ticks_position(config["time"]["ytickspos"])
    ax1.axes.set_xticks([])

    set_axis_style(ax1, keys, config)

    #####################################################################################################
    #                                          Memory PLOT                                              #
    #####################################################################################################
    memoryDict = dict()
    for id in intarnaIDs:
        memoryDict[id] = []

    for row in memoryDF.iterrows():
        index, data = row
        memoryDict[memoryDF.iloc[index]["callID"]] +=  data.tolist()[3:]

    # Handle the reference ID
    memoryData = []
    refData = memoryDict[args.referenceID]
    memoryDict.pop(args.referenceID, None)

    keys = list(memoryDict.keys())
    # sort the list on keys in a human readable form
    human_sort(keys)

    # Convert memory from kb to mb
    for key in keys:
        memoryKB = list(map(operator.sub, memoryDict[key], refData))
        memoryData.append([x / 1024 for x in memoryKB])

    violin_parts = ax2.violinplot(memoryData, showextrema=True, showmeans=True, showmedians=True)
    for idx, pc in enumerate(violin_parts['bodies']):
        pc.set_facecolor(config["general"]["colorList"].split(", ")[idx])
        pc.set_edgecolor(config["violin"]["edgecolor"])
        pc.set_alpha(float(config["violin"]["alpha"]))

    # cbars
    violin_parts["cbars"].set_edgecolor(config["violin"]["cbars_edgecolor"])
    violin_parts["cbars"].set_linestyle(config["violin"]["cbars_linestyle"])

    # cmins
    violin_parts["cmins"].set_edgecolor(config["violin"]["cmins_edgecolor"])
    violin_parts["cmins"].set_linestyle(config["violin"]["cmins_linestyle"])

    # cmaxes
    violin_parts["cmaxes"].set_edgecolor(config["violin"]["cmaxes_edgecolor"])
    violin_parts["cmaxes"].set_linestyle(config["violin"]["cmaxes_linestyle"])

    # cmeans
    violin_parts["cmeans"].set_edgecolor(config["violin"]["cmeans_edgecolor"])
    violin_parts["cmeans"].set_linestyle(config["violin"]["cmeans_linestyle"])

    # cmedians
    violin_parts["cmedians"].set_edgecolor(config["violin"]["cmedians_edgecolor"])
    violin_parts["cmedians"].set_linestyle(config["violin"]["cmedians_linestyle"])

    # label positioning
    ax2.axes.set_ylabel(config["memory"]["ylabel"], fontsize=int(config["memory"]["fontsize"]))
    ax2.axes.yaxis.set_label_position(config["memory"]["ylabelpos"])
    ax2.axes.yaxis.set_ticks_position(config["memory"]["ytickspos"])
    ax2.axes.set_xticks([])

    ax2.axhline(y=0, color="red", linestyle="-", zorder=0)

    set_axis_style(ax2, keys, config)

    plt.suptitle(config["additionalplots"]["title"], fontsize=int(config["additionalplots"]["fontsize"]))

    for tick in ax1.get_xticklabels():
        tick.set_rotation(float(config["axisstyle"]["xticksRotation"]))
    for tick in ax2.get_xticklabels():
        tick.set_rotation(float(config["axisstyle"]["xticksRotation"]))

    plt.tight_layout(rect=[float(x) for x in config["additionalplots"]["tight_layout"].split(" ")])
    plt.savefig(os.path.splitext(args.outputFile)[0] + "_info.pdf")
    plt.close()

def main(argv):
    parser = argparse.ArgumentParser(description="Script for plotting the benchmark results")
    parser.add_argument("-i", "--ifile", action="store", dest="inputFile", required=True
                        , help="mandatory benchmark file to be used for plotting.")
    parser.add_argument("-o", "--ofile", action="store", dest="outputFile", required=True
                        , help="the path of the outputFilePath.")
    parser.add_argument("-s", "--sep", action="store", dest="separator", default=";"
                        , help="separator of the csv file.")
    parser.add_argument("-c", "--config", action="store", dest="config", default="config.txt"
                        , help="path to the required configuration file.")
    parser.add_argument("-t", "--title", action="store", dest="title", default=""
                        , help="the title of the plot.")
    parser.add_argument("-r", "--referenceID", action="store", dest="referenceID", default=""
                        , help="the ID used to create the reference curve for violin plots.")
    parser.add_argument("-p", "--plottype", action="store", dest="plottype", default="merged"
                        , help="the type of plot required (merged/TODO/TODO)")
    parser.add_argument("-a", "--additional", action="store_true", dest="additional", default=False
                        , help="create additional plots for the time and memory consumption.")
    args = parser.parse_args()

    # Read the config file
    config = configparser.ConfigParser()
    config.sections()
    config.read(args.config)

    if args.plottype == "merged":
        plot_merged(args, config)

    if args.additional:
        plot_time_and_memory(args, config)

if __name__ == "__main__":
    main(sys.argv[1:])
