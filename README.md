# IntaRNA-benchmark
Data and scripts to benchmark IntaRNA.

### Setup
The `input` directory contains folders representing certain organisms (here Salmonella and E. coli) or benchmark data sets.
Each has to contain two folders, one holding the `query` RNAs and one holding the `target` RNAs.

The `output` directory contains a folder for each `callID` (see parameters of `calls.py`) holding all the result files for that specific callID.
This folder is initially empty and is filled using the benchmark scripts.

The `bin` folder holds various different scripts used in the benchmarking process.

A required file is the `verified_interactions.csv`. The file contains interactions that were verified experimentally.

### Theoretical background
The idea is to compare the output of different IntaRNA calls with the experimentally verified interactions.
In order to achieve this, the `calls.py` script is used on the query and target files for each benchmark data set (in `input` folder)  using the specified IntaRNA call.
This results in a result file for each data set and query RNA.
These files contain the interaction results produced by IntaRNA.

In each file, the results are ordered according to their energy.
This way, the result files are sorted from the most favorable (lowest energy) to the most unfavorable interaction (highest energy).
The hope is that the verified interactions for each query RNA are amongst the first entries of each file, i.e they have low energy.
Therefore, a rank is stored for each entry in the verified_interactions file, representing the rowID of that specific interaction in the according IntaRNA output.
For example, for sRNA ArcZ and mRNA STM1682 we check the Salmonella result file for ArcZ (ArcZ_NC_003197) and search for STM1682. The rank is then the row index in which STM1682 appears.
The lower the rank, the better.

In order to visualize the results, a receiver operating characteristic (ROC) curve is used.
It is created using the ranks determined earlier.
The X-axis describes the number of target predictions per query RNA, while the Y-axis represents
the number of true positives. 
This means that for each X, the number of ranks that are smaller or equal to X are counted and represented on the Y-axis.
Like this, multiple callIDs can be plotted into the same graph to compare the performance.

### Scripts

The scripts are contained in the bin folder.

#### calls.py
__Parameters:__
* __intaRNAPath (`-i`)__ the location of the intaRNA executable. Default: __..__/__..__/IntaRNA/src/bin/ 
* __inputPath (`-f`)__ location of the folder containing folders for each organism. The organism folders have to contain a query and a target folder holding the according fasta files. Default: __..__/input/
* __outputPath (`-o`)__ location of the output folder. The script will add a folder for each callID. Default: __..__/output/
* __callID (`-c`)__ is a mandatory ID to differentiate between multiple calls of the script.
* __arg (`-a`)__ commandline arguments for intaRNA.

This script calls IntaRNA from `intaRNAPath` using the queries and targets for all data sets found within the `inputPath` (see above) and the additional parameterization provided by `arg`.
The results of IntaRNA are piped to stdout and then into an output file in the `outputPath` where the `callID` is used for according file naming.
There are many different controls to assure that no files are overwritten and that the required files are available.

The time (in seconds) and maximal memory usage (in megabyte) required to handle each call is also measured and represented in a table. 
The tables are also stored in the specified `outputPath`. The individual calls are also logged into a log file.

Calls the benchmark.py using the specified callID as benchID.

__Output:__ (contained in the respective callID folder)
* (query)_(target).csv -> intarna output for a specific query-target combination (FASTA names used)
* calls.txt -> log file for the calls
* runTime.csv -> table with runtimes for each query-target combination.
* memoryUsage.csv -> table with memory usage for each query-target combination.

#### benchmark.py

__Parameters:__
* __verifiedHybrids (`-i`)__ the location of the file containing the experimentally verified interactions. Default: __..__/verified_interactions.csv
* __outputFile (`-o`)__ the name of the output file. Default: /benchmark.csv
* __outputPath (`-p`)__ the location where the output of the calls.py script lies. Default: __..__/output/
* __benchID (`-b`)__ mandatory ID to differentiate between multiple benchmarkings. (equal to callID)

This script uses the output of the `calls.py` script. It is called automatically at the end of the `calls.py` script.
It stores the verified interactions from the specified file in a dictionary and calculates the rank for each interaction.
In order to achieve this, it reads the files created by the `calls.py` script and sorts the tables according to the energy.
Once the files are sorted, the row-number for each interaction in the verified interactions file is determined. 
The resulting row-number is the rank for that interaction.
The ranks are then stored in a CSV file.

__Default Output:__ (contained in the respective `callID` folder)
* benchmark.csv -> file containing the rank for each verified interaction.


#### plot_performance.py

__Parameters:__
* __benchmarkFile (`-i`)__ mandatory benchmark file used to plot the results. (created using benchmark.py eventually in compination with mergeBenchmarks.py)
* __outputFilePath (`-o`)__ the location and name of the output file. Default: IntaRNA2_benchmark.pdf .
* __separator (`-s`)__ separator used for the csv files. Default: '__;__'
* __end (`-e`)__ the upper bound of the number of target predictions. Default: 200
* __xlim (`-x`)__ specify an x-limit for the output. x_start/x_end (x is already bound by end, changing might lead to strange results)
* __ylim (`-y`)__ specify an y-limit for the output. y_start/y_end

This script uses a benchmark.csv file created by the `benchmark.py` script.
For each callID present in the benchmark file, the ranks are used to create a receiver operating characteristic (ROC) curve.
For each step from 1 to "end(200)" the number of ranks that are smaller or equal to the current step are recorded. 
These are the desired true positives.

__Default Output:__
* IntaRNA2_benchmark.pdf -> a pdf of a roc plot for all contained callIDs

#### mergeBenchmarks.py

__Parameters:__
* __outputFileName (`-o`)__ mandatory name and path of the output file.
* __outputPath (`-d`)__ location of the result directory (containing the folders of the individual callIDs).
* __benchID (`-b`)__ specific benchIDs to be merged, atleast two. benchID1/benchID2/...
* __all (`-a`)__ when set, all benchIDs in the outputPath are merged.

This script can be used to merge benchmark files and their according runTime and memoryUsage files for multiple/all benchIDs.
This can be used to easily create one file for the data of multiple benchIDs, that can be used to plot all IDs at once using `plot_performance.py`.

#### clearAll.py

__Parameters:__
* __outputPath (`-f`)__ the location of the output files that will be deleted. Default ../output/ .
* __callID (`-c`)__ specific callIDs that will be deleted. callID1/callID2/...

Script to delete specific callIDs. If no specification is made all callIDs will be deleted from the specified folder.


