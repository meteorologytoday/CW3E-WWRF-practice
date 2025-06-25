#!/bin/bash


source run00_setup.sh

python3 $src_dir/main_code_GEFS/main_gencase.py  \
    --setup $setup_file \
    --groups PAT01_AMP4.0 PAT01_AMP2.0

