import xarray as xr
import pandas as pd
import numpy as np
import argparse
import tool_fig_config
import wrf_load_helper 
import datetime
import os
from pathlib import Path
import clim_tools
import scipy

def loadXarrayIfStr(fn, varname=None):
    
    if isinstance(fn, str):
        print("Load file: ", fn)
        ds = xr.open_dataset(fn)
    elif isinstance(fn, xr.Dataset):
        ds = fn
    elif isinstance(fn, xr.DataArray):
        ds = fn
    else:
        raise Exception("Unknown type of input: ", str(type(fn)))

    # Return DataArray
    if varname is not None:
        if not isinstance(fn, xr.DataArray):
            ds = ds[varname]
       
    return ds


def addSSTPerturbation(
    init_SST,
    pert_SST,
    input_dir,
    output_dir,
    beg_dt,
    end_dt,
    data_interval,
    cmb,  # clim_tools.climMagicBox
    frames_per_file = 1,
    input_prefix = "met_em.d01.",
    input_suffix = ".nc",
    output_prefix = "met_em.d01.",
    output_suffix = ".nc",
):

    file_cnt = ( end_dt - beg_dt ) / data_interval + 1

    if file_cnt % 1 != 0:
        raise Exception("The time selected is not a multiple of `data_interval`.")

    file_cnt = int(file_cnt)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    ds_init_SST = loadXarrayIfStr(init_SST)
    da_pert_SST = loadXarrayIfStr(pert_SST, varname="pert_SST")

    new_SST_base = ds_init_SST["SST"].to_numpy()


    lat = ds_init_SST["XLAT_M"].to_numpy()[0, :, 0]
    lon = ds_init_SST["XLONG_M"].to_numpy()[0, 0, :]
    
    init_SST_clim = cmb.loadClim(beg_dt).to_numpy()

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
        
        current_SST_clim = cmb.loadClim(_dt).to_numpy()
        clim_SST_diff = current_SST_clim - init_SST_clim
        nan_idx_in_clim = np.isnan(clim_SST_diff)


        # Important: Use ds_init_SST
        new_SST = new_SST_base.copy()
        lnd_mask = new_SST == 0
        ocn_mask = np.logical_not(lnd_mask)
       

        #print("sum of lnd_mask: ", np.sum(lnd_mask))
 
        nan_idx_in_both_clim_ocn = np.logical_and(nan_idx_in_clim, ocn_mask)
        if np.sum(nan_idx_in_both_clim_ocn) == 0:
            print("All points can be found in climatology files! ")
        else:
            print("There are %d points cannot find its climatology values. The trend at these points will be assigned as 0." % (np.sum(nan_idx_in_both_clim_ocn),))
        
        clim_SST_diff[nan_idx_in_clim] = 0
    
        new_SST += da_pert_SST.to_numpy() + clim_SST_diff
       
        # Clear land values 
        new_SST[lnd_mask] = 0.0

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


