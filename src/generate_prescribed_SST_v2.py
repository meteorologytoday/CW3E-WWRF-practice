import xarray as xr
import pandas as pd
import numpy as np
import argparse
import tool_fig_config
import wrf_load_helper 
import datetime
import os
from pathlib import Path

def addSSTPerturbation(
    init_SST_file,
    pert_SST_file,
    input_dir,
    output_dir,
    beg_dt,
    end_dt,
    data_interval,
    frames_per_file = 1,
    input_prefix = "met_em.d01.",
    input_suffix = ".nc",
    output_prefix = "met_em.d01.",
    output_suffix = ".nc",
):

    file_cnt = ( end_dt - beg_dt ) / data_interval

    if file_cnt % 1 != 0:
        raise Exception("The time selected is not a multiple of `data_interval`.")

    file_cnt = int(file_cnt)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("Load init SST file: ", init_SST_file)
    ds_init_SST = xr.open_dataset(init_SST_file)

    print("Load perturbation file: ", pert_SST_file)
    ds_pert_SST = xr.open_dataset(pert_SST_file)


    for i in range(file_cnt):
        
        _dt = beg_dt + i * data_interval
        timestr = _dt.strftime("%Y-%m-%d_%H:%M:%S")
        
        input_filename = "{input_prefix:s}{timestr:s}{input_suffix:s}".format(
            timestr = timestr,
            input_prefix = input_prefix,
            input_suffix = input_suffix,
        )
        
        output_filename = "{output_prefix:s}{timestr:s}{output_suffix:s}".format(
            timestr = timestr,
            output_prefix = output_prefix,
            output_suffix = output_suffix,
        )
        
        input_full_filename  = os.path.join(input_dir, input_filename)
        output_full_filename = os.path.join(output_dir, output_filename)
       
        print("Processing file: ", input_full_filename)
        ds = xr.open_dataset(input_full_filename)

        # Important: Use ds_init_SST
        new_SST = ds_init_SST["SST"].to_numpy()
        mask = new_SST == 0

        new_SST += ds_pert_SST["pert_SST"].to_numpy()
        
        new_SST[mask] = 0.0

        ds["SST"][:, :, :] = new_SST

        print("Output to file: ", output_full_filename)     
        ds.to_netcdf(
            output_full_filename,
            unlimited_dims = "Time",
        )
    
if __name__ == "__main__":
 
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--input-dir', type=str, help='Input directory.', required=True)
    parser.add_argument('--output-dir', type=str, help='Output directory.', required=True)
    parser.add_argument('--init-SST-file', type=str, help="Init SST file.", required=True)
    parser.add_argument('--pert-SST-file', type=str, help='Perturbation SST file.', required=True)
    parser.add_argument('--output-init-time', type=str, help='Init time of the output file.', required=True)
    parser.add_argument('--output-hours', type=int, help="How many hours.", required=True)
    parser.add_argument('--output-interval', type=int, help="Interval of out put in hours.", required=True)
    
    parser.add_argument('--pert-method', type=str, help='Perturbation method.', required=True, choices=["persistent_SST_anomaly", ])

    args = parser.parse_args()

    print(args)

     
    beg_dt          = pd.Timestamp(args.output_init_time)
    output_timelen  = pd.Timedelta(hours=args.output_hours)
    output_interval = pd.Timedelta(hours=args.output_interval)
    
    N = output_timelen / output_interval

    if N % 1 != 0:
        print("Warning: The time `--output-hours` is not a multiple of `--output-interval`.")

    N = int(np.floor(N))
    print("Will generate %d files." % (N,))
  
    end_dt = beg_dt + N * output_interval

    addSSTPerturbation(
        args.init_SST_file,
        args.pert_SST_file,
        args.input_dir,
        args.output_dir,
        beg_dt = beg_dt,
        end_dt = end_dt,
        data_interval = output_interval,
    )


