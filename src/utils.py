import os
import yaml
import numpy as np

def load_sim(filename):
    s = yaml.safe_load(open(filename))
    if 'tags' not in s:
        return s
    tag_substr( s, s['tags'])
    return s
    
def tag_substr(dest, tags, max_recursion=20):
    """ 'borrowed' from sotodlib because it's so useful. Do string substitution of all 
    our tags into dest (in-place if dest is a dict). Used to replace tags within yaml files.
    """
    assert(max_recursion > 0)  # Too deep this dictionary.
    if isinstance(dest, str):
        # Keep subbing until it doesn't change any more...
        new = dest.format(**tags)
        while dest != new:
            dest = new
            new = dest.format(**tags)
        return dest
    if isinstance(dest, list):
        return [tag_substr(x,tags) for x in dest]
    if isinstance(dest, tuple):
        return (tag_substr(x,tags) for x in dest)
    if isinstance(dest, dict):
        for k, v in dest.items():
            dest[k] = tag_substr(v,tags, max_recursion-1)
        return dest
    return dest

def load_band_file(fname):
    base = os.environ.get( "JBOLO_MODELS_PATH", "" )
    fpath = os.path.join( base, fname )
    return np.loadtxt( fpath, unpack=True)