import xarray as xr
import os
import pandas as pd
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from pathlib import Path

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

class climMagicBox:

    def __init__(
        self,
        raw_mon_SST_file,
        clim_SST_file,
        interpolated_clim_SST_file,
        interpolated_grid_file,
    ):
    
        self.raw_mon_SST_file = raw_mon_SST_file
        self.clim_SST_file = clim_SST_file
        self.interpolated_clim_SST_file = interpolated_clim_SST_file
        self.interpolated_grid_file = interpolated_grid_file

    def genClim(self):

        if not os.path.exists(self.clim_SST_file):
           
            print("Climatology SST file does not exist: ", self.clim_SST_file)

            output_dir = os.path.dirname(self.clim_SST_file)
            print("Making dir for clim SST: ", output_dir)
            Path(output_dir).mkdir(exist_ok=True, parents=True)

            print("Compute climatology...")
            ds = xr.open_dataset(self.raw_mon_SST_file)
            ds = ds.groupby("time.month").mean()

            # Repeat December and Jan so that interpolation will not deal with
            # out-of-boundary problem
            #                      -.5 .5 1.5 ...                    10.5 11.5 12.5
            new_ds = ds.sel(month=[12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1])
            new_ds = new_ds.rename({"month":"simple_time"})
            new_ds = new_ds.assign_coords(dict(simple_time=(np.arange(14)-0.5)/12))
            
            print("Output file:", self.clim_SST_file)
            new_ds.to_netcdf(self.clim_SST_file) 
     

    def loadClim(self, dts, grid="interpolated"):
        """
            This function assumes the climatology file
        """

        if grid == "interpolated":
            filename = self.interpolated_clim_SST_file
        elif grid == "raw":
            filename = self.clim_SST_file
            
        if not hasattr(dts, '__len__'):
            dts = [dts,]

        simple_times = [ 0.0 for _ in range(len(dts)) ]

        ds = xr.open_dataset(filename)["sst"]
        for i, dt in enumerate(dts):
            Jan1 = pd.Timestamp(year=dt.year, month=1, day=1)
            year_interval = pd.Timestamp(year=dt.year+1, month=1, day=1) - Jan1
               
            simple_times[i] = (dt - Jan1) / year_interval

        
        print("Open climatology file: ", filename)

       
        #print(simple_times) 
        ds = ds.interp(simple_time=simple_times, method='linear')
         
      
        return ds 
        
    def genInterpolatedClim(self):

        if not os.path.exists(self.interpolated_clim_SST_file):
        
            print("Interpolated climatology SST file does not exist: ", self.interpolated_clim_SST_file)
            print("Interpolated Grid File: ", self.interpolated_grid_file)

            print("Interpolating now... ")
            ds = xr.open_dataset(self.clim_SST_file)
            ds_gd = xr.open_dataset(self.interpolated_grid_file)

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
            
     
            print("Output file:", self.interpolated_clim_SST_file)
            new_ds.to_netcdf(self.interpolated_clim_SST_file) 
     

if __name__ == "__main__":
   
    data_dir = "/home/t2hsu/projects/CW3E-WWRF-practice/data"
    interpolated_data_dir = "./interpolated_data"

    print("Creating dir: ", interpolated_data_dir)
    Path(interpolated_data_dir).mkdir(exist_ok=True, parents=True)

    cmb = climMagicBox(
        raw_mon_SST_file           = os.path.join(data_dir, "sst.mon.mean.nc"),
        clim_SST_file              = os.path.join(data_dir, "clim_sst.mon.nc"),
        interpolated_clim_SST_file = os.path.join(interpolated_data_dir, "interpolated_clim_sst.mon.nc"),
        interpolated_grid_file     = os.path.join(interpolated_data_dir, "met_em.d01.2022-01-07_00:00:00.nc"),
    )

    print("Generating clim files")
    cmb.genClim()
    cmb.genInterpolatedClim()
 
    print("Try loading clim on interpolated grid")
    test_times = ["2024-%d-05" % (i,) for i in range(1, 13)]
    test_times = [ pd.Timestamp(t) for t in test_times ]
    ds = cmb.loadClim(test_times)

    ds.to_netcdf("test.nc")

    print(ds)

