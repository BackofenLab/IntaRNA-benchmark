#!/usr/bin/python
# Author: Rick Gelhausen, adapted from perl script by Patrick Wright
import sys, getopt
import csv
import os.path

def main(argv):
   verified_interactions = 'verified_interactions.csv'
   outputfile = 'benchmark.csv'
   directoryPaths = './predictions'
   try:
      opts, args = getopt.getopt(argv,"hi:o:p:",["ifile=","ofile=","pdirs="])
   except getopt.GetoptError:
      print('benchmark.py -i <verified_interactions.csv> -o <benchmark.csv> -p <directoryPaths>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('benchmark.py -i <verified_interactions.csv> -o <benchmark.csv> -p <directoryPaths>')
         sys.exit()
      elif opt in ("-i", "--ifile"):
         verified_interactions = arg
      elif opt in ("-o", "--ofile"):
         outputfile = arg
      elif opt in ("-p", "--pdirs"):
         directoryPaths = arg

   print('Input file is ', verified_interactions)
   print('Output file is ', outputfile)

   # read verified interactions
   if os.path.exists(verified_interactions) == True:
      data = open(verified_interactions)
      confirmed_hybrids = list(csv.reader(data))
   else:
      print("Error: %s ! File not found!" % (verified_interactions))
      sys.exit(0)

   # Get all directories with needed files
   dirs = ([x[0] for x in os.walk(directoryPaths)])[1:]

   #
   resultDirectory = ""

   #
   for confirmed_hybrid in confirmed_hybrids:
      split = confirmed_hybrid[0].split(";")
      srna_name = split[0]
      target_ltag = split[1]
      target_name = split[2]
      for dir in dirs:
         if (dir.split("/")[-1] == srna_name):
            if ("STM" in target_ltag):
               intaRNA_rank = os.system("grep -Poni %s %s | head -n1 | awk -F':' '{ print $1 }'" % (target_ltag, resultDirectory))
            else:
               intaRNA_rank = os.system("grep -Poni %s %s | head -n1 | awk -F':' '{ print $1 }'" % (target_ltag, resultDirectory))

   print(dirs)

if __name__ == "__main__":
   main(sys.argv[1:])