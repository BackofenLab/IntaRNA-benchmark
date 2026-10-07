#!/usr/bin/env python3
# Original author: Rick Gelhausen
"""Run the existing IntaRNA benchmark pipeline on one local computer."""
import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FASTA_SUFFIXES = {".fa", ".fasta"}


def executable(value):
    # Do not resolve symlinks: IntaRNA personalities depend on argv[0].
    found = shutil.which(value)
    if found is None:
        raise ValueError("IntaRNA executable not found or not executable: " + value)
    return os.path.abspath(found)


def runSubprocess(callArgs):
    """Return user CPU seconds and peak RSS in KiB; propagate tool failures."""
    with tempfile.NamedTemporaryFile(mode="r+", encoding="utf-8") as stats:
        subprocess.run(
            ["/usr/bin/time", "-f", "%U;%M", "-o", stats.name, "--", *callArgs],
            check=True, env={**os.environ, "LC_ALL": "C"},
        )
        stats.seek(0)
        cpu, memory = stats.read().strip().split(";")
        return float(cpu), int(memory)


def collect_inputs(input_path):
    """Validate every input before starting expensive predictions."""
    jobs = []
    outputs = set()
    for organism in sorted(p for p in input_path.iterdir() if p.is_dir()):
        groups = []
        for kind in ("query", "target"):
            folder = organism / kind
            if not folder.is_dir():
                raise ValueError("Missing input directory: " + str(folder))
            files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in FASTA_SUFFIXES)
            if not files:
                raise ValueError("No FASTA files in " + str(folder))
            for path in files:
                with path.open(encoding="utf-8") as handle:
                    count = sum(line.startswith(">") for line in handle)
                if count == 0 or (kind == "query" and count != 1):
                    raise ValueError("Each query FASTA must contain one sequence and each target FASTA at least one: " + str(path))
            groups.append(files)
        for target in groups[1]:
            for query in groups[0]:
                srna = query.stem.split("_")[0]
                output = srna + "_" + target.stem + ".csv"
                if output in outputs:
                    raise ValueError("Inputs would overwrite the same prediction file: " + output)
                outputs.add(output)
                jobs.append(dict(organism=organism.name, srna=srna, query=str(query),
                                 target=str(target), target_name=target.stem, output=output))
    if not jobs:
        raise ValueError("No benchmark datasets in " + str(input_path))
    return jobs


def option_names(arguments):
    return {arg.split("=", 1)[0] for arg in arguments if arg.startswith("-")}


