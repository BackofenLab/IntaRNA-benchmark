# Local runner smoke validation - checked 8 October 2026

**Status: the full biological benchmark has not run.** No IntaRNA benchmark process was active on the checked host at this follow-up. The only full-input record is a dry-run plan with 30 prediction calls and two ED precomputations. This report archives the small validation runs completed on 7 October during [PR #23](https://github.com/BackofenLab/IntaRNA-benchmark/pull/23), which has since been merged and closed [issue #22](https://github.com/BackofenLab/IntaRNA-benchmark/issues/22). No new predictions were launched for this check.

## Scope and provenance

- 11 configurations, each with four query/organism calls: ArcZ and ChiX for E. coli (`NC_000913`) and Salmonella (`NC_003197`).
- Three selected target sequences per organism: `b0619`, `b1892`, `b2741`; and `STM0687`, `STM1682`, `STM2970`. That is 12 candidate query-target pairs per configuration and 44 process invocations overall. The 127 emitted interactions reflect that some calls return no interaction for a candidate.
- The four query/organism pairs have 11 entries in the repository reference table. Only six of those verified pairs have their target in this fixture; five targets were deliberately omitted by the small input selection. Do not interpret the missing-target sentinel as five failed biological predictions.
- Every matrix manifest is complete and records `--threads=1`. The comparison is the default IntaRNA call, four model-X/noLP/noGU combinations, and six IntaRNAkix score A/B/C/noGU combinations. Here `noGU` means **`--outNoGUend=true`**, not a ban on all GU pairs or a seed-only constraint.
- Binary: IntaRNA 3.4.1, ViennaRNA 2.7.2, Boost 1.85.0. SHA-256: `3779a676dd6a96e6edf9fe9a7316c2125466d0c33be51723661eb1513dfcdd64`. The current local binary still matches every recorded matrix checksum.
- The runs were acquired during PR #23 development, subsequently consolidated as `71f05db5f6fe177f6e7491fa95651c7777349733`. Exact per-run source hashes were not recorded; the binary checksum and explicit arguments are the retained execution identity. Analysis-script and original output-file hashes are recorded in [provenance.json](provenance.json).

## Observed fixture results

All six included verified pairs receive finite ranks when the GU-end constraint is off. With `--outNoGUend=true`, five do; the omitted prediction is ArcZ/STM2970. This holds for the selected baselines and all three kinetic scores. It verifies that the pipeline records and distinguishes these configurations on this fixture; it does not establish their relative accuracy.

| Configuration | Included verified pairs recovered (of 6) | Sum of user CPU seconds (4 calls) | Maximum peak RSS (KiB) |
| --- | ---: | ---: | ---: |
| intarna-X-noLP-false-noGU-false | 6 | 8.11 | 20944 |
| intarna-X-noLP-false-noGU-true | 5 | 7.80 | 20884 |
| intarna-X-noLP-true-noGU-false | 6 | 7.30 | 20960 |
| intarna-X-noLP-true-noGU-true | 5 | 7.25 | 20828 |
| intarna-default | 6 | 8.12 | 20760 |
| intarnakix-A-noGU-false | 6 | 7.09 | 20648 |
| intarnakix-A-noGU-true | 5 | 7.02 | 20752 |
| intarnakix-B-noGU-false | 6 | 7.10 | 20636 |
| intarnakix-B-noGU-true | 5 | 7.05 | 20776 |
| intarnakix-C-noGU-false | 6 | 7.05 | 20744 |
| intarnakix-C-noGU-true | 5 | 7.06 | 20624 |

Runtime is **user CPU time**, not elapsed time; memory is per-process peak RSS. These are single, short, uncontrolled smoke runs with no repeated timing trials or captured hardware baseline. The timing/RSS values and plots are diagnostic outputs, not speedup or memory-efficiency evidence. Dense ranks share equal energies after rounding to two decimals; the historical missing-rank value is `9223372036854775807`.

## Checks performed

- Rechecked all 11 completion manifests, binary identities, 44 expected output files, target/query IDs, finite energies, measurement units and data coverage. The fixture FASTAs match the corresponding tracked input sequences.
- Recomputed every published rank independently using the standard library and decimal energy rounding. Rebuilt the merged rank/CPU/RSS tables with the maintained merge script and regenerated/visually inspected all three plots.
- Rechecked byte-for-byte prediction equality for direct versus cached ED at default settings (four files), and for kinetic score C at 25 C with target interaction length 60, accessibility window 90 and span 60 (four files). Rank tables also match. These checks used the earlier text-ED format; they do not validate the subsequently introduced `.agz` cache path.
- Excluded two failed custom-setting attempts (`smoke-kix-custom` and `smoke-kix-custom-ed`): the requested window was 90 while the default span remained 100. Both failed before producing a benchmark. The corrected span-60 runs are the successful equality checks above.

## Current-master differences and blocker

At this follow-up, master is `6eaff33772596b81f10076195fab5025d8463484`. Since the smoke acquisition, the example has changed to four threads and the `IntaRNAsnap` personality, the documented invocation adds `-m 80`, and ED output uses `.agz`. **The archived results do not validate that newer setup.** The provisional interpretation of `noGU` has not been changed.

A read-only dry-run invocation against current master failed immediately:

```text
./intarna-benchmark-local -b /path/to/IntaRNA -n -c scheduled-dry-run-check
bin/calls.py:138: print("# mkdir : " + str(output), file=log, flush=True)
UnboundLocalError: cannot access local variable 'log' where it is not associated with a value
```

No output directory or prediction was created by this check. The no-directory dry-run change also leaves later manifest/log writes dependent on the absent directory, so fixing only the first reference is insufficient. This results update does not change the runner or the newer benchmark settings. Repair and validate that dry-run path before relying on the documented full-benchmark preview.

## Files and reproduction

- [summary.csv](summary.csv): compact per-configuration counts and resource observations.
- [predictions.csv](predictions.csv): all 127 raw interaction rows, with run/query/organism context added.
- [comparison.csv](comparison.csv), [CPU table](comparison_runTimes.csv), [RSS table](comparison_MaxMemoryUsage.csv): the maintained analysis pipeline outputs.
- [Rank-recovery plot](comparison.pdf), [runtime plot](comparison_runtime.pdf), [memory plot](comparison_memory.pdf): diagnostic smoke plots. Rank-recovery includes the five reference targets omitted from the fixture as missing, so use the six included pairs when interpreting the fixture counts.
- [fixture/](fixture/) and [verified-interactions.csv](verified-interactions.csv): the exact selected sequences and 11 corresponding original reference records.
- [provenance.json](provenance.json): recorded run arguments, source hashes, binary identity, ED checks and excluded failures. [SHA256SUMS](SHA256SUMS) covers every published file in this folder except itself.

From the repository root, verify the archive without IntaRNA or third-party Python packages:

```bash
python3 results/2026-10-08-smoke-validation/verify.py
```

To reproduce the historical prediction setup, use an executable matching the recorded checksum and the arguments in each `provenance.json` run; do not substitute the newer matrix example defaults. The following deliberately starts fresh smoke runs only when executed by the reader:

```bash
export INTARNA_BINARY=/path/to/matching/IntaRNA
python3 - <<'PY_REPRODUCE'
import json, os, subprocess
from pathlib import Path
report = Path('results/2026-10-08-smoke-validation').resolve()
for run in json.loads((report / 'provenance.json').read_text())['runs']:
    subprocess.run(['./intarna-benchmark-local', '-b', os.environ['INTARNA_BINARY'],
                    '-i', str(report / 'fixture'), '-v', str(report / 'verified-interactions.csv'),
                    '-o', 'output/reproduced-smoke', '-c', run['callID'], '--',
                    *run['arguments']], check=True)
PY_REPRODUCE
python3 bin/mergeBenchmarks.py -d output/reproduced-smoke -a -o output/reproduced-smoke-comparison.csv
python3 bin/plot.py -i output/reproduced-smoke-comparison.csv -o output/reproduced-smoke-comparison.pdf \
  -r intarna-default -c config.txt --time --memory --title 'Smoke validation: selected targets only'
```

Use a new output directory for another repetition. Reproduction can validate predictions and ranks; resource measurements will vary. A full run of the bundled data, with an agreed GU interpretation and the intended current binary/settings, remains outstanding.
