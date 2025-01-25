import requests
import pandas as pd
import numpy as np
import argparse
import os
import re
import pprint 
import pprint as pp
from pathlib import Path

def work(details):

    pass

        




if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--date-rng', type=str, nargs=2, help='Input directories.', required=True)
    parser.add_argument('--fcst-hrs', type=int, nargs="+", help='fcst.', required=True)
    parser.add_argument('--init-hrs', type=int, nargs="+", help='Init hr.', required=True)
    parser.add_argument('--groups', type=str, nargs="+", help='Group name, use colon to separate primary and secondary goup.', required=True)
    parser.add_argument('--perturbation-members', type=int, help='Number of perturbation members.', required=True)
    parser.add_argument('--output-root', type=str, help='Output filename in png.', required=True)
    args = parser.parse_args()
    pp.pprint(args)
   

    for dt in pd.date_range(args.date_rng[0], args.date_rng[1], freq="D"):
        dt_str = dt.strftime("%Y%m%d")

        for init_hr in args.init_hrs:
            init_hr_str = "%02d" % (init_hr,)

            for fcst_hr in args.fcst_hrs:

                for group in args.groups:


                    """
                    details = dict(
                        group = group,
                        dt    = dt,
                        init_hr = init_hr,
                        fcst_hr = fcst_hr,
                        group = 
                    )
                    """


                    gp_subdivide = group.split(":")
                    
                    pri_gp = gp_subdivide[0]
                    sec_gp = gp_subdivide[1]
                    altsec_gp = re.sub( r'0*$', '', re.sub(r'^0*', '', sec_gp))    

                    gp="%s%s" % (pri_gp, altsec_gp)
                    
                    
                    for number in range(args.perturbation_members):

                        member_label = "c%02d" % (number,) if number == 0 else "p%02d" % (number,)

                        output_dir = Path(args.output_root) / f"gefs.{dt_str:s}/{init_hr_str:s}/{member_label:s}/atmos"
                        output_dir.mkdir(parents=True, exist_ok=True)

                        full_file = f"ge{member_label:s}.t{init_hr_str:s}z.{pri_gp:s}.{sec_gp}.f{fcst_hr:03d}"
                        full_link = f"https://noaa-gefs-pds.s3.amazonaws.com/gefs.{dt_str:s}/{init_hr_str:s}/atmos/{gp:s}/{full_file:s}"
                        
                        output_file = output_dir / full_file

                        if os.path.exists(output_file):
                            print("File %s already exists. Skip." % (output_file,))
                            continue

                        print("Downloading file: %s => %s" % (full_link, output_file,))
                        try:
                            # get request
                            response = requests.get(full_link)
                            if response.status_code != 200:
                                raise requests.ConnectionError(f'{response.status_code}')

                            with open(output_file, "wb") as output_file:
                                output_file.write(response.content)
                                
                        except Exception as e:
                            
                            print("Something goes wrong with date: %s" % (dt_str,))
                            print(str(e))
                    
                
