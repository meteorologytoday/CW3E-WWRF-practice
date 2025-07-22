#!/bin/bash


source run00_setup.sh

python3 $src_dir/main_code_GEFS/main_gencase.py  \
    --setup $setup_file \
    --groups PAT00_AMP-1.0 PAT00_AMP1.0

