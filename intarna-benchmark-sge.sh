#!/bin/bash
#$ -N intaRNA-benchmark
#$ -cwd
#$ -pe smp 8
#$ -l h_vmem=1G
#$ -o <path to the working folder>
#$ -e <path to the working folder>
#$ -j y
#$ -M <email address if desired>
#$ -m a

# This script will require a conda environment with:
# - the necessary dependencies of intaRNA
# - python3 | pandas
export PATH="<path to miniconda>/miniconda3/bin/:$PATH"
cd <path to the working folder>
source activate intarna-benchmark

# Variables
scriptsPath="./bin/"
intaRNAbinary="../intaRNA/src/bin/"
inputPath="./input/"
outputPath="./output/"
intaRNACall=""
callID=""
withED=false

# Handling input
while getopts "h?s:b:i:o:a:c:e" opt; do
    case "$opt" in
    h|\?)
        exit 0
        ;;
    s)  scriptsPath=$OPTARG
        ;;
    b)  intaRNAbinary=$OPTARG
        ;;
    i)  inputPath=$OPTARG
        ;;
    o)  outputPath=$OPTARG
        ;;
    a)  intaRNACall=$OPTARG
        ;;
    c)  callID=$OPTARG
        ;;
    e)  withED=true
        ;;
    esac
done

# Enforce callID
if [ "$callID" == "" ]
then
  echo "No callID specified. Please specify a callID using -c <callID>"
  exit;
fi

# Run benchmark
if [ "$withED" == true ]
then
  python3 $scriptsPath/calls.py -b $intaRNAbinary -i $inputPath -o $outputPath -c $callID $intaRNACall -e
else
  python3 $scriptsPath/calls.py -b $intaRNAbinary -i $inputPath -o $outputPath -c $callID $intaRNACall
fi
