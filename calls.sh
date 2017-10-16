#!/bin/bash

# Author: Rick Gelhausen <rick.gelhausen@gmail.com>

# file paths

# directory containing the /src folder of IntaRNA
intaRNAPath="../IntaRNA"

fastaFilePath="./predictions"


# help text
usage=$'The following options are available:\n
intaRNAPath (-i) : path where the intaRNA src folder lies. Default: ../IntaRNA . \n
fastaPath (-f) : location where the folders containing the fasta files lies. Default: ./predictions .\n
arg (-a) : extra command line arguments applied to the intaRNA query. Like outputMode or numberOfResults . \n
seedArg (-s) : extra command line arguments for the seed predictors. Like seedBP or seedMaxUp .\n
help (-h) : print this usage. \n
Options that require an argument are called with: -o <input>\n'

# commandline parsing
while getopts hi:f:a:s: option
do
 case "${option}"
 in
 i) intaRNAPath=${OPTARG:-"../IntaRNA"};;
 f) fastaFilePath=${OPTARG:-"./predictions"};;
 a) commandLineArguments=${OPTARG:-""} ;;
 s) seedArguments=${OPTARG:-""};;
 h) echo "$usage"
    exit;;
 esac
done

# get all relevant folder names
directories=("${fastaFilePath}/*")

# declaring file names of target fasta files
targetFastaB="NC_000913_upfromstartpos_200_down_100.fa"
targetFastaSTM="NC_003197_upfromstartpos_200_down_100.fa"

for dir in ${directories[@]}
do
  # declaring file names of query fasta files
  queryFastaB="${dir##*/}_IntaRNA_NC_000913.fasta"
  queryFastaSTM="${dir##*/}_IntaRNA_NC_003197.fasta"
  
  # Trap
  trap '{ echo "Registered Ctrl-C.  Shutting down." ; exit 1; }' INT

  # Call IntaRNA with the given settings

  # Normal IntaRNA case
  # Echoli
  echo $intaRNAPath/src/bin/IntaRNA -q "${dir}/${queryFastaB}" -t "${dir}/${targetFastaB}" --pred=S --mode=E --out "${dir}/IntaRNA_Simple_000913.csv" --outMode=C ${commandLineArguments}
  $intaRNAPath/src/bin/IntaRNA -q "${dir}/${queryFastaB}" -t "${dir}/${targetFastaB}" --pred=S --mode=E --out "${dir}/IntaRNA_Simple_000913.csv" --outMode=C ${commandLineArguments}

  # Salmonella
  echo $intaRNAPath/src/bin/IntaRNA -q "${dir}/${queryFastaSTM}" -t "${dir}/${targetFastaSTM}" --pred=S --mode=E --out "${dir}/IntaRNA_Simple_003197.csv" --outMode=C ${commandLineArguments}
  $intaRNAPath/src/bin/IntaRNA -q "${dir}/${queryFastaSTM}" -t "${dir}/${targetFastaSTM}" --pred=S --mode=E --out "${dir}/IntaRNA_Simple_003197.csv" --outMode=C ${commandLineArguments}

  #

done
