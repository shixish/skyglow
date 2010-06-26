# given a directory
#   make a list of all of the files within
# given a glob
#   make a list of all of the matching files
# given a list of files
#   use the list of files

import re 
from os.path import isfile, isdir, abspath, basename, splitext, join, split
from os import listdir
from glob import glob

def humansort(lst):
  """ Sort the given list in the way that humans expect.
  """
  convert = lambda text: int(text) if text.isdigit() else text
  alphanumkey = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
  lst.sort(key = alphanumkey)

class FileInfo:

    def __init__(self):
        self.fdir = 1
        self.fspec = 1
        self.files = 1
        self.sndx = 1
        self.endx = 1
        self.frcnt = 1
        self.cumfrcnt = 1

class MultiData:

    def __init__(self, fspec):

        self.finfo = FileInfo()
        
        self.M = 0
        self.N = 0
        self.K = 0
        
        self.calib = 1; # stdcal
        
        self.rcrop = (0, 0)
        self.ccrop = (0, 0)
        self.kcrop = (0, 0)
        
        self.lval = ''

        d = []
        f = ''
        ext = ''
        if isinstance(fspec, list):
            d = [abspath(x) for x in fspec]
        elif isdir(fspec):
            d = listdir(fspec)
            humansort(d)
            d = [join(abspath(fspec), x) for x in d]
            d = filter(isfile, d)
        elif isfile(fspec):
            d = [abspath(fspec)]
        else:
            d = glob(fspec)
            humansort(d)
            d = [abspath(x) for x in d]
            d = filter(isfile, d)

        # num files for now, subclass will adj if multi frames per file
        K = len(d)
            
        self.finfo.fdir, dum = split(d[0])
        self.finfo.fspec = splitext(basename(d[0]))
        self.finfo.files = d
        self.finfo.sndx = (0, K)
        self.finfo.endx = (0, K)
        self.finfo.frcnt = 1
        self.finfo.cumfrcnt = (0, K)

        self.K = len(d)

        self.kcrop = (0, self.K)

