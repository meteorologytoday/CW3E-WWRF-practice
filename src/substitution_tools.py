import pandas as pd
import numpy as np
import argparse
import toml
import re
import pprint

def searchSubstitution(s, verbose = True):
        
    matches = re.findall(r"__[a-zA-Z_0-9]+__", s)
   
    if verbose:
        print("Found the following string substitution:")
        for i, match in enumerate(matches):
            print("[%d] %s" % (i+1, match))

    return matches


def stringSubstitution(string_content, mapping, verbose=False):
    
    for keyword, content in mapping.items():
        searched_text = "__%s__" % (keyword,)
        
        p = re.compile(searched_text)
        if re.search(p, string_content):

            if isinstance(content, str):
                substr = content
            elif isinstance(content, int):
                substr = "%d" % (content,)
            elif isinstance(content, float):
                substr = "%f" % (content,)
                
            

            verbose and print("Replacing %s => %s" % (searched_text, substr,))
            string_content = re.sub(p, substr, string_content)
        else:
            print("Warning: Cannot find %s" % (searched_text,))

    return string_content


