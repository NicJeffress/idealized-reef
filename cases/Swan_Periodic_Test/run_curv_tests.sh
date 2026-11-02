#!/bin/bash
# Run the curvilinear periodic SWAN test on this VM (inputs: make_curv_inputs.py).
# Usage: [IMAGE=coawst:swan_periodic] [COAWSTM=/host/path/coawstM]
#        [OLD_IMAGE=image without swan-periodic-curvilinear] run_curv_tests.sh RUN_DIR
# COAWSTM runs that binary inside IMAGE instead of the image's own coawstM.
# OLD_IMAGE (optional) reruns uni-reg-mid, uni-reg-flat and str-norep with the
# older build, to check what swan-periodic-curvilinear changes outside curvilinear REPEATING grids.
# Each run goes to RUN_DIR/<case>-np<N>[-old]. SERIAL / PARALLEL (case lists)
# override which cases run with 1 and with 4 processes.
set -euo pipefail
export IMAGE=${IMAGE:-coawst:swan_periodic}
export COAWSTM=${COAWSTM:-}
cd "$1"

run() {  # run CASE NP [old]
    local d="$1-np$2${3:+-$3}" image="$IMAGE" bin=coawstM mount=()
    if [ "${3:-}" = old ]; then
        image="$OLD_IMAGE"
    elif [ -n "$COAWSTM" ]; then
        mount=(-v "$COAWSTM:/opt/dev/coawstM:ro"); bin=/opt/dev/coawstM
    fi
    rm -rf "$d" && cp -r "$1" "$d"
    docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/$d:/run" -w /run "${mount[@]}" \
        -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
        "$image" mpirun --bind-to none -np "$2" $bin swan.in > "$d/log.txt" 2>&1 \
        && echo "$d: done" || echo "$d: FAILED (see $d/log.txt)"
}

export -f run
SERIAL=${SERIAL:-uni-reg-mid uni-crv-mid uni-reg-flat str-mid str-seam str-flat str-search str-norep str-badper a15-mid a15-seam a15-norep}
PARALLEL=${PARALLEL:-str-mid str-seam str-flat a15-mid a15-seam}
echo $SERIAL | tr ' ' '\n' | xargs -P 4 -I{} bash -c 'run {} 1'     # 4 at a time (4 cores)
if [ -n "${OLD_IMAGE:-}" ]; then
    export OLD_IMAGE
    for c in uni-reg-mid uni-reg-flat str-norep; do
        case " $SERIAL " in *" $c "*) run "$c" 1 old & ;; esac
    done; wait
fi
for c in $PARALLEL; do run "$c" 4; done
