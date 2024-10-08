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
    pert_file,
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
    
    print("Load perturbation file: ", pert_file)
    ds_SST_pert = xr.open_dataset(pert_file)

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

        new_SST = ds["SST"].to_numpy()
        mask = new_SST == 0

        new_SST += ds_SST_pert["pert_SST"].to_numpy()
        
        new_SST[mask] = 0.0

        ds["SST"][:, :, :] = new_SST

        print("Output to file: ", output_full_filename)     
        ds.to_netcdf(
            output_full_filename,
            unlimited_dims = "Time",
        )
    
if __name__ == "__main__":
    
    pert_file = "/home/t2hsu/projects/CW3E-WWRF-practice/test/perturbation/pert_SST.d01.2022-01-07_00:00:00.nc"
    input_dir = "/home/t2hsu/temp_project/WRF_RUNS/test_gcc"
    output_dir = "/home/t2hsu/temp_project/WRF_RUNS/altered_SST"
    beg_dt = pd.Timestamp("2022-01-07T06:00:00")
    end_dt = pd.Timestamp("2022-01-08T00:00:00")
    data_interval = pd.Timedelta(hours=3)
    
    addSSTPerturbation(
        pert_file,
        input_dir,
        output_dir,
        beg_dt = beg_dt,
        end_dt = end_dt,
        data_interval = data_interval,
    )

    print(ds.time)

