#!/usr/bin/env python
import os
import argparse
import pandas as pd
import collections
import csv
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
from operator import itemgetter
import math

def natural_sort(l, key):
    """
    sort the way human expect the sorting (alpha-numerically)
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda item: [ convert(c) for c in re.split('([0-9]+)', key(item)) ]
    return sorted(l, key = alphanum_key)

def screen_files(args):
    file_paths = []
    for root, dirs, files in os.walk(args.input_folder):
        for file in files:
            if file == "benchmark.csv":
                 file_paths.append(os.path.join(root, file))
    return file_paths

def create_hits_table(file_paths):
    results = []
    folder_names = [file.split("/")[-2] for file in file_paths]

    file_paths = [list(x) for x in zip(*natural_sort(list(zip(folder_names, file_paths)), itemgetter(0)))][1]

    for file in file_paths:
        name = file.split("/")[-2]
        bench_df = pd.read_csv(file, sep=";", comment="#")
        rank_list = bench_df.iloc[:,-1].tolist()
        check_list = [1 if int(x) <=100 else 0 for x in rank_list]
        results.append([name] + check_list)
    header = ["parameters"]+[name +"-"+ tag for name, tag in zip(bench_df["srna_name"].tolist(), bench_df["target_ltag"].tolist())]

    name_list = ["s%s" % str(x) for x in range(len(header))]
    nTuple = collections.namedtuple('Pandas', name_list)
    results = [nTuple(*result) for result in results]
    return pd.DataFrame.from_records(results, columns=[header[x] for x in range(len(header))])

# def draw_heatmaps(in_df, out_name):
#     sns.set(rc={'figure.figsize':(140,100)})
#     # set index
#     in_df = in_df.set_index("parameters")
#     chunk_count = math.ceil(in_df.shape[0] / 25)
#
#     df_chunks = np.array_split(in_df, chunk_count)
#     for df in df_chunks:
#         sns.heatmap(df,cbar=False, xticklabels=True, yticklabels=True)
#         plt.show()

def main():
    # store commandline args
    parser = argparse.ArgumentParser(description='Create a table with the srna predictions.')
    parser.add_argument("-i", "--input_folder", action="store", dest="input_folder", help="input folder.")
    #parser.add_argument("-v", "--verified_targets", action="store", dest="verified_targets", help="table of verified targets")
    parser.add_argument("-o", "--output_file", action="store", dest="output_file", help="output folder for concatenated files.")
    args = parser.parse_args()

    file_paths = screen_files(args)
    out_df = create_hits_table(file_paths)
    out_df.to_csv(args.output_file, index=False, sep="\t", quoting=csv.QUOTE_NONE)

    cols = out_df.columns

    # split ecoli and salmonella
    ecoli=["parameters"]
    salmonella=["parameters"]
    for col in cols[1:]:
        if "-STM" in col:
            salmonella.append(col)
        else:
            ecoli.append(col)

    ecoli_df = out_df[ecoli].copy()
    salmonella_df = out_df[salmonella].copy()

    file_ext = args.output_file.split(".")[-1]
    # write to file
    ecoli_df.to_csv(args.output_file.split(".")[-2]+"_ecoli."+file_ext, index=False, sep="\t", quoting=csv.QUOTE_NONE)
    salmonella_df.to_csv(args.output_file.split(".")[-2]+"_salmonella."+file_ext, index=False, sep="\t", quoting=csv.QUOTE_NONE)
    # 
    #
    # salmonella_df = salmonella_df.set_index("parameters")
    # draw_heatmaps(ecoli_df, "ecoli")


if __name__ == '__main__':
    main()
