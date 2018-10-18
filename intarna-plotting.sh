#!/bin/bash
#$ -N intaRNA-benchmark
#$ -cwd
#$ -pe smp 1
#$ -l h_vmem=2G
#$ -o <folder path>
#$ -e <folder path>
#$ -j y
#$ -M <email address>
#$ -m a

# This script will require a conda environment with:
# - python3 | pandas | matplotlib
export PATH="<path to miniconda>/miniconda3/bin/:$PATH"
cd <path to the working folder>
source activate intarna-plotting

# Variables
scriptsPath="./bin/"
inputPath="./output/"
outputPath="./plots/intaRNA.pdf"
all=false
fixedID=""
plotTitle=""
plotEnd="200"

# Handling input
while getopts "h?i:o:c:b:f:t:e:a" opt; do
    case "$opt" in
    h|\?)
        exit 0
        ;;
    b)  scriptsPath=$OPTARG
        ;;
    i)  inputPath=$OPTARG
        ;;
    o)  outputPath=$OPTARG
        ;;
    c)  callIDs+=("$OPTARG")
        ;;
    a)  all=true
        ;;
    f)  fixedID=$OPTARG
        ;;
    t)  plotTitle=$OPTARG
        ;;
    e)  plotEnd=$OPTARG
        ;;
    esac
done

# unique output file
tmpOutput="./tmp/mergedBenchmark_$(date +%Y%m%d%H%M%S).csv"

# Enforce callID
if [ "$callIDs" == "" ]
then
  echo "No callID specified. Please specify a callID using -c <callID>"
  exit;
fi

# merge benchmarks
if [ "$all" == true ]
then
  python3 $scriptsPath/mergeBenchmarks.py -b $callIDs -d $inputPath -o $tmpOutput -a
else
  python3 $scriptsPath/mergeBenchmarks.py -b $callIDs -d $inputPath -o $tmpOutput
fi

if [ "$fixedID" != "" ]
then
  fixedID="-f $fixedID"
fi

# plot
python3 $scriptsPath/plot_performance.py -i $tmpOutput -o $outputPath $fixedID -t $plotTitle -e $plotEnd
