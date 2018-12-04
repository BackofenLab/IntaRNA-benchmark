#!/bin/bash
#$ -N intaRNA-plotting
#$ -cwd
#$ -pe smp 1
#$ -l h_vmem=2G
#$ -o /scratch/bi03/gelhausr/intaRNA/IntaRNA-benchmark/
#$ -e /scratch/bi03/gelhausr/intaRNA/IntaRNA-benchmark/
#$ -j y

# This script will require a conda environment with:
# - python3 | pandas | matplotlib
export PATH="/scratch/bi03/gelhausr/miniconda3/bin/:$PATH"
cd /scratch/bi03/gelhausr/intaRNA/IntaRNA-benchmark/
source activate intarna-plotting

# Variables
scriptsPath="./bin/"
inputPath="./output/"
outputPath="./plots/intaRNA.pdf"
all=false
referenceID=""
plotTitle="''"
delete=false
additional=false
config="./config.txt"

# Handling input
while getopts "h?i:o:c:b:f:t:p:r:f:dam" opt; do
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
    r)  referenceID=$OPTARG
        ;;
    t)  plotTitle=$OPTARG
        ;;
    p)  plottype=$OPTARG
        ;;
    d)  delete=true
        ;;
    f)  config=$OPTARG
        ;;
    m)  additional=true
    esac
done

# Enforce callID
if [ "$callIDs" == "" ]
then
  echo "No callID specified. Please specify a callID using -c <callID>!"
  exit;
fi

if [ "$referenceID" == "''" ]
then
  echo "Please specify a reference curve for the violin plot using -r <callID>!"
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
if [ "$additional" == true ] 
then
  python3 $scriptsPath/plot.py -i $tmpOutput --referenceID $referenceID -o $outputPath -t "$plotTitle" --config $config --plottype $plottype --additional
else
  python3 $scriptsPath/plot.py -i $tmpOutput --referenceID $referenceID -o $outputPath -t "$plotTitle" --config $config --plottype $plottype
fi

# remove temporary files if wanted
if [ "$delete" == true ]
then
  rm "${tmpOutput%.csv}"*
fi
