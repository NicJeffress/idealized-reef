#!/bin/bash
# Run the SWAN periodic test on this VM.
# Usage: [IMAGE=coawst:swan_periodic] run_tests.sh RUN_DIR   (RUN_DIR made by make_inputs.py)
# Each case runs with 1 and 4 SWAN processes, in RUN_DIR/<case>-np1, -np4.
set -euo pipefail
export IMAGE=${IMAGE:-coawst:swan_periodic}
cd "$1"
CASES="tall-rep-mid tall-rep-seam tall-norep-mid wide-rep-mid wide-rep-seam wide-norep-mid"

run() {  # run CASE NP
    local d="$1-np$2"
    rm -rf "$d" && cp -r "$1" "$d"
    docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/$d:/run" -w /run \
        "$IMAGE" mpirun --bind-to none -np "$2" coawstM swan.in > "$d/log.txt" 2>&1 \
        && echo "$d: done" || echo "$d: FAILED (see $d/log.txt)"
}

export -f run
for c in $CASES; do run "$c" 1 & done; wait                       # 6 serial runs at once
echo $CASES | tr ' ' '\n' | xargs -P 2 -I{} bash -c 'run {} 4'    # then two 4-process runs at a time
