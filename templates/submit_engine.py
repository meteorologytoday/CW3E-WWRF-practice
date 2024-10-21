import toml
from pathlib import Path
import pandas as pd
import f90nml
import argparse
import pprint
import numpy as np
import shlex, subprocess, shutil
import sys

def pleaseRun(cmds, cwd=None):

    if isinstance(cmds, str):
        cmds = [cmds,]

    for cmd in cmds:
        cmd_split = shlex.split(cmd)
        print(">> ", cmd)

        #subprocess.run(cmd_split)

        with subprocess.Popen(
            cmd_split,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            universal_newlines=True,
            encoding='utf-8',
            cwd=cwd,
        ) as p:
       
            for line in p.stdout:
                print(line, end='', flush=True)

            p.wait()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='This program modifies namelist.input to allow resubmit for resubmit.')
    parser.add_argument('--setup', type=str, help='Input TOML setup file containing start_time and end_time.', default="submit_detail.toml")
    parser.add_argument('--lock-file', type=str, help='A lock file to prevent multiple submission.', default="submit.lock")
    parser.add_argument('--reset-submit-count', action="store_true", help='Reset the submit count to zero')
    parser.add_argument('--unlock', action="store_true", help='Remove lock file')
    parser.add_argument('--fake-submit', action="store_true")
    parser.add_argument('--submit', action="store_true")
    args = parser.parse_args()

    pprint.pprint(args)
    
    setup = toml.load(args.setup)
 
   
    if args.unlock:
        print("The option `--unlock` is flagged. Remove lock file: ", args.lock_file)
        lock_file = Path(args.lock_file)
        
        if lock_file.exists():
            lock_file.unlink()
        
        sys.exit(0)
         
    if args.reset_submit_count:

        print("The option `--reset-submit-cout` is flagged. Reset submit_count.")

        setup['submit_count'] = 0
        with open(args.setup, "w") as f:
            toml.dump(setup, f)

        sys.exit(0) 


    if args.submit:
        
        print("The option `--submit` is flagged. Start submitting.")

        lock_file = Path(args.lock_file)
        if lock_file.exists():
            print("The lock file %s exists. Abort the submission process." % (str(lock_file),))
            sys.exit(1)
     
        domain_idx = setup['domain'] - 1
        
        nml = f90nml.read(setup['input_nml'])
       
        start_time = pd.Timestamp(setup["start_time"])
        end_time = pd.Timestamp(setup["end_time"])
        resubmit_interval = pd.Timedelta(hours=setup["resubmit_interval_hr"])
        
        if start_time > end_time:
            raise Exception("Error: start_time is after end_time.")
     
        # Count
        submit_count = setup["submit_count"]

        submit_count_max = int(np.ceil((end_time - start_time) / resubmit_interval))
        
        print("Resubmit count max: ", submit_count_max)
        print("Current resubmit count: ", submit_count)

        if submit_count == submit_count_max:
            print("Resubmit max reached! There is no need to resubmit.")
       
        else: 

            print("Looks like we need to submit again!")

            new_start_time = start_time + submit_count * resubmit_interval
            new_end_time = new_start_time + resubmit_interval
            
            nml["time_control"]["start_year"][domain_idx]   = new_start_time.year
            nml["time_control"]["start_month"][domain_idx]  = new_start_time.month
            nml["time_control"]["start_day"][domain_idx]    = new_start_time.day
            nml["time_control"]["start_hour"][domain_idx]   = new_start_time.hour
            nml["time_control"]["start_minute"][domain_idx] = new_start_time.minute
            nml["time_control"]["start_second"][domain_idx] = new_start_time.second
            
            nml["time_control"]["end_year"][domain_idx]   = new_end_time.year
            nml["time_control"]["end_month"][domain_idx]  = new_end_time.month
            nml["time_control"]["end_day"][domain_idx]    = new_end_time.day
            nml["time_control"]["end_hour"][domain_idx]   = new_end_time.hour
            nml["time_control"]["end_minute"][domain_idx] = new_end_time.minute
            nml["time_control"]["end_second"][domain_idx] = new_end_time.second
            
            setup["submit_count"] += 1
            
            f90nml.write(nml, setup["output_nml"], sort=True, force=True)
            
            with open(args.setup, "w") as f:
                toml.dump(setup, f)
     
            with open(args.lock_file, "w") as f:
                setup['submit_real_time'] = str(pd.Timestamp.now())
                setup['submit_start_time'] = str(new_start_time)
                setup['submit_end_time']   = str(new_end_time)
                toml.dump(setup, f)
            
            cmd = "sbatch %s" % (setup["submit_file"],)
             
            if args.fake_submit:
                print("Fake submit >> ", cmd)
            else:
                 pleaseRun(cmd)





