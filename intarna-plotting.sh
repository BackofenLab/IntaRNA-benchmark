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
plotTitle="''"
plotEnd="200"
remove=false

# Handling input
while getopts "h?i:o:c:b:f:t:e:ra" opt; do
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
    r)  remove=true
        ;;
    esac
done

# Enforce callID
if [ "$callIDs" == "" ]
then
  echo "No callID specified. Please specify a callID using -c <callID>!"
  exit;
fi

if [ "$fixedID" == "" ]
then
  echo "Please specify a reference curve for the violin plot using -f <callID>!"
  exit;
fi

# unique output file
tmpOutput="./tmp/mergedBenchmark_$(date +%Y%m%d%H%M%S).csv"
mkdir -p ./tmp
mkdir -p ./plots

# merge benchmarks
if [ "$all" == true ]
then
  python3 $scriptsPath/mergeBenchmarks.py -c ${callIDs[@]} -d $inputPath -o $tmpOutput -a
else
  python3 $scriptsPath/mergeBenchmarks.py -c ${callIDs[@]} -d $inputPath -o $tmpOutput
fi

# plot
python3 $scriptsPath/plot_performance.py -i $tmpOutput -f $fixedID -o $outputPath -t $plotTitle -e $plotEnd

# remove temporary files if wanted
if [ "$remove" == true ]
then
  rm "${tmpOutput%.csv}"*
fi
