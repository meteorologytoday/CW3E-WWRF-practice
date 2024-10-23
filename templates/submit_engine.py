#!/usr/bin/env python3
import toml
from pathlib import Path
import pandas as pd
import f90nml
import argparse
import pprint
import numpy as np
import shlex, subprocess, shutil
import sys

def exitIfLocked(lock_file):
    lock_file = Path(lock_file)
    if lock_file.exists():
        print("The lock file %s exists. Abort the submission process." % (str(lock_file),))
        sys.exit(1)



def pleaseRun(cmds, cwd=None, store_output=False):

    if isinstance(cmds, str):
        cmds = [cmds,]

    output = [] if store_output else None

    for cmd in cmds:

        if store_output:
            cmd_output = []

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

                if store_output:
                    cmd_output.append(line)

            p.wait()

        if store_output:
            output.append(cmd_output)

    return output

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='This program modifies namelist.input to allow resubmit for resubmit.')
    parser.add_argument('--setup', type=str, help='Input TOML setup file containing start_time and end_time.', default="submit_detail.toml")
    parser.add_argument('--lock-file', type=str, help='A lock file to prevent multiple submission.', default="submit.lock")
    
    parser.add_argument('--unlock', action="store_true", help='Remove lock file')
    parser.add_argument('--reset-submit-count', action="store_true", help='Reset the submit count to zero')
    parser.add_argument('--fake-submit', action="store_true")
    parser.add_argument('--submit', action="store_true")
    parser.add_argument('--check-output', action="store_true", help='Check if restart file is generated. If so, add 1 to submit count.')
    args = parser.parse_args()

    pprint.pprint(args)
    
    setup = toml.load(args.setup)

    if args.unlock:
        print("The option `--unlock` is flagged. Remove lock file: ", args.lock_file)
        lock_file = Path(args.lock_file)
        
        if lock_file.exists():
            lock_file.unlink()
        
        sys.exit(0)
         
    
    # Check lock file    
    exitIfLocked(args.lock_file)

    if args.reset_submit_count:
        print("The option `--reset-submit-cout` is flagged. Reset submit_count.")

        setup['submit_count'] = 0
        with open(args.setup, "w") as f:
            toml.dump(setup, f)

        sys.exit(0) 


    elif args.submit:
        
        print("The option `--submit` is flagged. Start the submission process.")
     
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
            print("Resubmit max reached, the runs are all done! There is no need to resubmit.")
       
        else: 

            if submit_count == 0:
                print("This is the first submit! Set restart = .false.")
                nml["time_control"]["restart"] = False
            else:
                print("This is a restart run! Set restart = .true.")
                nml["time_control"]["restart"] = True

            new_start_time = start_time + submit_count * resubmit_interval
            new_end_time = new_start_time + resubmit_interval
            if new_end_time > end_time:
                new_end_time = end_time
                
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
            
            # cannot do it here
            #setup["submit_count"] += 1

            
            f90nml.write(nml, setup["output_nml"], sort=True, force=True)
            setup['submit_count_max']   = submit_count_max
            
            #with open(args.setup, "w") as f:
            #    toml.dump(setup, f)
     
            cmd = "sbatch %s" % (setup["submit_file"],)
             
            if args.fake_submit:
                print("Fake submit >> ", cmd)
            else:
                 submit_info = pleaseRun(cmd, store_output=True)
            

            with open(args.lock_file, "w") as f:
                setup['submit_real_time'] = str(pd.Timestamp.now())
                setup['submit_start_time'] = str(new_start_time)
                setup['submit_end_time']   = str(new_end_time)

                if not args.fake_submit:
                    setup['submit_message'] = ",".join(submit_info[0])
                    
                toml.dump(setup, f)

            sys.exit(0)
 
    elif args.check_output:
        
        print("The option `--check-output` is flagged.")
        
        start_time = pd.Timestamp(setup["start_time"])
        end_time = pd.Timestamp(setup["end_time"])
        resubmit_interval = pd.Timedelta(hours=setup["resubmit_interval_hr"])
        submit_count = setup['submit_count']
        
        submit_count_max = (end_time - start_time) / resubmit_interval

        # If it is not an integer, that means the alst restart file
        # will not be produced. We can only check the wrfout file. 
        has_last_wrfrst = submit_count_max % 1 == 0 
        
        submit_count_max = int(np.ceil(submit_count_max))

        if submit_count == submit_count_max:
            print("Resubmit max reached, the runs are all done! There is no need to resubmit.")
            sys.exit(0)
 


        last_submit = submit_count == submit_count_max - 1
       

        new_start_time = start_time + submit_count * resubmit_interval
        new_end_time = new_start_time + resubmit_interval

        if new_end_time > end_time:
            new_end_time = end_time
 

       
        wrfrst_file = Path(".") / "output" / "wrfrst" / "wrfrst_d01_{timestr:s}".format(
            timestr = new_end_time.strftime("%Y-%m-%d_%H:%M:%S")
        )

        wrfout_file = Path(".") / "output" / "wrfout" / "wrfout_d01_{timestr:s}{suffix:s}".format(
            timestr = new_end_time.strftime("%Y-%m-%d_%H:%M:%S"),
            suffix = setup["wrfout_suffix"] if "wrfout_suffix" in setup else "",
        )

        target_files = []
        target_files.append(wrfout_file)

        if last_submit:
            if has_last_wrfrst:
                target_files.append(wrfrst_file)
            else:
                print("It won't have last restart file.")
        else:
            target_files.append(wrfrst_file)

 
        # Check if target_files exist
        files_exist = [ target_file.exists() for target_file in target_files ]
        
        print("Check if target file exists: ")
        for i, target_file in enumerate(target_files):
            print("[%d] %s" % (i, str(target_file), ))
        
        if np.all(files_exist):
            print("Yes. WRF run is successful.")
            with open(args.setup, "w") as f:
                new_submit_count = submit_count + 1
                print("Now increse submit count from %d => %d" % (submit_count, new_submit_count,))
                setup["submit_count"] = new_submit_count
                toml.dump(setup, f)

            sys.exit(0)
        else:
            print("No. Warning: WRF run failed because I cannot find target file ", str(target_file))
            print("Information: submit_count={submit_count:d}. Sim time = {start_time:s} ~ {end_time:s}".format(
                submit_count = submit_count,
                start_time = new_start_time.strftime("%Y-%m-%d_%H:%M:%S"),
                end_time = new_end_time.strftime("%Y-%m-%d_%H:%M:%S"),
            ))

            sys.exit(1)


    else:

        print("Warning: You have not flagged anything. No action is taken.")
