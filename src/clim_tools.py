import xarray as xr
import os
import pandas as pd
import numpy as np
from scipy.interpolate import RegularGridInterpolator

raw_mon_SST_file = "data/sst.mon.mean.nc"
clim_SST_file = "data/clim_sst.mon.nc"

interpolated_clim_SST_file = "data/interpolated_clim_sst.mon.nc"
interpolated_grid_file = "/home/t2hsu/temp_project/WRF_RUNS/test_gcc/met_em.d01.2022-01-07_00:00:00.nc"

"""
    This function assumes the climatology file
"""
def loadClim(dts, grid="interpolated"):

    if grid == "interpolated":
        filename = interpolated_clim_SST_file
    elif grid == "raw":
        filename = clim_SST_file
        

    if not hasattr(dts, '__len__'):
        dts = [dts,]

    simple_times = [ 0.0 for _ in range(len(dts)) ]

    for i, dt in enumerate(dts):
        Jan1 = pd.Timestamp(year=dt.year, month=1, day=1)
        year_interval = pd.Timestamp(year=dt.year+1, month=1, day=1) - Jan1
           
        simple_times[i] = (dt - Jan1) / year_interval 
        
    
    print("Open climatology file: ", filename)
    ds = xr.open_dataset(filename)["sst"]
   
    #print(simple_times) 
    ds = ds.interp(simple_time=simple_times, method='linear')
     
  
    return ds 
     

def interpFromRegularGrid(lat, lon, data, new_lat, new_lon):
    

    Nt = data.shape[0]
    N = new_lat.size
    new_shape = new_lat.shape
 
    new_pts = np.zeros((N, 2), dtype=float)

    new_pts[:, 0] = new_lat.flatten()
    new_pts[:, 1] = new_lon.flatten()
    new_data = np.zeros( (Nt, *new_lat.shape), dtype=float)
   

    repeated_lon = np.concatenate( (lon - 360, lon, lon + 360) )
 
    for t in range(Nt):
        
        interp = RegularGridInterpolator(
            (lat, repeated_lon),
            np.tile(
                data[t, :, :],
                (1, 3),
            ),
        )

        _tmp = interp(new_pts).reshape(new_shape)
        new_data[t, :, :] = _tmp
    

    return new_data

if __name__ == "__main__":
    
    if not os.path.exists(clim_SST_file):
       
        print("Climatology SST file does not exist: ", clim_SST_file)

        print("Compute climatology...")
        ds = xr.open_dataset(raw_mon_SST_file)
        ds = ds.groupby("time.month").mean()

        # Repeat December so that interpolation will not deal with
        # out-of-boundary problem
        new_ds = ds.sel(month=[12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        new_ds = new_ds.rename({"month":"simple_time"})
        new_ds = new_ds.assign_coords(dict(simple_time=(np.arange(13)-0.5)/12))
        
        print("Output file:", clim_SST_file)
        new_ds.to_netcdf(clim_SST_file) 
        
 
    if not os.path.exists(interpolated_clim_SST_file):
       
        print("Interpolated climatology SST file does not exist: ", interpolated_clim_SST_file)
        print("Interpolated Grid File: ", interpolated_grid_file)

        print("Interpolating now... ")
        ds = xr.open_dataset(clim_SST_file)
        ds_gd = xr.open_dataset(interpolated_grid_file)

        lat = ds.coords["lat"].to_numpy()
        lon = ds.coords["lon"].to_numpy()
        data = ds["sst"].to_numpy()

        # Only need one time
        new_lat = ds_gd["XLAT_M"].to_numpy()[0, :, :]
        new_lon = ds_gd["XLONG_M"].to_numpy()[0, :, :]
        
        new_data = interpFromRegularGrid(lat, lon, data, new_lat, new_lon)
       
        new_ds = xr.Dataset(
            data_vars=dict(
                sst = (["simple_time", "south_north", "west_east"], new_data),
            ),
            coords = dict(
                simple_time = (["simple_time"], ds.coords["simple_time"].to_numpy()),
                XLAT_M  = (["south_north", "west_east", ], new_lat),
                XLONG_M = (["south_north", "west_east", ], new_lon),
            )
        ) 
        
 
        print("Output file:", interpolated_clim_SST_file)
        new_ds.to_netcdf(interpolated_clim_SST_file) 
        
        

    test_times = ["2024-%d-05" % (i,) for i in range(1, 13)]
    test_times = [ pd.Timestamp(t) for t in test_times ]
    ds = loadClim(test_times)

    ds.to_netcdf("test.nc")

    print(ds)

