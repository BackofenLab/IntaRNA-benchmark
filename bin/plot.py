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
    rotation = float(config["axisstyle"]["xticksRotation"])
    if len(labels) > 4 and max(map(len, labels)) > 12 and rotation == 0:
        rotation = 90
    ax.set_xticklabels(labels, fontsize=int(config["axisstyle"]["xticksFontsize"]),
                       rotation=rotation, ha="center" if rotation in (0, 90) else "right")

def save_plot(filename, config, section):
    fig = plt.gcf()
    axis = fig.axes[0]
    handles, labels = axis.get_legend_handles_labels()
    rect = [float(x) for x in config[section]["tight_layout"].split()]
    if len(labels) > 4:
        # Large comparison matrices need space for long run IDs and a legend.
        fig.set_size_inches(fig.get_figwidth(), max(fig.get_figheight(), 9))
        axis.get_legend().remove()
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.94),
                   ncol=2, fontsize=min(int(config["legend"]["fontsize"]), 11))
        rect[3] = min(rect[3], 0.76)
    plt.tight_layout(rect=rect)
    plt.savefig(filename)
    plt.close()


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
    intarnaIDs = [x[:-len("_intarna_rank")] for x in benchDF.columns if x not in prefix]

    rankDictionary = dict()
    # Init dictionary
    for entry in intarnaIDs:
        rankDictionary[entry] = []

    # Get the ranks for each callID
    for i in range(0, int(config["general"]["end"]) + 1):
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

    if args.referenceID not in keys or len(keys) < 2:
        sys.exit("At least two runs and a matching --referenceID are required")

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
        ax1.axes.set_yscale(config["body"]["yscale"])


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
        pc.set_facecolor(config["general"]["colorList"].split(", ")[idx % len(config["general"]["colorList"].split(", "))])
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
    set_axis_style(ax2, keys, config)

    ax2.axhline(y=0, color="red", linestyle="-", zorder=0)

    # Set the title, if given
    if args.title != "":
        plt.suptitle(args.title, fontsize=int(config["title"]["fontsize"]))

    save_plot(args.outputFile, config, "title")

def read_measurements(args, suffix, divisor):
    frame = pd.read_csv(os.path.splitext(args.inputFile)[0] + suffix, sep=args.separator,
                        dtype={"callID": str, "target_name": str, "Organism": str})
    keys = ["callID", "target_name", "Organism"]
    long = frame.melt(id_vars=keys, var_name="query", value_name="value").dropna(subset=["value"])
    index = ["Organism", "target_name", "query"]
    if long.duplicated(["callID", *index]).any():
        raise ValueError("Duplicate resource measurements")
    values = long.pivot(index=index, columns="callID", values="value") / divisor
    if values.empty or values.isna().any().any() or not np.isfinite(values.to_numpy()).all():
        raise ValueError("Runs must contain the same finite resource measurements")
    if args.referenceID not in values:
        raise ValueError("Reference ID missing from resource measurements")
    values = values.sort_values(args.referenceID, kind="stable")
    return {key: values[key].tolist() for key in values}


def relative_changes(values, reference):
    # A zero reference CPU time has no defined percentage change.
    return [(value - ref) / ref * 100 for value, ref in zip(values, reference) if ref > 0]


def plot_time(args, config):
    runTimeFile = os.path.splitext(args.inputFile)[0] + "_runTimes.csv"

    if not os.path.exists(runTimeFile):
        sys.exit("no runTimeFile found!!")

    # Create a subplot
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14,6))
    colorcycler = cycle(config["general"]["colorList"].split(", "))

    #####################################################################################################
    #                                            TIME PLOT                                              #
    #####################################################################################################

    timeDict = read_measurements(args, "_runTimes.csv", 60)
    refData = timeDict[args.referenceID]
    keys = list(timeDict)
    human_sort(keys)

    # the labels for the x-axis
    xlabels = range(1,len(timeDict[args.referenceID])+1)

    # Check keys and plot the referenceID in red.
    # The other keys are colored according to the given color list.
    for key in keys:
        if key == args.referenceID:
            ax1.plot(xlabels, timeDict[key], label=args.referenceID, color="red", zorder=30)
            continue

        ax1.plot(xlabels, timeDict[key], label=key, color=next(colorcycler))

    # Create the legend
    ax1.legend(loc="upper left", fontsize=int(config["legend"]["fontsize"]))
    ax1.axes.set_ylabel(config["time"]["ylabelleft"], fontsize=int(config["time"]["fontsize"]))
    ax1.axes.set_xlabel(config["time"]["xlabel"], fontsize=int(config["body"]["fontsize"]))

    set_axis_limits(ax1, config)
    ax1.set_xticks(np.arange(min(xlabels), max(xlabels)+2, 2.0))

    # =========================================================================
    timeDict.pop(args.referenceID, None)
    timeData = []
    keys = list(timeDict.keys())
    human_sort(keys)

    for key in keys:
        timeData.append(relative_changes(timeDict[key], refData))

    if all(timeData):
        violin_parts = ax2.violinplot(timeData, showextrema=True, showmeans=True, showmedians=True)
        for idx, pc in enumerate(violin_parts['bodies']):
            pc.set_facecolor(config["general"]["colorList"].split(", ")[idx % len(config["general"]["colorList"].split(", "))])
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

    else:
        ax2.text(0.5, 0.5, "Percentage undefined: zero reference CPU time",
                 ha="center", va="center", transform=ax2.transAxes)

    ax2.axhline(y=0, color="red", linestyle="-", zorder=0)

    # label positioning
    ax2.axes.set_ylabel(config["time"]["ylabelright"], fontsize=int(config["time"]["fontsize"]))
    ax2.axes.yaxis.set_label_position(config["time"]["ylabelpos"])
    ax2.axes.yaxis.set_ticks_position(config["time"]["ytickspos"])
    ax2.axes.set_xticks([])

    set_axis_style(ax2, keys, config)

    plt.suptitle(config["time"]["title"], fontsize=int(config["additionalplots"]["fontsize"]))

    for tick in ax1.get_xticklabels():
        tick.set_rotation(float(config["axisstyle"]["xticksRotation"]))

    save_plot(os.path.splitext(args.outputFile)[0] + "_runtime.pdf", config, "additionalplots")

