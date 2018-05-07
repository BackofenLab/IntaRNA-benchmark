import argparse
import os, sys
import pandas as pd

def main(argv):
    fastaFileEndings = [".fasta", ".fa"]

    parser = argparse.ArgumentParser(
        description="Script to rename existing callIDs. This renames the folder and the entries in the included benchmark/time/memory files.")
    parser.add_argument("-n", "--name", action="store", dest="newName", default=""
                        , help="the new name for the callID given!")
    parser.add_argument("-c", "--callID", action="store", dest="callID", default=""
                        , help="the callID to be renamed")
    parser.add_argument("-d", "--dir", action="store", dest="outDir", default=os.path.join("..", "output")
                        , help="Folder containing the callID folder to be changed.")

    args = parser.parse_args()

    # Check whether a callID was given
    if args.callID == "":
        sys.exit("No callID was specified! Please specify a callID using -c <name> or --callID=<name>")

    # Check whether a name was given
    if args.newName == "":
        sys.exit("No name was specified! Please specify a name using -c <name> or --callID=<name>")

    # Check whether directory path exists
    if not os.path.exists(os.path.join(args.outDir, args.callID)):
        sys.exit("Error!!! FilePath does not exist! Please specify it using -o <outDir>!")

    filePath=os.path.join(args.outDir, args.callID)
    newPath=os.path.join(args.outDir, args.newName)

    benchmark = os.path.join(filePath, "benchmark.csv")
    memoryUsage = os.path.join(filePath, "memoryUsage.csv")
    runTime = os.path.join(filePath, "runTime.csv")
    # Check whether the callID folder is intact
    if not os.path.isfile(benchmark) or not os.path.isfile(memoryUsage) or not os.path.isfile(runTime):
        sys.exit("Error!!! Incomplete folder!")

    # change callID to new name for memoryUsage.csv
    memory = pd.read_csv(memoryUsage,sep=";")
    memory.loc[memory["callID"] == args.callID, "callID"] = args.newName
    memory.to_csv(memoryUsage, sep=";",index=False)

    # change callID to new name for runTime.csv
    time = pd.read_csv(runTime,sep=";")
    time.loc[time["callID"] == args.callID, "callID"] = args.newName
    time.to_csv(runTime, sep=";",index=False)

    # change callID to new name for benchmark.csv
    bench = pd.read_csv(benchmark,sep=";")
    bench = bench.rename(columns={"%s_intarna_rank" % args.callID : "%s_intarna_rank" % args.newName})
    bench.to_csv(benchmark, sep=";",index=False)

    # Finally rename directory
    os.rename(filePath, newPath)

if __name__ == "__main__":
    main(sys.argv[1:])
