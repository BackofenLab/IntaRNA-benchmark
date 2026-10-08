#!/usr/bin/env python3
"""Verify this archived smoke result using only the Python standard library."""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
MISSING = 9223372036854775807


def rows(filename):
    with (BASE / filename).open(newline='') as handle:
        return list(csv.DictReader(handle, delimiter=';'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    for line in (BASE / 'SHA256SUMS').read_text().splitlines():
        expected, filename = line.split('  ', 1)
        require(hashlib.sha256((BASE / filename).read_bytes()).hexdigest() == expected,
                'Checksum mismatch: ' + filename)
    provenance = json.loads((BASE / 'provenance.json').read_text())
    predictions = rows('predictions.csv')
    comparison = rows('comparison.csv')
    summary = {row['callID']: row for row in rows('summary.csv')}
    cpu = rows('comparison_runTimes.csv')
    memory = rows('comparison_MaxMemoryUsage.csv')
    with (BASE / 'verified-interactions.csv').open(newline='') as handle:
        verified = list(csv.reader(handle, delimiter=';'))
    require(len(provenance['runs']) == 11, 'Expected 11 configurations')
    require(len(predictions) == 127, 'Expected 127 emitted interactions')
    require(len(verified) == len(comparison) == 11, 'Expected 11 reference rows')
    known_ids = {run['callID'] for run in provenance['runs']}
    for table in (predictions, cpu, memory):
        require({row['callID'] for row in table} == known_ids, 'Run IDs differ')
    require(set(summary) == known_ids, 'Summary run IDs differ')
    lookup = {(row['srna_name'], row['target_ltag'], row['target_name']): row for row in comparison}
    require(len(lookup) == 11, 'Duplicate interaction keys')
    for run in provenance['runs']:
        call_id = run['callID']
        require(run['status'] == 'complete' and len(run['jobs']) == 4, 'Incomplete run')
        recovered = present = seen = 0
        jobs = {(job['srna'], job['organism']): job for job in run['jobs']}
        require(len(jobs) == 4, 'Duplicate query/organism job')
        for (srna, organism), job in jobs.items():
            target_ids = {line[1:].split()[0] for line in (BASE / job['target']).read_text().splitlines()
                          if line.startswith('>')}
            require(target_ids == set(job['target_ids']) and len(target_ids) == 3, 'Wrong target fixture')
            query_id = (BASE / job['query']).read_text().splitlines()[0][1:]
            output = [row for row in predictions if (row['callID'], row['srna_name'], row['Organism']) ==
                      (call_id, srna, organism)]
            require(len(output) == job['prediction_rows'], 'Prediction row count differs')
            require(len({r['id1'] for r in output}) == len(output), 'Duplicate target predictions')
            require(all(row['id1'] in target_ids and row['id2'] == query_id for row in output), 'Wrong sequence IDs')
            require(all(Decimal(row['E']).is_finite() for row in output), 'Nonfinite energy')
            energies = {row['id1']: Decimal(row['E']).quantize(Decimal('0.01')) for row in output}
            # Independently reproduce dense energy ranks, without pandas or benchmark.py.
            ordered = sorted(set(energies.values()))
            ranks = {target: ordered.index(energy) + 1 for target, energy in energies.items()}
            for ref in verified:
                if (ref[0], ref[3]) != (srna, organism):
                    continue
                seen += 1
                present += ref[1] in target_ids
                rank = ranks.get(ref[1], MISSING)
                actual = int(lookup[tuple(ref[:3])][call_id + '_intarna_rank'])
                require(actual == rank, 'Rank mismatch: ' + call_id + ' / ' + ref[1])
                recovered += rank != MISSING
        record = summary[call_id]
        require(seen == 11 and present == 6, 'Incorrect reference coverage')
        require(int(record['verified_pairs_recovered']) == recovered, 'Incorrect recovery count')
        require(int(record['verified_pairs_in_fixture']) == present, 'Incorrect present-pair count')
        require(int(record['verified_rows']) == seen, 'Incorrect reference-row count')
        require(int(record['prediction_calls']) == 4 and int(record['candidate_pairs']) == 12, 'Incorrect workload')
        require(recovered == (5 if '--outNoGUend=true' in run['arguments'] else 6), 'Unexpected fixture recovery')
        times = [row for row in cpu if row['callID'] == call_id]
        rss = [row for row in memory if row['callID'] == call_id]
        require(len(times) == len(rss) == 2, 'Incorrect resource-table coverage')
        expected_organisms = {'NC_000913', 'NC_003197'}
        require({r['Organism'] for r in times} == {r['Organism'] for r in rss} == expected_organisms,
                'Incorrect resource-table organisms')
        measured_cpu = [Decimal(row[q]) for row in times for q in ('ArcZ', 'ChiX')]
        measured_rss = [int(row[q]) for row in rss for q in ('ArcZ', 'ChiX')]
        require(all(value.is_finite() and value >= 0 for value in measured_cpu), 'Invalid CPU measurement')
        require(all(value > 0 for value in measured_rss), 'Invalid memory measurement')
        require(sum(measured_cpu) == Decimal(record['user_cpu_seconds_sum']), 'CPU sum mismatch')
        require(max(measured_rss) == int(record['peak_rss_kib_max']), 'RSS maximum mismatch')
    print('PASS: archive checksums, 11 runs, 44 calls, 127 predictions, dense ranks, coverage and resource summaries')
    print('Scope: smoke validation only. No full-dataset benchmark results are present.')


if __name__ == '__main__':
    main()