def plot_memory(args, config):
    memoryFile = os.path.splitext(args.inputFile)[0] + "_MaxMemoryUsage.csv"

    if not os.path.exists(memoryFile):
        sys.exit("no maxMemoryUsage file found!!")

    # Create a subplot
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14,6))
    colorcycler = cycle(config["general"]["colorList"].split(", "))

    #####################################################################################################
    #                                          MEMORY PLOT                                              #
    #####################################################################################################

    memoryDict = read_measurements(args, "_MaxMemoryUsage.csv", 1024)
    refData = memoryDict[args.referenceID]
    keys = list(memoryDict)
    human_sort(keys)

    # the labels for the x-axis
    xlabels = range(1,len(memoryDict[args.referenceID])+1)

    # Check keys and plot the referenceID in red.
    # The other keys are colored according to the given color list.
    for key in keys:
        if key == args.referenceID:
            ax1.plot(xlabels, memoryDict[key], label=args.referenceID, color="red", zorder=30)
            continue

        ax1.plot(xlabels, memoryDict[key], label=key, color=next(colorcycler))

    # Create the legend
    ax1.legend(loc="upper left", fontsize=int(config["legend"]["fontsize"]))
    ax1.axes.set_ylabel(config["memory"]["ylabelleft"], fontsize=int(config["memory"]["fontsize"]))
    ax1.axes.set_xlabel(config["memory"]["xlabel"], fontsize=int(config["body"]["fontsize"]))

    set_axis_limits(ax1, config)
    ax1.set_xticks(np.arange(min(xlabels), max(xlabels)+2, 2.0))

    # =========================================================================
    memoryDict.pop(args.referenceID, None)
    memoryData = []
    keys = list(memoryDict.keys())
    human_sort(keys)

    # Convert memory from kb to mb
    for key in keys:
        memoryKB = list(map(operator.sub, memoryDict[key], refData))
        memoryData.append(memoryKB)

    violin_parts = ax2.violinplot(memoryData, showextrema=True, showmeans=True, showmedians=True)
    for idx, pc in enumerate(violin_parts['bodies']):
        pc.set_facecolor(config["general"]["colorList"].split(", ")[idx % len(config["general"]["colorList"].split(", "))])
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
    ax2.axes.set_ylabel(config["memory"]["ylabelright"], fontsize=int(config["memory"]["fontsize"]))
    ax2.axes.yaxis.set_label_position(config["memory"]["ylabelpos"])
    ax2.axes.yaxis.set_ticks_position(config["memory"]["ytickspos"])
    ax2.axes.set_xticks([])

    ax2.axhline(y=0, color="red", linestyle="-", zorder=0)

    set_axis_style(ax2, keys, config)

    plt.suptitle(config["memory"]["title"], fontsize=int(config["additionalplots"]["fontsize"]))

    for tick in ax1.get_xticklabels():
        tick.set_rotation(float(config["axisstyle"]["xticksRotation"]))

    save_plot(os.path.splitext(args.outputFile)[0] + "_memory.pdf", config, "additionalplots")

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
    parser.add_argument("-n", "--title", action="store", dest="title", default=""
                        , help="the title of the plot.")
    parser.add_argument("-r", "--referenceID", action="store", dest="referenceID", default=""
                        , help="the ID used to create the reference curve for violin plots.")
    parser.add_argument("-p", "--plottype", action="store", dest="plottype", default="merged", choices=["merged"]
                        , help="the type of plot required (merged/TODO/TODO)")
    parser.add_argument("-t", "--time", action="store_true", dest="time", default=False
                        , help="create additional plots for the runtime.")
    parser.add_argument("-m", "--memory", action="store_true", dest="memory", default=False
                        , help="create additional plots for the memory consumption.")
    args = parser.parse_args(argv)

    # Read the config file
    config = configparser.ConfigParser(interpolation=None)
    config.sections()
    if not config.read(args.config):
        parser.error("Configuration file not found: " + args.config)
    os.makedirs(os.path.dirname(os.path.abspath(args.outputFile)), exist_ok=True)

    if args.plottype == "merged":
        plot_merged(args, config)

    if args.time:
        plot_time(args, config)

    if args.memory:
        plot_memory(args, config)

if __name__ == "__main__":
    main(sys.argv[1:])
