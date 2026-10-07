"""Regression coverage for the local runner and scientific result processing."""
import csv
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "bin" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAKE = '''#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as handle:
    handle.write(json.dumps(args) + "\\n")
if args == ["--version"]:
    print("IntaRNA fixture")
    sys.exit(0)
if "--fail" in args:
    print("deliberate prediction failure", file=sys.stderr)
    sys.exit(7)
if "-n" in args:
    ed = next(a.split(":", 1)[1] for a in args if a.startswith("--out=tAcc:"))
    pathlib.Path(ed).write_text("ED fixture")
    sys.exit(0)
for arg in args:
    if arg.startswith("--tAccFile="):
        assert pathlib.Path(arg.split("=", 1)[1]).is_file()
print("diagnostic with: colon", file=sys.stderr)
out = pathlib.Path(args[args.index("--out") + 1])
if "--bad-csv" in args:
    out.write_text("bad;header\\n1;2\\n")
else:
    out.write_text("id1;E\\nb2;-4.001\\nb1;-5.001\\nb3;-4.004\\n")
'''


class LocalPipeline(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="benchmark test ")
        self.base = Path(self.temp.name)
        self.binary = self.base / "local IntaRNA"
        self.binary.write_text(FAKE)
        self.binary.chmod(0o755)
        self.log = self.base / "invocations.jsonl"
        self.env = {**os.environ, "FAKE_LOG": str(self.log), "MPLCONFIGDIR": str(self.base / "mpl")}
        self.input = self.base / "input data"
        for kind in ("query", "target"):
            (self.input / "org" / kind).mkdir(parents=True)
        (self.input / "org" / "query" / "ArcZ_org.fa").write_text(">ArcZ\nACGUACGU\n")
        (self.input / "org" / "query" / "ChiX_org.fa").write_text(">ChiX\nACGUACGU\n")
        (self.input / "org" / "target" / "org.fa").write_text(">b1\nACGUACGU\n")
        self.verified = self.base / "verified data.csv"
        self.verified.write_text("ArcZ;b1;one;org\nArcZ;b3;three;org\nArcZ;b9;missing;org\nChiX;b2;two;org\n")
        self.output = self.base / "output data"

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *args, success=True):
        process = subprocess.run([sys.executable, *map(str, args)], cwd=self.base,
                                 env=self.env, text=True, capture_output=True)
        self.assertEqual(process.returncode == 0, success, process.stdout + process.stderr)
        return process

    def run_local(self, call_id="test", *options, success=True):
        return self.command(ROOT / "intarna-benchmark-local", "-b", self.binary,
                            "-i", self.input, "-o", self.output, "-v", self.verified,
                            "-c", call_id, *options, success=success)

    def read_csv(self, path):
        with path.open() as handle:
            return list(csv.DictReader(handle, delimiter=";"))

    def test_quoted_paths_ranks_units_and_provenance(self):
        self.run_local("quoted", "--", "--energyFile", "path with spaces", "--threads=2")
        run = json.loads((self.output / "quoted" / "run.json").read_text())
        self.assertEqual(run["status"], "complete")
        self.assertEqual(run["memory_unit"], "KiB")
        self.assertEqual(len(run["binary_sha256"]), 64)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertIn("path with spaces", calls[1])
        self.assertNotIn("--threads=1", calls[1])
        rows = self.read_csv(self.output / "quoted" / "benchmark.csv")
        self.assertEqual([int(row["quoted_intarna_rank"]) for row in rows], [1, 2, sys.maxsize, 2])
        self.assertGreater(int(self.read_csv(self.output / "quoted" / "memoryUsage.csv")[0]["ArcZ"]), 0)

    def test_dry_run_with_ed_executes_nothing(self):
        self.run_local("dry", "-n", "-e")
        self.assertFalse(self.log.exists())
        self.assertFalse((self.output / "dry" / "benchmark.csv").exists())
        self.assertEqual(len((self.output / "dry" / "calls.txt").read_text().splitlines()), 3)
        self.assertEqual(self.read_csv(self.output / "dry" / "runTime.csv")[0]["ArcZ"], "NA")

    def test_ed_precomputed_once_per_target_and_preserves_settings(self):
        self.run_local("ed", "-e", "-m", "60", "--", "--tAccW=90", "--tAccL=60", "--temperature=25")
        calls = [json.loads(line) for line in self.log.read_text().splitlines()][1:]
        self.assertEqual(len(calls), 3)
        self.assertIn("-n", calls[0])
        for call in calls:
            self.assertIn("--tIntLenMax=60", call)
            self.assertIn("--temperature=25", call)
            self.assertIn("--tAccW=90", call)
        self.assertIn("--tAcc=E", calls[1])

    def test_prediction_failure_propagates(self):
        result = self.run_local("failure", "--", "--fail", success=False)
        self.assertIn("deliberate prediction failure", result.stderr)
        self.assertFalse((self.output / "failure" / "benchmark.csv").exists())
        self.assertEqual(json.loads((self.output / "failure" / "run.json").read_text())["status"], "failed")

    def test_precomputation_failure_stops_before_predictions(self):
        self.run_local("ed-failure", "-e", "--", "--fail", success=False)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(len(calls), 2)  # version, then failing precomputation
        self.assertIn("-n", calls[-1])
        self.assertFalse((self.output / "ed-failure" / "benchmark.csv").exists())

    def test_different_query_sets_produce_rectangular_logs(self):
        for kind in ("query", "target"):
            (self.input / "other" / kind).mkdir(parents=True)
        (self.input / "other" / "query" / "ArcZ_other.fa").write_text(">ArcZ\nACGUACGU\n")
        (self.input / "other" / "target" / "other.fa").write_text(">b1\nACGUACGU\n")
        self.run_local("sets", "-n")
        rows = self.read_csv(self.output / "sets" / "runTime.csv")
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(set(row) == {"callID", "target_name", "Organism", "ArcZ", "ChiX"} for row in rows))
        self.assertEqual(rows[1]["ChiX"], "NA")

    def test_multiple_queries_in_one_fasta_rejected(self):
        (self.input / "org" / "query" / "ArcZ_org.fa").write_text(">a\nACGU\n>b\nUGCA\n")
        self.run_local("multiple", success=False)
        self.assertFalse((self.output / "multiple").exists())

    def test_benchmark_failure_propagates(self):
        self.run_local("bad", "--", "--bad-csv", success=False)
        self.assertFalse((self.output / "bad" / "benchmark.csv").exists())
        self.assertEqual(json.loads((self.output / "bad" / "run.json").read_text())["status"], "failed")

    def test_existing_output_is_preserved(self):
        self.run_local("existing", "-n")
        path = self.output / "existing" / "calls.txt"
        before = path.read_bytes()
        self.run_local("existing", "-n", success=False)
        self.assertEqual(path.read_bytes(), before)

    def test_invalid_inputs_and_reserved_options_fail_before_output(self):
        for arguments in (("--", "--out=elsewhere"), ("--", "-n2"), ("--", "--parameterFile=params"),
                          ("-e", "--", "--tAcc=N"), ("-m", "60", "--", "--tIntLenMax=30")):
            self.run_local("invalid", *arguments, success=False)
            self.assertFalse((self.output / "invalid").exists())
        (self.input / "org" / "target" / "org.fa").unlink()
        self.run_local("invalid", success=False)
        self.assertFalse((self.output / "invalid").exists())

    def test_personality_symlink_not_resolved(self):
        link = self.base / "IntaRNAkix"
        link.symlink_to(self.binary)
        self.binary = link
        self.run_local("personality", "-n")
        run = json.loads((self.output / "personality" / "run.json").read_text())
        self.assertEqual(Path(run["binary"]).name, "IntaRNAkix")

    def test_short_intarna_mode_after_separator(self):
        self.run_local("mode", "--", "-m", "M")
        run = json.loads((self.output / "mode" / "run.json").read_text())
        self.assertEqual(run["arguments"][:2], ["-m", "M"])

    def test_full_merge_and_plot_pipeline(self):
        self.run_local("first")
        self.run_local("second")
        # --all ignores ED caches and planned runs.
        (self.output / "ED-values").mkdir()
        self.run_local("planned", "-n")
        merged = self.base / "plots" / "merged.csv"
        self.command(ROOT / "bin" / "mergeBenchmarks.py", "-d", self.output, "-o", merged, "-a")
        self.assertEqual(len(self.read_csv(merged)), 4)
        pdf = self.base / "plots" / "result.pdf"
        self.command(ROOT / "bin" / "plot.py", "-i", merged, "-o", pdf, "-r", "first",
                     "-c", ROOT / "config.txt", "--time", "--memory")
        for suffix in ("", "_runtime", "_memory"):
            self.assertTrue(pdf.with_name("result" + suffix + ".pdf").read_bytes().startswith(b"%PDF"))

    def test_numeric_call_ids_preserved_in_merge(self):
        self.run_local("001")
        self.run_local("002")
        merged = self.base / "numeric.csv"
        self.command(ROOT / "bin" / "mergeBenchmarks.py", "-d", self.output,
                     "-o", merged, "-c", "001", "002")
        rows = self.read_csv(self.base / "numeric_runTimes.csv")
        self.assertEqual({row["callID"] for row in rows}, {"001", "002"})

    def test_merge_rejects_different_coverage(self):
        self.run_local("first")
        self.verified.write_text("ArcZ;b1;one;org\n")
        self.run_local("second")
        merged = self.base / "merged.csv"
        result = self.command(ROOT / "bin" / "mergeBenchmarks.py", "-d", self.output,
                              "-o", merged, "-c", "first", "second", success=False)
        self.assertIn("different verified interactions", result.stderr)
        self.assertFalse(merged.exists())

    def test_matrix_has_eleven_dry_runs(self):
        process = subprocess.run(["bash", str(ROOT / "examples" / "benchmark-kix.sh"), str(self.binary),
                                  "-n", "-i", str(self.input), "-o", str(self.output), "-v", str(self.verified)],
                                 env=self.env, cwd=self.base, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(list(self.output.glob("*/run.json"))), 11)
        self.assertFalse(self.log.exists())


