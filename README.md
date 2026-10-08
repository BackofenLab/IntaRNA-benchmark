# IntaRNA-benchmark
Data and scripts to benchmark IntaRNA.

### Run locally (no Conda or cluster required)

Use a locally installed IntaRNA executable, Python >= 3.8, and **GNU time**
(`/usr/bin/time`, available on Linux). Prediction and ranking require pandas;
plotting also requires matplotlib and NumPy. An ordinary Python environment is
sufficient; an optional virtual environment can be set up with:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

From this repository, run:

```bash
./intarna-benchmark-local -b /path/to/IntaRNA -c intarna-default
./intarna-benchmark-local -b /path/to/IntaRNA -c intarna-X -- --model=X --threads=4
```

`-b` also accepts a name on `PATH` (the default is `IntaRNA`), including
personality executables such as `IntaRNAkix`. The runner uses the invoking Python
interpreter, processes query/target files sequentially on one computer, and
adds `--threads=1` unless a thread count is supplied. It calls `bin/calls.py`,
which calls the existing `bin/benchmark.py` after successful predictions.
The usual CSV filenames and columns are retained.

The entry point can be called from any working directory. Its default input,
output and verified-interaction paths are relative to the repository; explicit
paths are relative to the caller's directory. Use `--help` for all options:

| Option | Purpose |
| --- | --- |
| `-b PATH_OR_NAME` | Locally installed executable (no downloading or building) |
| `-c ID` | Required unique run ID; existing output is never overwritten |
| `-i DIRECTORY` | Input datasets, default: repository `input/` |
| `-o DIRECTORY` | Parent result directory, default: repository `output/` |
| `-v FILE` | Verified interactions, default: repository `verified_interactions.csv` |
| `-n` | Dry run: log commands and `NA` measurements; execute **no** IntaRNA commands |
| `-e` | Precompute target ED once per target file within this run |
| `-m LENGTH` | Explicitly set `--tIntLenMax` in both precomputation and prediction |
| `-a 'OPTIONS'` | Quoted IntaRNA options, an alternative to arguments after `--` |

Put IntaRNA options after `--` to avoid short-option collisions. For example,
`-- -m M` selects IntaRNA's exact mode, while the runner's own `-m` sets a length.
Input/output routing, CSV columns, query/target subsets, parameter files and
number of predictions are managed by the runner. Each target contributes its
best interaction (`--outNumber=1`); one query sequence per query FASTA is required.

Preview a run in its own output directory before launching an expensive job:

```bash
./intarna-benchmark-local -b /path/to/IntaRNA -c preview -n -- --model=X
```

Use a different call ID for the real run. A failed command stops the pipeline
with a nonzero exit status. Partial outputs remain available for diagnosis;
`run.json` records whether the run is planned, running, failed or complete.
It also records the executable path, version, SHA-256, actual IntaRNA arguments,
input paths and measurement units. `calls.txt` contains shell-quoted commands.

### Merge and plot local results

```bash
python3 bin/mergeBenchmarks.py -d output -c intarna-default intarna-X -o output/comparison.csv
python3 bin/plot.py -i output/comparison.csv -o output/comparison.pdf \
  --referenceID intarna-default --config config.txt --title 'Local comparison' --time --memory
```

The merge produces `comparison.csv`, `comparison_runTimes.csv` and
`comparison_MaxMemoryUsage.csv`. Plotting produces `comparison.pdf`,
`comparison_runtime.pdf` and `comparison_memory.pdf`. Merging rejects different
sets of verified interactions instead of silently discarding rows. `-a` merges
all completed benchmark directories and ignores ED caches and dry runs. Use a
fresh output filename for each merge.

Runtime CSVs contain **user CPU seconds**, not wall-clock seconds. Memory CSVs
contain **peak RSS in KiB** (the historical raw GNU-time units); plots convert
them to minutes and MiB. ED precomputation is excluded from per-prediction
measurements and recorded separately in `run.json`. CPU percentage differences
use the reference as denominator and exclude zero reference times.

### Prepare the IntaRNAkix benchmark (IntaRNA issue 255)

