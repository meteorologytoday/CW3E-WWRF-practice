import pandas as pd
import numpy as np
import argparse
import toml
import re
import pprint
import time

def searchSubstitution(s, verbose = True):
        
    matches = re.findall(r"__[a-zA-Z_0-9]+__", s)
   
    if verbose:
        print("Found the following namelist substitution:")
        for i, match in enumerate(matches):
            print("[%d] %s" % (i+1, match))

    return matches


def namelistSubstitution(namelist_content, mapping):
    
    for keyword, content in mapping.items():
        searched_text = "__%s__" % (keyword,)
        
        p = re.compile(searched_text)
        if re.search(p, namelist_content):

            if isinstance(content, str):
                substr = content
            elif isinstance(content, int):
                substr = "%d" % (content,)
            elif isinstance(content, float):
                substr = "%f" % (content,)
                
            

            print("Replacing %s => %s" % (searched_text, substr,))
            namelist_content = re.sub(p, substr, namelist_content)
        else:
            print("Warning: Cannot find %s" % (searched_text,))

    return namelist_content


