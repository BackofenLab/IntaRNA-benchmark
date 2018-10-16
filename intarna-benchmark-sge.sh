#!/bin/bash
#$ -N IntaRNA-benchmark
#$ -cwd
#$ -pe smp 8
#$ -l h_vmem=1G
#$ -o <folder path>
#$ -e <folder path>
#$ -j y
#$ -M <email address>
#$ -m a

#source activate intarna-benchmark

# Variables
intaRNAbinary="../intaRNA/src/bin/"
inputPath="./input/"
outputPath="./output/"
intaRNACall=""
callID=""
withED=false

# Handling input
while getopts "h?b:i:o:a:c:e" opt; do
    case "$opt" in
    h|\?)
        exit 0
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
  python bin/calls.py -b $intaRNAbinary -i $inputPath -o $outputPath -c $callID $intaRNACall -e
else
  python bin/calls.py -b $intaRNAbinary -i $inputPath -o $outputPath -c $callID $intaRNACall
fi
