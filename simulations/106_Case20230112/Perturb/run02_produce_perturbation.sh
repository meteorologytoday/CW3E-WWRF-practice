#!/bin/bash

source run00_setup.sh

set -x
python3 $src_dir/produce_perturbation.py \
    --method  fixed               \
    --setup   $setup_file         \
    --bdy-SST-varname  SKINTEMP   \
    --pert-SST-varname sst        \
    --nproc   1
