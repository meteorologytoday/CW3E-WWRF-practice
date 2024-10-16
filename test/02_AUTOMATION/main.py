import pandas as pd
import numpy as np
import argparse
import toml
import re
import pprint
import subprocess, shlex
import os
from pathlib import Path

def pleaseRun(cmds):

    if isinstance(cmds, str):
        cmds = [cmds,]

    for cmd in cmds:
        cmd_split = shlex.split(cmd)
        print(">> ", cmd)

        with subprocess.Popen(
            cmd_split,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            universal_newlines=True,
            encoding='utf-8',
        ) as p:
       
            for line in p.stdout:
                print(line, end='', flush=True)

            p.wait()

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='This high-level program oversees the entire process from downloading data, generating boundary files, adding perturbations to generating cases.')
    parser.add_argument('--setup', type=str, help='Setup TOML file.', required=True)
    parser.add_argument('--workflow', type=str, help='The steps', required=True)
    parser.add_argument('--test-dir', type=str, help='The steps', default="")

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)
    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])
  
    is_test = args.test_dir != ""
 
    if is_test:
        print("Using test_dir: ", args.test_dir)
        Path(args.test_dir).mkdir(exist_ok=True, parents=True)

    ## Part 1
    
    # step 3: generate namelist file for WPS
    wps_output_file = os.path.join(args.test_dir if is_test else case_setup["WPS_DIR"], "namelist.wps")
    pleaseRun("python3 generate_namelist.py --program WRF --setup setup.toml --output {wpsoutput:s}".format(
        wpsoutput = wps_output_file,
    ))
    
    # Run WPS
    pleaseRun(os.path.join(case_setup["WPS_DIR"], "metgrid.exe"))
    

    # Stage 1 : Download Data
      

    ## Part 2
    # Stage 2 :  
    