class AnalysisRegressions(unittest.TestCase):
    def test_roc_thresholds_include_zero_and_endpoint(self):
        plot = load("plot")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "benchmark.csv"
            path.write_text("srna_name;target_ltag;target_name;test_intarna_rank_intarna_rank\na;b;c;1\nd;e;f;3\n")
            args = type("Args", (), {"inputFile": path, "separator": ";"})()
            self.assertEqual(plot.determine_ranks(args, {"general": {"end": "3"}})["test_intarna_rank"], [0, 1, 1, 2])

    def test_resource_alignment_and_percentage_denominator(self):
        plot = load("plot")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "merged.csv"
            path.with_name("merged_runTimes.csv").write_text(
                "callID;target_name;Organism;q\nref;t;z;4\nref;t;a;2\nother;t;a;4\nother;t;z;12\n")
            args = type("Args", (), {"inputFile": str(path), "separator": ";", "referenceID": "ref"})()
            values = plot.read_measurements(args, "_runTimes.csv", 1)
            self.assertEqual(values, {"other": [4, 12], "ref": [2, 4]})
            self.assertEqual(plot.relative_changes(values["other"], values["ref"]), [100, 200])
            self.assertEqual(plot.relative_changes([1, 4], [0, 2]), [100])

    def test_empty_prediction_retains_missing_target_sentinel(self):
        benchmark = load("benchmark")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.csv"
            path.write_text("id1;E\n")
            self.assertEqual(benchmark.target_ranks([path]), {})

    def test_targets_count_once_across_shards_and_suboptimal_hits(self):
        benchmark = load("benchmark")
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.csv", Path(tmp) / "b.csv"
            a.write_text("id1;E\nb1;-5\nb1;-4\nb2;-3\n")
            b.write_text("id1;E\nb3;-3.001\nb4;-2\n")
            self.assertEqual(benchmark.target_ranks([a, b]), {"b1": 1, "b2": 2, "b3": 2, "b4": 3})


if __name__ == "__main__":
    unittest.main()
