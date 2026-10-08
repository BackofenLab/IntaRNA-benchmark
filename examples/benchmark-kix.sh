#!/usr/bin/env bash
# Prepare/run the 11 comparisons in BackofenLab/IntaRNA#255 on one computer.

# number of threads to use for IntaRNA calls (default: 4)
RUNTHREADS=4

set -euo pipefail
if (( $# < 1 )); then
    echo "Usage: $0 /path/to/IntaRNA [local runner options, e.g. -n -i INPUT -o OUTPUT]" >&2
    echo "Use GU_OPTION=seedNoGU or GU_OPTION=both to change the GU constraint." >&2
    exit 2
fi
binary=$1
shift
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
gu_option=${GU_OPTION:-outNoGUend}
case "$gu_option" in
    outNoGUend|seedNoGU) gu_options=("--$gu_option=true") ;;
    both) gu_options=(--outNoGUend=true --seedNoGU=true) ;;
    *) echo "GU_OPTION must be outNoGUend, seedNoGU, or both" >&2; exit 2 ;;
esac
run() {
    local id=$1
    shift
    # running the benchmark with the local runner and precomputed ED
    "$root/intarna-benchmark-local" -m 80 -e -b "$binary" "${runner_options[@]}" -c "$id" -- "--threads=$RUNTHREADS" "$@"
}
runner_options=("$@")
run intarna-default
for lp in false true; do
    for gu in false true; do
        options=(--model=X "--outNoLP=$lp")
        if [[ $gu == true ]]; then options+=("${gu_options[@]}"); fi
        run "intarna-X-noLP-$lp-noGU-$gu" "${options[@]}"
    done
done
for score in A B C; do
    for gu in false true; do
        options=(--personality=IntaRNAsnap "--kineticScore=$score")
        if [[ $gu == true ]]; then options+=("${gu_options[@]}"); fi
        run "intarnakix-$score-noGU-$gu" "${options[@]}"
    done
done
