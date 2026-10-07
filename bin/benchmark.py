#!/usr/bin/env python3
# Original author: Rick Gelhausen, adapted from Patrick Wright
"""Rank experimentally verified interactions in IntaRNA CSV predictions."""
import argparse
import csv
import json
from pathlib import Path
import sys

import pandas as pd


def prediction_files(directory, verified_keys):
    manifest = directory / "run.json"
    groups = {}
    if manifest.is_file():
        run = json.loads(manifest.read_text(encoding="utf-8"))
        if run["status"] not in {"running", "complete"}:
            raise ValueError("Cannot benchmark a planned or failed run")
        for job in run["predictions"]:
            path = directory / job["output"]
            if not path.is_file():
                raise ValueError("Missing prediction file: " + str(path))
            groups.setdefault((job["srna"], job["organism"]), []).append(path)
    else:
        # Backward compatibility with existing calls.py output directories.
        for srna, organism in verified_keys:
            files = [path for path in sorted(directory.glob("*.csv"))
                     if path.stem.startswith(srna + "_") and
                     (path.stem[len(srna) + 1:] == organism or path.stem.endswith("_" + organism))]
            if files:
                groups[(srna, organism)] = files
    return groups


def target_ranks(files):
    frames = []
    for path in files:
        frame = pd.read_csv(path, sep=";", dtype={"id1": str})
        if not {"id1", "E"} <= set(frame.columns):
            raise ValueError("Prediction must contain id1 and E columns: " + str(path))
        frame["E"] = pd.to_numeric(frame["E"], errors="raise").round(2)
        if frame["id1"].isna().any() or frame["E"].isna().any() or frame["E"].isin([float("inf"), -float("inf")]).any():
            raise ValueError("Missing target ID or nonfinite energy in " + str(path))
        frames.append(frame[["id1", "E"]])
    # Rank targets, not suboptimal interactions; preserve historical dense ties.
    energies = pd.concat(frames).groupby("id1")["E"].min()
    return energies.rank(method="dense", ascending=True).astype(int).to_dict()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--infile", type=Path, default=Path("verified_interactions.csv"))
    parser.add_argument("-o", "--outfile", type=Path, default=Path("benchmark.csv"))
    parser.add_argument("-p", "--callDirs", type=Path, default=Path("output"))
    parser.add_argument("-c", "--callID", required=True)
    args = parser.parse_args(argv)
    try:
        directory = args.callDirs / args.callID
        output = directory / args.outfile
        if output.exists():
            raise ValueError("Benchmark output already exists: " + str(output))
        verified = {}
        with args.infile.open(newline="", encoding="utf-8") as handle:
            for line, row in enumerate(csv.reader(handle, delimiter=";"), 1):
                if not row:
                    continue
                if len(row) < 4 or not all(row[:4]):
                    raise ValueError("Invalid verified interaction at line " + str(line))
                verified.setdefault((row[0], row[3]), []).append((row[1], row[2]))
        groups = prediction_files(directory, verified)
        rows = []
        for (srna, organism), targets in verified.items():
            files = groups.get((srna, organism))
            if not files:
                continue  # Explicitly selected datasets may cover only a subset.
            ranks = target_ranks(files)
            for target, name in targets:
                rows.append([srna, target, name, ranks.get(target, sys.maxsize)])
        if not rows:
            raise ValueError("No predictions match the verified interactions")
        with output.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(["srna_name", "target_ltag", "target_name", args.callID + "_intarna_rank"])
            writer.writerows(rows)
    except (OSError, ValueError, KeyError, pd.errors.ParserError) as error:
        parser.error(str(error))
    print("Finished benchmarking: " + args.callID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
