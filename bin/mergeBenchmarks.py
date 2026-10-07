#!/usr/bin/env python3
# Original author: Rick Gelhausen
"""Merge matching benchmark runs and their runtime/memory tables."""
import argparse
import json
from pathlib import Path
import sys

import pandas as pd

KEYS = ["srna_name", "target_ltag", "target_name"]


def completed_run(directory):
    manifest = directory / "run.json"
    return not manifest.exists() or json.loads(manifest.read_text(encoding="utf-8"))["status"] == "complete"


def merged_benchmarks(paths):
    result = pd.read_csv(paths[0], sep=";", dtype={key: str for key in KEYS})
    if result.empty or result.duplicated(KEYS).any():
        raise ValueError("Benchmark must have nonempty, unique interaction keys: " + str(paths[0]))
    for path in paths[1:]:
        other = pd.read_csv(path, sep=";", dtype={key: str for key in KEYS})
        if (set(result.columns) & set(other.columns)) - set(KEYS):
            raise ValueError("Duplicate run columns in " + str(path))
        result = result.merge(other, on=KEYS, how="outer", validate="one_to_one", indicator=True)
        if not result["_merge"].eq("both").all():
            raise ValueError("Benchmarks cover different verified interactions; refusing to drop rows")
        result = result.drop(columns="_merge")
    return result.reindex(columns=KEYS + sorted(set(result.columns) - set(KEYS)))


def mergeBenchmarks(benchList, outputPath):
    merged_benchmarks(benchList).to_csv(outputPath, sep=";", index=False)


def merged_logs(ids, directory, filename):
    frames = []
    for call_id in ids:
        frame = pd.read_csv(directory / call_id / filename, sep=";", dtype={"callID": str, "target_name": str, "Organism": str})
        if frame.empty or not frame["callID"].eq(call_id).all():
            raise ValueError("Incorrect callID or empty log: " + str(directory / call_id / filename))
        if frame.duplicated(["target_name", "Organism"]).any():
            raise ValueError("Duplicate target/organism measurements in " + call_id)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True).sort_values(["callID", "Organism", "target_name"])


def mergeLogFiles(callIDList, benchPath, outputpath):
    base = Path(outputpath).with_suffix("")
    for filename, suffix in (("runTime.csv", "_runTimes.csv"), ("memoryUsage.csv", "_MaxMemoryUsage.csv")):
        merged_logs(callIDList, Path(benchPath), filename).to_csv(str(base) + suffix, sep=";", index=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--ifile", default="benchmark.csv")
    parser.add_argument("-o", "--ofile", type=Path, required=True)
    parser.add_argument("-d", "--bdirs", type=Path, default=Path("output"))
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("-c", "--callID", nargs="+")
    selection.add_argument("-a", "--all", action="store_true")
    args = parser.parse_args(argv)
    try:
        ids = args.callID if not args.all else sorted(path.name for path in args.bdirs.iterdir()
                                                     if path.is_dir() and (path / args.ifile).is_file() and completed_run(path))
        if len(ids) < 2 or len(ids) != len(set(ids)):
            raise ValueError("Select at least two different completed callIDs")
        for call_id in ids:
            if not completed_run(args.bdirs / call_id):
                raise ValueError("Run is not complete: " + call_id)
        # Read and validate everything before writing any merged output.
        benchmark = merged_benchmarks([args.bdirs / call_id / args.ifile for call_id in ids])
        runtime = merged_logs(ids, args.bdirs, "runTime.csv")
        memory = merged_logs(ids, args.bdirs, "memoryUsage.csv")
        base = str(args.ofile.with_suffix(""))
        outputs = [(args.ofile, benchmark), (Path(base + "_runTimes.csv"), runtime),
                   (Path(base + "_MaxMemoryUsage.csv"), memory)]
        for path, _ in outputs:
            if path.exists():
                raise ValueError("Merged output already exists: " + str(path))
        args.ofile.parent.mkdir(parents=True, exist_ok=True)
        for path, frame in outputs:
            frame.to_csv(path, sep=";", index=False)
    except (OSError, ValueError, KeyError, pd.errors.ParserError, pd.errors.MergeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