def validate_arguments(arguments, with_ed):
    # The pipeline owns input/output routing. Changing these can silently rank
    # the wrong data, suppress CSV output, or include suboptimal hits as targets.
    reserved = {"-q", "--query", "-t", "--target", "--out", "--outMode",
                "--outCsvCols", "-n", "--outNumber", "--outPairwise",
                "--qSet", "--tSet", "--qId", "--tId", "--parameterFile",
                "-h", "--help", "--fullhelp", "--version"}
    if with_ed:
        reserved |= {"--tAcc", "--tAccFile", "--acc"}
    for arg in arguments:
        name = arg.split("=", 1)[0]
        if name in reserved or (arg.startswith(("-q", "-t", "-n")) and not arg.startswith("--")):
            raise ValueError("The benchmark manages this IntaRNA option: " + name)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run local IntaRNA predictions and benchmark.py, without Conda or a scheduler.",
        epilog="Pass IntaRNA options after --, e.g. -- --threads=4 --model=X. "
               "Short options after -- belong to IntaRNA, not this runner.", allow_abbrev=False)
    parser.add_argument("-b", "--intaRNAbinary", default="IntaRNA", help="executable path or name on PATH")
    parser.add_argument("-i", "--infile", type=Path, default=ROOT / "input", help="dataset directory")
    parser.add_argument("-o", "--outfile", type=Path, default=ROOT / "output", help="results directory")
    parser.add_argument("-c", "--callID", required=True, help="unique run ID (letters, digits, dot, underscore, hyphen)")
    parser.add_argument("-n", "--callsOnly", action="store_true", help="write commands without executing any IntaRNA calls")
    parser.add_argument("-e", "--withTargetED", action="store_true", help="precompute target ED once per target for this run")
    parser.add_argument("-v", "--verified", type=Path, default=ROOT / "verified_interactions.csv")
    parser.add_argument("-m", "--maxInteractionLength", type=int, help="set --tIntLenMax for precomputation AND predictions")
    parser.add_argument("-a", "--arguments", default="", help="quoted IntaRNA options (alternative to --)")
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" in argv:
        boundary = argv.index("--")
        args = parser.parse_args(argv[:boundary])
        extra = argv[boundary + 1:]
    else:
        args, extra = parser.parse_known_args(argv)
    try:
        extra = shlex.split(args.arguments) + extra
        validate_arguments(extra, args.withTargetED)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.callID):
            raise ValueError("callID must start with a letter or digit and contain only letters, digits, ., _, -")
        binary = executable(args.intaRNAbinary)
        if args.maxInteractionLength is not None:
            if args.maxInteractionLength < 0 or option_names(extra) & {"--tIntLenMax", "--intLenMax"}:
                raise ValueError("Use a nonnegative -m or an IntaRNA length option, not both")
            extra += ["--tIntLenMax=" + str(args.maxInteractionLength)]
        if "--threads" not in option_names(extra):
            extra.append("--threads=1")
        jobs = collect_inputs(args.infile.resolve())
        if not args.verified.is_file():
            raise ValueError("Verified interactions file not found: " + str(args.verified))
        if not args.callsOnly:
            if importlib.util.find_spec("pandas") is None:
                raise ValueError("Install pandas in this Python environment before running the benchmark")
            subprocess.run(["/usr/bin/time", "--version"], check=True, stdout=subprocess.DEVNULL)
        output = args.outfile.resolve() / args.callID
        output.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))

    metadata = dict(callID=args.callID, binary=binary, arguments=extra, predictions=jobs,
                    verified=str(args.verified.resolve()), status="planned" if args.callsOnly else "running",
                    runtime_unit="user CPU seconds", memory_unit="KiB", python=sys.version,
                    precomputation=[])
    manifest = output / "run.json"

    def save_metadata():
        manifest.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    save_metadata()
    try:
        if not args.callsOnly:
            metadata["version"] = subprocess.check_output([binary, "--version"], text=True, stderr=subprocess.STDOUT).strip()
            with open(binary, "rb") as handle:
                metadata["binary_sha256"] = hashlib.file_digest(handle, "sha256").hexdigest() if sys.version_info >= (3, 11) else hashlib.sha256(handle.read()).hexdigest()
            save_metadata()
        measurements = []
        ed_files = {}
        with (output / "calls.txt").open("w", encoding="utf-8") as log:
            def execute(command):
                print(shlex.join(command), file=log, flush=True)
                print(shlex.join(command), flush=True)
                if not args.callsOnly:
                    return runSubprocess(command)
                return "NA", "NA"

            for job in jobs:
                prediction_args = list(extra)
                if args.withTargetED:
                    if job["target"] not in ed_files:
                        ed_dir = output / "ED-values" / job["organism"] / job["target_name"]
                        ed_dir.mkdir(parents=True)
                        ed_file = ed_dir / "intarna.target.ed"
                        # Same binary, target and parameters as the prediction.
                        # -n 0 skips interactions but still computes accessibility.
                        ed_cpu, ed_memory = execute([binary, *extra, "-q", job["query"], "-t", job["target"],
                                 "-n", "0", "--out", os.devnull, "--out=tAcc:" + str(ed_file)])
                        metadata["precomputation"].append(dict(target=job["target"],
                                                              user_cpu_seconds=ed_cpu, peak_rss_kib=ed_memory))
                        ed_files[job["target"]] = ed_file
                    prediction_args += ["--tAcc=E", "--tAccFile=" + str(ed_files[job["target"]])]
                cpu, memory = execute([binary, *prediction_args, "-q", job["query"], "-t", job["target"],
                                       "--out", str(output / job["output"]), "--outMode=C", "--outNumber=1"])
                measurements.append((job, cpu, memory))

        # A union header keeps datasets with different query sets rectangular.
        srnas = sorted({job["srna"] for job in jobs})
        for filename, index in (("runTime.csv", 1), ("memoryUsage.csv", 2)):
            rows = {}
            for entry in measurements:
                job = entry[0]
                key = (job["target_name"], job["organism"])
                rows.setdefault(key, dict(callID=args.callID, target_name=key[0], Organism=key[1]))[job["srna"]] = entry[index]
            with (output / filename).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, ["callID", "target_name", "Organism", *srnas], delimiter=";", restval="NA")
                writer.writeheader()
                writer.writerows(rows.values())
        if not args.callsOnly:
            subprocess.run([sys.executable, str(ROOT / "bin" / "benchmark.py"), "-c", args.callID,
                            "-i", str(args.verified.resolve()), "-p", str(args.outfile.resolve())], check=True)
            metadata["status"] = "complete"
        save_metadata()
    except (OSError, ValueError, subprocess.CalledProcessError, KeyboardInterrupt) as error:
        metadata["status"] = "failed"
        metadata["error"] = str(error)
        save_metadata()
        print("Benchmark failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