Use a recent local build that supports `--personality=IntaRNAkix` and
`--kineticScore=A/B/C`. The example below prepares the 11 configurations from
[BackofenLab/IntaRNA#255](https://github.com/BackofenLab/IntaRNA/issues/255):
one default run, four `--model=X` baseline runs crossing `--outNoLP=false/true`
with the GU constraint, and six IntaRNAkix runs crossing scores A/B/C with that
constraint. The default baseline is kept separate from the seed-extension
model X baseline. IntaRNAkix always uses no-lonely-pair extensions.

```bash
# Inspect all calls without executing IntaRNA.
./examples/benchmark-kix.sh /path/to/recent/IntaRNA -m 80 -o output/kix-plan -n

# Run on the bundled datasets (potentially lengthy).
./examples/benchmark-kix.sh /path/to/recent/IntaRNA -m 80 -o output/kix-results

python3 bin/mergeBenchmarks.py -d output/kix-results -a -o output/kix-comparison.csv
python3 bin/plot.py -i output/kix-comparison.csv -o output/kix-comparison.pdf \
  -r intarna-default -c config.txt --time --memory
```

The issue's shorthand **noGU is provisionally interpreted as `--outNoGUend=true`**
(no GU pairs at interaction ends). It is not a ban on all GU pairs. To instead
constrain seeds use `GU_OPTION=seedNoGU`; to enable both constraints use
`GU_OPTION=both` before the example command. The exact choice is retained in each
run's command log and manifest. The script accepts runner options such as `-i`,
`-v`, `-e`, and `-a '--threads=4'`. Use the standard `IntaRNA` executable so the
default baseline retains its normal personality. Use separate output directories
when changing the GU interpretation or binary version.

For a quick installation check, create a small input directory with the same
organism/query/target layout and pass `-i` and a corresponding `-v` file. A smoke
run verifies the pipeline; it does not establish biological or performance
conclusions for the full datasets.

### Validation and legacy entry points

```bash
python3 -m unittest discover -s tests -v
```

The regression suite uses a small executable fixture, does not require IntaRNA,
and covers failure propagation, paths with spaces, dry runs, ED reuse, ranking,
merging and plotting. Real-binary smoke validation for this update used IntaRNA
3.4.1 with ViennaRNA 2.7.2, two queries and three targets per organism: all 11
configurations completed, and direct/default versus precomputed-ED predictions
matched byte for byte. The full benchmark is prepared, not claimed as completed.

`intarna-benchmark-sge.sh` and `intarna-plotting.sh` are historical,
installation-specific cluster wrappers. For local work use the commands above.
The maintained plotting path is `bin/plot.py`; the older `plot_performance.py`
and `plot_boxes.py` scripts are retained for historical analyses.

### Setup
The `input` directory contains folders representing certain organisms (here Salmonella and E. coli) or benchmark data sets.
Each has to contain two folders, one holding the `query` RNAs and one holding the `target` RNAs. Each query FASTA contains exactly one sequence; target FASTAs may contain many sequences. Use `.fa` or `.fasta` extensions.

The `output` directory contains a folder for each `callID` (see parameters of `calls.py`) holding all the result files for that specific callID.
This folder is initially empty and is filled using the benchmark scripts.

The `bin` folder holds various different scripts used in the benchmarking process.

A required file is the `verified_interactions.csv`. The file contains interactions that were verified experimentally. The current data set covers interactions for
- Echericha coli (GenBank accession number NC_000913)
- Salmonella typhimurium (NC_003197)

### Theoretical background
The idea is to compare the output of different IntaRNA calls with the experimentally verified interactions.
In order to achieve this, the `calls.py` script is used on the query and target files for each benchmark data set (in `input` folder)  using the specified IntaRNA call.
This results in a result file for each data set and query RNA.
These files contain the interaction results produced by IntaRNA.

Predictions are ranked from the most favorable (lowest energy) to the least favorable interaction (highest energy) during analysis.
The hope is that the verified interactions for each query RNA are amongst the first entries of each file, i.e they have low energy.
For each verified target, energies are rounded to two decimal places and ranked
in ascending order. Equal energies share a dense rank (1, 2, 2, 3); a missing
prediction receives `sys.maxsize` and never counts as a recovered interaction
at the plotted thresholds. When a target occurs more than once, only its best
energy contributes. Target shards for the same query and organism are ranked
together. Lower ranks indicate better recovery. Explicit input subsets produce
rows only for query/organism combinations included in that run.

In order to visualize the results, a receiver operating characteristic (ROC) curve is used.
It is created using the ranks determined earlier.
The X-axis describes the number of target predictions per query RNA, while the Y-axis represents
the number of true positives.
This means that for each X, the number of ranks that are smaller or equal to X are counted and represented on the Y-axis.
Like this, multiple callIDs can be plotted into the same graph to compare the performance.

### Scripts

The scripts are contained in the bin folder.
The analysis script defaults expect calls from the repository root. `calls.py` and the local entry point resolve their defaults relative to the repository.

#### calls.py
__Parameters:__
* __intaRNAbinary (`-b`)__ the path of the intaRNA executable. Default: `IntaRNA` on `PATH`
* __infile (`-i`)__ location of the folder containing folders for each organism. The organism folders have to contain a query and a target folder holding the according fasta files. Default: `./input/`
* __outfile (`-o`)__ location of the output folder. The script will add a folder for each callID. Default: `./output/`
* __callID (`-c`)__ is a mandatory ID to differentiate between multiple calls of the script.
* __withTargetED (`-e`)__ allows the precomputation of target ED-values in order to avoid recomputation.
* __callsOnly (`-n`)__ generates the calls and saves them in a log file without starting the process.
* __verified (`-v`)__ the path and file containing the verified interactions.
* __maxInteractionLength (`-m`)__ The maximum target interaction length for both precomputation and prediction. Default: use the binary's own settings

__IMPORTANT:__ Arguments for IntaRNA can be added at the end of the script call and will be redirected to IntaRNA. `python3 bin/calls.py -c callID -- --model=X`

This script calls IntaRNA from `intaRNAPath` using the queries and targets for all data sets found within the `inputPath` (see above) and the additional parameterization provided by `arg`.
IntaRNA writes predictions directly into CSV files under `outputPath/callID`.
There are many different controls to assure that no files are overwritten and that the required files are available.

The time (in seconds) and peak resident memory (in KiB) required to handle each call is also measured and represented in a table.
The tables are also stored in the specified `outputPath`. The individual calls are also logged into a log file.

With `-e`, target ED files are precomputed under
`output/<callID>/ED-values/<organism>/<target>/` and reused by queries within
that run. Precomputation uses the same binary, accessibility/energy parameters
and interaction length as prediction. Caches are isolated per run to prevent
reuse across different settings or binaries. Omit `-e` to use normal direct
accessibility computation; the default interaction length is never overridden.
`-e` cannot be combined with explicit `--tAcc`, `--tAccFile` or `--acc` options.

Calls the benchmark.py using the specified callID as benchID.

__Output:__ (contained in the respective callID folder)
* (query)_(target).csv -> intarna output for a specific query-target combination (FASTA names used)
* calls.txt -> log file for the calls
* runTime.csv -> table with runtimes for each query-target combination.
* memoryUsage.csv -> table with peak RSS in KiB for each query-target combination.
* run.json -> provenance, input/output mapping, status and ED precomputation measurements.

#### benchmark.py

__Parameters:__
* __infile (`-i`)__ the location of the file containing the experimentally verified interactions. Default: `./verified_interactions.csv`
* __outfile (`-o`)__ the name of the output file. Default: `benchmark.csv` within the callID directory
* __callDirs (`-p`)__ the location where the output of the calls.py script lies. Default: `./output/`
* __callID (`-c`)__ mandatory ID to differentiate between multiple benchmarkings.

This script uses the output of the `calls.py` script. It is called automatically at the end of the `calls.py` script.
It matches predictions to verified query/organism pairs, computes the dense
energy ranks described above, and writes the result CSV. New runs use the exact
input mapping from `run.json`; historical runs use query and organism filenames.
Malformed predictions and empty benchmark matches fail with a nonzero status.

__Default Output:__ (contained in the respective `callID` folder)
* benchmark.csv -> file containing the rank for each verified interaction.

#### plot.py

__Parameters:__
* __benchmarkFile (`-i`)__ mandatory benchmark file used to plot the results. (created using benchmark.py eventually in compination with mergeBenchmarks.py)
* __outputFilePath (`-o`)__ required location and name of the output file.
* __separator (`-s`)__ separator used for the csv files. Default: `;`
* __config (`-c`)__ path to the required configuration file.
* __title (`-n`, `--title`)__ the title of the main plot (currently not in config file to allow easier changing via script).
* __referenceID (`-r`)__ the ID used to create the reference curve for violin plots.
* __plottype (`-p`)__ the supported type is `merged` (ROC and violin).
* __time (`-t`, `--time`)__ create the runtime plot.
* __memory (`-m`, `--memory`)__ create the memory plot.

__This is the maintained plotting script.__
This plotting script requires a `config.txt` as provided in the github repository. This allows a complete costumization of the plots without changing the code.
The script can currently output combined ROC/violin plots showing the performance of a given IntaRNA call.
Further, it can also plot the time and memory consumption for the given call.

#### plot_performance.py

__Parameters:__
* __benchmarkFile (`-i`)__ mandatory benchmark file used to plot the results. (created using benchmark.py eventually in compination with mergeBenchmarks.py)
* __outputFilePath (`-o`)__ the location and name of the output file. Default: IntaRNA2_benchmark.pdf .
* __separator (`-s`)__ separator used for the csv files. Default: `;`
* __end (`-e`)__ the upper bound of the number of target predictions. Default: 200
* __xlim (`-x`)__ specify an x-limit for the output. x_start/x_end (x is already bound by end, changing might lead to strange results)
* __ylim (`-y`)__ specify an y-limit for the output. y_start/y_end

__UNDER REPLACEMENT: Will be removed after plot.py script is fully functional__
This script uses a benchmark.csv file created by the `benchmark.py` script.
For each callID present in the benchmark file, the ranks are used to create a receiver operating characteristic (ROC) curve.
For each step from 1 to "end(200)" the number of ranks that are smaller or equal to the current step are recorded.
These are the desired true positives.

__Default Output:__
* IntaRNA2_benchmark.pdf -> a pdf of a roc plot for all contained callIDs

#### plot_boxes.py

__Parameters:__
* __benchmarkFile (`-i`)__ mandatory benchmark file used to plot the results. (created using benchmark.py eventually in compination with mergeBenchmarks.py)
* __outputFilePath (`-o`)__ the location and name of the output file. Default: IntaRNA2_benchmark.pdf .
* __separator (`-s`)__ separator used for the csv files. Default: `;`
* __title (`-t`)__ title for the plot
* __rankThreshold (`-r`)__ thresholds for which the boxplots are created. Default: 5 10 50 100 200
* __fixedID (`-f`)__ the callID for the reference curve (needed for the boxplots)

This script uses a benchmark.csv file created by the `benchmark.py` script.
For each callID present in the benchmark file, the ranks are used to create a receiver operating characteristic (ROC) curve.
The data plotted is the number of ranks smaller or equal to the currently allowed target predictions. [0-max(threshold)]
The data from the ROC curve is used to create a difference measure between each curve and the reference curve (defined by fixedID).
This is visualized using boxplots for different target prediction thresholds (user-defineable).
The upper bound of the x-axis is taken from the thresholds. Default: 200.


#### mergeBenchmarks.py

__Parameters:__
* __outputFileName (`-o`)__ mandatory name and path of the output file.
* __outputPath (`-d`)__ location of the result directory (containing the folders of the individual callIDs).
* __callID (`-c`)__ specific callIDs to be merged, at least two. benchID1 benchID2 ...
* __all (`-a`)__ when set, all benchIDs in the outputPath are merged.

This script can be used to merge benchmark files and their according runTime and memoryUsage files for multiple/all benchIDs.
This can be used to easily create one file for the data of multiple benchIDs, that can be used to plot all IDs at once using `plot.py`.

#### clearAll.py

__Parameters:__
* __outputPath (`-f`)__ the location of the output files that will be deleted. Default ../output/ .
* __callID (`-c`)__ specific callIDs that will be deleted. callID1/callID2/...

Script to delete specific callIDs. If no specification is made all callIDs will be deleted from the specified folder.
