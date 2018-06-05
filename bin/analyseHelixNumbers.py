#!/usr/bin/env python3
# Author: Rick Gelhausen
import sys, argparse
import os.path
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


########################################################################################################################
#                                                                                                                      #
#                                       Analyse helix sizes in a for a given benchID                                   #
#                                                                                                                      #
########################################################################################################################


# For each Bracket in the dotBracket notation, find the according closing bracket
# return: list of positions of the matching brackets
def createBPList(dotBracket, possibleBrackets):
    # A list that contains the information about which brackets are matching
    bpList = [-1 for _ in range(len(dotBracket))]
    # For all types of brackets analyse and further complete bpList
    for bracketType in possibleBrackets:
        # If the bracketType does not exist, continue to the next
        if bracketType[0] not in dotBracket:
            continue
        # Stack for keeping track of opening brackets
        stack = []
        for i, b in enumerate(dotBracket):
            # Handle opening brackets
            if b == bracketType[0]:
                stack.append(i)
            # Handle closing brackets
            elif b == bracketType[1]:
                # If the stack is empty and there are still closing brackets -> error
                if len(stack) == 0:
                    raise IndexError("No matching opening bracket for position: " + str(i))
                # Set the according base pairs and remove last stacked bracket
                bpList[i] = stack[-1]
                bpList[stack.pop()] = i
        # If the computation is done, but there are still brackets in the stack -> error
        if len(stack) > 0:
            raise IndexError("No matching closing brackets for: " + str(stack[-1]))

    return bpList

# Used by retrieve_stackingInformation
# This method looks for one stacking from the given start position to the end
# bulge: maximal allowed bulge size
# return: stackLength - the length of a found stack
#         visited     - a set of positions that belong to the stack, they can be skipped by the main method
def findStacking(bpL, bulge, start):
    stackLength = 1
    visited = set([start, bpL[start]])
    # Run until the end of the base pair list
    while start < len(bpL) - 1:
        startE = bpL[start]
        endE = start
        pos = 0
        found = False
        # Run over all the next bases that are within the bulge boundaries
        for base in bpL[start + 1:start + 2 + bulge]:
            # Skip entry
            if base == -1:
                pos += 1
            else:
                # Check if the new base pair is within the last found base pairs
                if startE > base > endE and startE > bpL[base] > endE:
                    # Check if the next found base pair is within the bulge boundaries
                    # If yes, break and check for the next valid base pair
                    if 0 < (startE - base) <= bulge + 1:
                        stackLength += 1
                        start += pos + 1
                        found = True
                        visited.update([start, bpL[start]])
                        break
                    else:
                        pos += 1
                else:
                    pos += 1
        #
        if not found:
            if stackLength > 1:
                return stackLength, visited
            else:
                return 0, visited
    return "There is probably a base missing!!"


# This method finds all stackings in a given bpList.
# bulge: max length of occuring bulges
# return: list of stackings (normal and only pseudoknot)
def retrieve_stackingInformation(bpL, structure, bulge=0):
    stackings = []
    pseudoknotStackings = []
    i = 0
    visited = set()
    while i < len(bpL):
        # If -1 skip entry
        if bpL[i] == -1:
            i += 1
        # If entry is not part of already established stackings, search for new Stacking
        elif bpL[i] not in visited:
            newStackLength, newlyVisited = findStacking(bpL, bulge, i)
            visited.update(newlyVisited)
            # When a new Stack occured update statistics
            if newStackLength != 0:
                stackings.append(newStackLength)

                # pseudoknot stack
                if structure[i] != "(":
                    pseudoknotStackings.append(newStackLength)

            i += 1

        # No stacking found for current position
        else:
            i += 1

    return stackings, pseudoknotStackings


def main(argv):
    parser = argparse.ArgumentParser(description="Script to merge multiple benchmarks")

    parser.add_argument("-b", "--benchID", action="store", dest="benchID", default=""
                       , help="The benchID file to be analysed.")
    parser.add_argument("-i", "--inputPath", action="store", dest="inputPath", default=""
                       , help="The inputPath the benchmark output is located.")
    parser.add_argument("-o", "--outPath", action="store", dest="outPath", default=""
                        , help="The outputPath for the plot.")
    args = parser.parse_args()

    if (args.benchID == "" or args.inputPath == "" or args.outPath == ""):
        sys.exit("benchID, inputPath and outputPath are mandatory!")

    if not os.path.exists(os.path.join(args.inputPath,args.benchID)):
        sys.exit("Filepath does not exist!!!")

    sRNAfiles = glob.glob(os.path.join(args.inputPath, args.benchID, "*"))
    sRNAfiles = [x for x in sRNAfiles if "memoryUsage" not in x and "runTime" not in x and ".txt" not in x and "benchmark" not in x]

    numberOfStackingsList = []
    maxLengthList = []
    helixLengthList = []
    for sRNA in sRNAfiles:
        try:
            df = pd.read_csv(sRNA, sep=";")
        except:
            continue

        helixData = df["hybridDP"].tolist()[:200]

        interactionLengthList = []

        for helix in helixData:
            lengths = retrieve_stackingInformation(createBPList(helix, ["()"]), helix)[0]
            numberOfStackingsList.append(len(lengths))

            helixLengthList += lengths
            splitInteraction = helix.split("&")
            interactionLengthList.append(max(len(splitInteraction[0]), len(splitInteraction[1])))

        maxLengthList += interactionLengthList

    # NUMBER
    plt.hist(numberOfStackingsList,bins=[x for x in range(2, max(numberOfStackingsList), 1)])

    plt.ylabel("Count")
    plt.xlabel("# Helices")
    plt.title("Number of helices predicted per interaction", fontsize=10)

    plt.yscale("log", nonposy="clip")

    plt.ylim(ymax=12000)
    plt.xlim(xmax=25)

    plt.tight_layout()

    plt.savefig(args.outPath + "_number.pdf")
    plt.close()




    # LENGHTS
    helixLengthList = [x for x in helixLengthList if x < 40]
    plt.hist(helixLengthList)

    plt.ylabel("Count")
    plt.xlabel("Number of helices")
    plt.title("Distribution of helix lengths", fontsize=10)

    # plt.yscale("log", nonposy="clip")

    plt.ylim(ymax=6000)
    # plt.xlim(xmax=20)

    plt.tight_layout()

    plt.savefig(args.outPath+ "_lengths.pdf")
    plt.close()




    # INTERACTION
    plt.hist(maxLengthList, bins=[x for x in range(0, 140, 5)])

    # print(interactionLengthList)
    plt.ylabel("Count")
    plt.xlabel("Interaction lengths")
    plt.title("Distribution of maximum interaction lengths", fontsize=10)

    plt.yscale("log", nonposy="clip")
    #
    plt.ylim(ymax=6000)
    plt.xlim(xmax=160)

    plt.tight_layout()

    plt.savefig(args.outPath +"_interaction.pdf")
    plt.close()

if __name__ == "__main__":
    main(sys.argv[1:])
