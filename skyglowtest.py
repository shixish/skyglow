from __future__ import print_function


#import skyglow as sg
# ^- why is this necessary?
import uavdata as ud
import affines as af
import time

#pfits is for fits files, unused atm
#import pfits
import numpy as np
#import scipy.stsci.convolve as ic
#import scipy.stats as st
import scipy;
from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps, ImageEnhance

import os.path as op
import os, fnmatch
import sys
import io
import cPickle
import tempfile
import shutil
#isfile, isdir, abspath, basename, splitext, join, split
import operator
import glob
import datetime
import subprocess

'''
# note: these global consts are not used anymore.
#       they are left here for reference

# regular format
#IMGNROWS=240
#IMGNCOLS=320
#TOTDEGRS=140
#SMFONTSZ=24
#BGFONTSZ=64

# large format
#IMGNROWS=512
#IMGNCOLS=640
#TOTDEGRS=170
#SMFONTSZ=64
#BGFONTSZ=128

# this function takes a list of .img filenames or a directory containing .img files
# catalogs their contents (1 entry per image)
# for each image:
#     calc/store stats
# save the catalog to a file for use later
# return the catalog for use now
# cldcat20100309 = sg.cldcatalog('/media/lava-h/meade-img/', '', True)
def cldcatalog(datalocn, resultsdir='', writecat=False):
    topdatdir = ''
    filenames = []
    # datalocn can either be
    #   a list of .img filenames OR
    #   a directory that containes .img files
    if isinstance(datalocn, list) and \
       len(datalocn) > 0 and \
       all(isinstance(filename, basestring) for filename in datalocn) and \
       all(op.isfile(filename) and filename.endswith('.img') for filename in datalocn):
        # datalocn is a non-empty list of .img filenames
        topdatdir = commondir(datalocn)
        filenames = datalocn
    elif isinstance(datalocn, basestring) and op.isdir(datalocn):
        # datalocn is a string and is a path to and actual directory
        topdatdir = op.abspath(datalocn)
        filenames = glob.glob(topdatdir + '/*.img')
        if len(filenames) == 0:
            raise RuntimeError('skyglow.cldcatalog: no data files found in given data location')
    else:
        raise RuntimeError('skyglow.cldcatalog: bad data location information: not dir or list of img files')

    filenames.sort()

    # ex. topdatdir   /media/lava-h/meade-img
    #     resultsdir  /media/lava-h/meade-img/meta <- catalog.pk file oes here
    #     cachesdir   /media/lava-h/meade-img/meta/caches <- nostarcache

    if resultsdir == '':
        resultsdir = op.join(topdatdir, 'meta')
    if not op.isdir(resultsdir):
        os.makedirs(resultsdir)
    
    cachesdir = op.join(resultsdir, 'caches')
    if not op.isdir(cachesdir):
        os.makedirs(cachesdir)

    print('topdatdir   = ', topdatdir)
    print('resultsdir  = ', resultsdir)
    print('cachesdir   = ', cachesdir)

    cat = []
    for i, filename in enumerate(filenames):
        print('  {0:3d}/{1:3d}   {2}'.format(i, len(filenames), filename)) # just to see progress during exec of azelix (slow)
        sys.stdout.flush()
        try:
            sf = ud.UAVData(filename)
        except RuntimeError:
            print('RuntimeError UAVData ctor, just skip it as a bad file for now: ', filename)
            continue
        except MemoryError:
            print('MemoryError UAVData ctor, just skip it as a bad file for now: ', filename)
            continue
        mds = [sf.framemeta(i) for i in range(len(sf))] # list of metadatas
        for j, md in enumerate(mds):
            d = dict()
            d['time'] = time.localtime(md['LTime'])
            d['filename'] = filename
            d['index'] = j
            cat.append(d)
            
    return cat


'''















#
#Unused
#
def catalogmeadefits(datalocn):
    if isinstance(datalocn, list) and \
       len(datalocn) > 0 and \
       all(isinstance(filename, basestring) for filename in datalocn) and \
       all(op.isfile(filename) and filename.endswith('.fit') for filename in datalocn):
        # datalocn is a non-empty list of .fit filenames
        topdatdir = commondir(datalocn)
        filenames = datalocn
    elif isinstance(datalocn, basestring) and op.isdir(datalocn):
        # datalocn is a string and is a path to and actual directory
        topdatdir = op.abspath(datalocn)
        filenames = glob.glob(topdatdir + '/*.fit')
        if len(filenames) == 0:
            raise RuntimeError('skyglow.catalogmeadfits: no data files found in given data location')
    else:
        raise RuntimeError('skyglow.catalogmeadfits: bad data location information: not dir or list of fit files')
    filenames.sort()
    cat = []
    for f in filenames:
        ffl = pfits.FITS(f)
        hdu = ffl.get_hdus()[0]
#        hdus = ffl.get_hdus()
#        hdu = hdus[0]
        fe = dict()
        fe['filename'] = f
        for k in hdu.keys():
            fe[k] = hdu[k]
        s = fe['DATE']
        fe['date'] = datetime.datetime(int(s[0:4]), int(s[5:7]), int(s[8:10]),
                                       int(s[11:13]), int(s[14:16]), int(s[17:19]))
        cat.append(fe)
    cat.sort(key=lambda x: x['DATE'])
    return cat

def getmeadeimg(mcat, dt):
    ci = 0
    mni = 0
    mxi = len(mcat) - 1
    def totsecs(t):
        return t.days * 86400 + t.seconds + t.microseconds / 1000000
    def close(t1, t2):
        d = abs(totsecs(t2 - t1))
        return d < 10
    while 1:
        ci = mni + (mxi - mni + 1) / 2
        cd = mcat[ci]['date']
        if close(dt, cd):
            print('close')
            break
        if (mni >= mxi):
            print('index collide')
            break
        if dt < cd:
            mxi = ci
        else:
            mni = ci
    print('min, max, cur = ', mni, mxi, ci)
    print('min, max, cur = ', mcat[mni]['DATE'], mcat[mxi]['DATE'], mcat[ci]['DATE'])
    ffl = pfits.FITS(mcat[ci]['filename'])
    hdu = ffl.get_hdus()[0]
    return (mcat[ci]['date'], hdu.get_data())
    

def copyforvideo(srcdir, dstdir, az, el):
    print('srcdir = ', srcdir)
    print('dstdir = ', dstdir)
    if not op.isdir(srcdir):
        raise RuntimeError('skyglow.copyforvideo: source directory does not exist')
    azelglob = '*-{0:0>4d}-{1:0>4d}.png'.format(int(az * 10), int(el * 10))
    filenames = glob.glob(op.join(srcdir, azelglob))
    print('filename = ', filenames)
    if len(filenames) == 0:
        raise RuntimeError('skyglow.copyforvideo: source directory does not contain images asked for')
    if not op.isdir(dstdir):
        os.makedirs(dstdir)
    filepaths = [op.abspath(x) for x in filenames]
    filepaths.sort()
    print('filepaths = ', filepaths)
    for i, filepath in enumerate(filepaths):
        filename = op.basename(filepath)
        srcfilename, extn = op.splitext(filename)
        sfnparts = srcfilename.split('-')
        dstfilename = sfnparts[0] + '-' + sfnparts[4] + '- ' + sfnparts[5] + '-{0:0>6d}'.format(i) + extn
        dstpathname = op.join(dstdir, dstfilename)
        print('i, dstpathname = ', i, ', ', dstpathname)
        shutil.copy(filepath, dstpathname)

def copyforvideoall(srcdir, dstdir=''):
    if not op.isdir(srcdir):
        raise RuntimeError('skyglow.copyforvideo: source directory does not exist')
    if dstdir == '':
        dstdir = srcdir
    filenames = glob.glob(op.join(srcdir, '*.png'))
    filepaths = [op.abspath(x) for x in filenames]
    azels = set()
    for i, filepath in enumerate(filepaths):
        filename = op.basename(filepath)
        srcfilename, extn = op.splitext(filename)
        sfnparts = srcfilename.split('-')
        az = int(sfnparts[4]) / 10.
        el = int(sfnparts[5]) / 10.
        azels.add((az, el))
    print('azels = ', azels)
    for azel in azels:
        az = azel[0]
        el = azel[1]
        aedstdir = op.join(dstdir, '{0:0>4d}-{1:0>4d}'.format(int(az * 10), int(el * 10)))
        print('srcdir, aedstdir, az, el = ', srcdir, aedstdir, az, el)
        copyforvideo(srcdir, aedstdir, az, el)

def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)

def createfilename(prefix, extention, p):
    datestr = '{0}{1:0>2d}{2:0>2d}'.format(p['date_year'], p['date_month'], p['date_day'])
    timestr = '{0:0>2d}{1:0>2d}{2:0>2d}'.format(p['date_hours'], p['date_minutes'], p['date_seconds'])
    passstr = '{0:0>3}'.format(p['passid'])
    azelstr = '{0:0>4d}-{1:0>4d}'.format(int(p['az']*10), int(p['el']*10))
    flname = '{0}-{1}-{2}-{3}-{4}.{5}'.format(prefix, datestr, timestr, passstr, azelstr, extention)
    return flname

def correctimagefilenames(catalog):
    topdatdir = op.dirname(op.dirname(op.abspath(catalog[0]['filename'][0])))
    datprddir = op.join(topdatdir, 'dataproducts')
    cachesdir = op.join(datprddir, 'caches')

    for p in catalog:
        rgpth = p['regularpath']
        nspth = p['nostarspath']
        pkpth = p['nspicklepath']
        rgdir = op.dirname(rgpth)
        nsdir = op.dirname(nspth)
        pkdir = op.dirname(pkpth)
        rgfln = createfilename('regular', 'png', p)
        nsfln = createfilename('nostars', 'png', p)
        pkfln = createfilename('nostars', 'pk', p)
        rgpthnew = op.join(rgdir, rgfln)
        nspthnew = op.join(nsdir, nsfln)
        pkpthnew = op.join(pkdir, pkfln)
        os.rename(rgpth, rgpthnew)
        os.rename(nspth, nspthnew)
        os.rename(pkpth, pkpthnew)
        p['regularpath'] = rgpthnew
        p['nostarspath'] = nspthnew
        p['nspicklepath'] = pkpthnew
        
    pkname = 'catalog.pk'
    pkpath = op.join(cachesdir, pkname)
    with open(pkpath, 'wb') as pkfile:
        cPickle.dump(catalog, pkfile)

    return catalog

def commondir(filenames):
    fns = [op.dirname(op.abspath(x)).split('/') for x in filenames]
    tdd = fns[0] # first estimate
    for filepath in fns:
        tddnew = []
        for i in range(min(len(tdd), len(filepath))):
            if tdd[i] == filepath[i]:
                tddnew.append(tdd[i])
            else:
                break
        tdd = tddnew
    return '/'.join(tdd)
    
def redopasses(catalog):
    cat = catalog
    passid = 0
    lastel = 0
    for posn in cat:
        if posn['el'] - lastel > 0:
            passid += 1
        lastel = posn['el']
        posn['passid'] = passid
    # calc pass stats
    catsplit = splitsames(cat, lambda a, b: a['passid'] == b['passid'])
    for skypass in catsplit:
        # init stats
        passmin = skypass[0]['rgmin']
        passmax = skypass[0]['rgmax']
        passmean = 0.
        passstdev = 0.
        nspassmin = skypass[0]['nsmin']
        nspassmax = skypass[0]['nsmax']
        nspassmean = 0.
        nspassstdev = 0.
        # calc stats
        for posn in skypass:
            passmin = min(passmin, posn['rgmin'])
            passmax = max(passmax, posn['rgmax'])
            passmean += posn['rgmean']
            passstdev += posn['rgstdev']
            nspassmin = min(nspassmin, posn['nsmin'])
            nspassmax = max(nspassmax, posn['nsmax'])
            nspassmean += posn['nsmean']
            nspassstdev += posn['nsstdev']
        n = len(skypass)
        passmean /= n
        passstdev /= n
        nspassmean /= n
        nspassstdev /= n
        # store stats; yes, saving pass stats in every position ... much duplication
        for posn in skypass:
            posn['rgpassmin'] = passmin
            posn['rgpassmax'] = passmax
            posn['rgpassmean'] = passmean
            posn['rgpassstdev'] = passstdev
            posn['nspassmin'] = nspassmin
            posn['nspassmax'] = nspassmax
            posn['nspassmean'] = nspassmean
            posn['nspassstdev'] = nspassstdev
    # calc night stats
    # init stats
    nightmin = cat[0]['rgmin']
    nightmax = cat[0]['rgmax']
    nightmean = 0.
    nightstdev = 0.
    nsnightmin = cat[0]['nsmin']
    nsnightmax = cat[0]['nsmax']
    nsnightmean = 0.
    nsnightstdev = 0.
    # calc stats
    for posn in cat:
        nightmin = min(nightmin, posn['rgmin'])
        nightmax = max(nightmax, posn['rgmax'])
        nightmean += posn['rgmean']
        nightstdev += posn['rgstdev']
        nsnightmin = min(nsnightmin, posn['nsmin'])
        nsnightmax = max(nsnightmax, posn['nsmax'])
        nsnightmean += posn['nsmean']
        nsnightstdev += posn['nsstdev']
    n = len(cat)
    nightmean /= n
    nightstdev /= n
    nsnightmean /= n
    nsnightstdev /= n
    # store stats; yes, saving night stats in every position ... much duplication
    for posn in cat:
        posn['rgnightmin'] = nightmin
        posn['rgnightmax'] = nightmax
        posn['rgnightmean'] = nightmean
        posn['rgnightstdev'] = nightstdev
        posn['nsnightmin'] = nsnightmin
        posn['nsnightmax'] = nsnightmax
        posn['nsnightmean'] = nsnightmean
        posn['nsnightstdev'] = nsnightstdev

    return cat

# this function takes a list of .img filenames or a directory containing .img files
# catalogs their contents (1 entry per position)
# for each position:
#   determines the pass id
#   determines a representitive frame
#   with the representitive frame
#     calc/store stats
#     calculates the no-stars frame
#     calc/store stats for the no-stars frame
#     save the no-stars array to a file (since expensive to calc)
# save the catalog to a file for use later
# return the catalog for use now
# cat20100309 = sg.catalog('/media/lavag/data20100308/100309', '', True)
def catalog(datalocn, resultsdir='', writecat=False):
    dostarremoval = True
    topdatdir = ''
    filenames = []
    # datalocn can either be
    #   a list of .img filenames OR
    #   a directory that containes .img files
    if isinstance(datalocn, list) and \
       len(datalocn) > 0 and \
       all(isinstance(filename, basestring) for filename in datalocn) and \
       all(op.isfile(filename) and filename.endswith('.img') for filename in datalocn):
        # datalocn is a non-empty list of .img filenames
        topdatdir = commondir(datalocn)
        filenames = datalocn
    elif isinstance(datalocn, basestring) and op.isdir(datalocn):
        # datalocn is a string and is a path to and actual directory
        topdatdir = op.abspath(datalocn)
        filenames = glob.glob(topdatdir + '/*.img')
        if len(filenames) == 0:
            raise RuntimeError('skyglow.catalog: no data files found in given data location')
    else:
        raise RuntimeError('skyglow.catalog: bad data location information: not dir or list of img files')

    filenames.sort()

    # ex. topdatdir   /media/lavag/100308
    #     resultsdir  /media/lavag/100308/meta <- catalog.pk file oes here
    #     cachesdir   /media/lavag/100308/meta/caches <- nostarcache

    if resultsdir == '':
        resultsdir = op.join(topdatdir, 'meta')
    if not op.isdir(resultsdir):
        os.makedirs(resultsdir)
    
    cachesdir = op.join(resultsdir, 'caches')
    if not op.isdir(cachesdir):
        os.makedirs(cachesdir)

    print('topdatdir   = ', topdatdir)
    print('resultsdir  = ', resultsdir)
    print('cacmhesdir   = ', cachesdir)

    cat00 = []
    nfiles = len(filenames)
    print('extracting az el information')
    for i, filename in enumerate(filenames):
        print('  {0:3d}/{1:3d}   {2}'.format(i, nfiles, filename)) # just to see progress during exec of azelix (slow)
        sys.stdout.flush()
        try:
            sf = ud.UAVData(filename)
        except RuntimeError:
            print('RuntimeError UAVData ctor, just skip it as a bad file for now: ', filename)
            continue
        except MemoryError:
            print('MemoryError UAVData ctor, just skip it as a bad file for now: ', filename)
            continue
        azels = sg.azelix(sf, 0, sf.K)
        cat00.append((filename, azels))

    # create catalog of positions (each position is a dictionary)
    # determine pass id for each position
    cat01 = []
    passid = 0
    lastel = 0
    for fnaes in cat00:
        filename = fnaes[0]
        azels = fnaes[1]
        for azel in azels:
            p = dict()
            begix = azel[0][0]
            endix = azel[0][1]
            p['framelocs'] = [{'filename': filename,
                               'begix': begix,
                               'endix': endix}]
            p['az'] = azel[1][0]
            p['el'] = azel[1][1]
            # the last positions in a pass have elevation 30
            # we use this to determine if we have started a new pass
            #if lastel == 30 and p['el'] != 30:
            #if lastel == 0 and p['el'] != 0:
            # 90 -  0 > 0  :  new passid
            # 90 - 30 > 0  :  new passid
            # 45 - 60 < 0  :  NO new passid
            if p['el'] - lastel > 0:
                passid += 1
            lastel = p['el']
            p['passid'] = passid
            cat01.append(p)

    # find cases where a position is split over multiple files and merge them
    prevp = cat01[0]
    removelist = []
    i = 0
    for p in cat01[1:]:
        prevazel = (prevp['az'], prevp['el'])
        azel = (p['az'], p['el'])
        if prevazel == azel:
            prevp['framelocs'] += p['framelocs']
            removelist.append(i + 1)
        prevp = p
        i += 1
    for removeix in removelist[::-1]: # iterate backwards so ix's remain valid
        cat01.pop(removeix)

    # determine representitive index for each position and calc stats for this image
    cat02 = []
    nposns = len(cat01)
    if dostarremoval:
        print('no-stars pickle paths')
    for i, p in enumerate(cat01):
        # find the middle frame (frames could be across multiple files)
        nframes = 0
        for frameloc in p['framelocs']:
            n = frameloc['endix'] - frameloc['begix'] + 1
            nframes += n
        midframe = (nframes + 1) / 2
        nframes = 0
        midloc = dict()
        for frameloc in p['framelocs']:
            n = frameloc['endix'] - frameloc['begix'] + 1
            nframes += n
            if nframes >= midframe:
                startn = nframes - n
                midix = midframe - startn
                midloc['filename'] = frameloc['filename']
                midloc['index'] = frameloc['begix'] + midix
                if midloc['index'] < frameloc['begix']:
                    print('**** tried to use midloc index of {0} in file: {1}, begix, endix = ({2}, {3})'.format(midloc['index'],
                                                                                                                 midloc['filename'],
                                                                                                                 frameloc['begix'],
                                                                                                                 frameloc['endix']))
                    midloc['index'] = frameloc['begix']
                if midloc['index'] > frameloc['endix']:
                    print('**** tried to use midloc index of {0} in file: {1}, begix, endix = ({2}, {3})'.format(midloc['index'],
                                                                                                                 midloc['filename'],
                                                                                                                 frameloc['begix'],
                                                                                                                 frameloc['endix']))
                    midloc['index'] = frameloc['endix']
                break

        uadata = ud.UAVData(midloc['filename'])

        try:
            fm = uadata.frame(midloc['index'])
        except IndexError:
            print('midloc error: filename: {0}, index: {1}'.format(midloc['filename'], midloc['index']))
            print('framelocs = ', p['framelocs'])
            print('len(uadata) = ', len(uadata))
            raise

        p['rep_frame'] = midloc

        p['rep_recorded_az'] = round(float(fm['TargetAzimuth']), 1)
        p['rep_recorded_el'] = round(float(fm['TargetElevation']), 1)

        timestamp = time.localtime(fm['LTime'])

        p['date_year'] = timestamp.tm_year
        p['date_month'] = timestamp.tm_mon
        p['date_day'] = timestamp.tm_mday
        p['date_hours'] = timestamp.tm_hour
        p['date_minutes'] = timestamp.tm_min
        p['date_seconds'] = timestamp.tm_sec
        
        dtfl = np.array(fm['Data'], dtype='float32')
        # scale data
        irradpcount = 0.105 # nW / cm2 / um  per  count
        dtfl *= irradpcount
        dtfl.shape = (fm['FrameSizeY'], fm['FrameSizeX'])
        # calc stats for scaled data before removing stars
        p['rgmin'] = dtfl.min()
        p['rgmax'] = dtfl.max()
        p['rgmean'] = dtfl.mean()
        p['rgstdev'] = dtfl.std()

        if dostarremoval:
            # remove stars
            dtflsr = medianfilt2(dtfl, 9)

            # pickle dtflsr to use later, because medianfilt2d takes a long time
            pkname = createfilename('nostars', 'pk', p)
            pkpath = op.join(cachesdir, 'nostarspk', pkname)
        
            print('  {0:3d}/{1:3d}   {2}'.format(i, nposns, pkpath)) # just to see progress during exec of azelix (slow)
            sys.stdout.flush()

            pkdir = op.dirname(pkpath)
            if not op.isdir(pkdir):
                os.makedirs(pkdir)
            
            p['nspicklepath'] = pkpath
            with open(pkpath, 'wb') as pkfile:
                cPickle.dump(dtflsr, pkfile)
            # calc stats for scaled data after removing stars
            p['nsmin'] = dtflsr.min()
            p['nsmax'] = dtflsr.max()
            p['nsmean'] = dtflsr.mean()
            p['nsstdev'] = dtflsr.std()

        cat02.append(p)

    # calc pass stats
    cat02split = splitsames(cat02, lambda a, b: a['passid'] == b['passid'])
    cat03 = []
    for skypass in cat02split:
        # init stats
        passmin = skypass[0]['rgmin']
        passmax = skypass[0]['rgmax']
        passmean = 0.
        passstdev = 0.
        if dostarremoval:
            nspassmin = skypass[0]['nsmin']
            nspassmax = skypass[0]['nsmax']
            nspassmean = 0.
            nspassstdev = 0.
        # calc stats
        for posn in skypass:
            passmin = min(passmin, posn['rgmin'])
            passmax = max(passmax, posn['rgmax'])
            passmean += posn['rgmean']
            passstdev += posn['rgstdev']
            if dostarremoval:
                nspassmin = min(nspassmin, posn['nsmin'])
                nspassmax = max(nspassmax, posn['nsmax'])
                nspassmean += posn['nsmean']
                nspassstdev += posn['nsstdev']
        n = len(skypass)
        passmean /= n
        passstdev /= n
        if dostarremoval:
            nspassmean /= n
            nspassstdev /= n
        # store stats; yes, saving pass stats in every position ... much duplication
        for posn in skypass:
            posn['rgpassmin'] = passmin
            posn['rgpassmax'] = passmax
            posn['rgpassmean'] = passmean
            posn['rgpassstdev'] = passstdev
            if dostarremoval:
                posn['nspassmin'] = nspassmin
                posn['nspassmax'] = nspassmax
                posn['nspassmean'] = nspassmean
                posn['nspassstdev'] = nspassstdev
            cat03.append(posn)
    
    if writecat:
        pkname = 'catalog.pk'
        pkpath = op.join(resultsdir, pkname)
        with open(pkpath, 'wb') as pkfile:
            cPickle.dump(cat03, pkfile)

    return cat03

# after assembling a catalog (from other catalogs if needed)
# we write the representitive image to files
def writepositionimages(catalog, resultsdir='', writecat=False):
    dostarremoval = True
    topdatdir = ''
    cat = []
    # catalog can either a
    #   catalog data structure OR
    #   file containing a catalog data structure
    if isinstance(catalog, list) and len(catalog) > 0:
        cat = catalog
    elif isinstance(catalog, basestring) and op.isfile(catalog):
        if os.access(catalog, os.R_OK):
            with open(catalog, 'rb') as catinput:
                cat = cPickle.load(catinput)
    else:
        raise RuntimeError('skyglow.writepositionimages: bad catalog parameter')

    topdatdir = commondir([x['framelocs'][0]['filename'] for x in catalog])
    print('topdatdir = ', topdatdir)
    
    if resultsdir == '':
        resultsdir = topdatdir

    metadir = op.join(resultsdir, 'meta')
    imagesdir = op.join(resultsdir, 'images')
    rgimagesdir = op.join(imagesdir, 'regular')
    nsimagesdir = op.join(imagesdir, 'nostars')

    print('metadir     = ', metadir)
    print('imagesdir   = ', imagesdir)
    print('rgimagesdir = ', rgimagesdir)
    print('nsimagesdir = ', nsimagesdir)

    if not op.isdir(metadir):
        os.makedirs(metadir)
    if not op.isdir(imagesdir):
        os.makedirs(imagesdir)
    if not op.isdir(rgimagesdir):
        os.makedirs(rgimagesdir)
    if not op.isdir(nsimagesdir):
        os.makedirs(nsimagesdir) 

    cat00 = []
    nposns = len(cat)
    print(nposns, ': ', sep='', end='')
    for i, p in enumerate(cat):
        print(i, ', ', sep='', end='')
        sys.stdout.flush()
        # write regular image
        filename = p['rep_frame']['filename']
        uadata = ud.UAVData(filename)
        fm = uadata.frame(p['rep_frame']['index'])
        dtfl = np.array(fm['Data'], dtype='float32')
        irradpcount = 0.105 # nW / cm2 / um  per  count
        dtfl *= irradpcount
        dtfl.shape = (fm['FrameSizeY'], fm['FrameSizeX'])

        # regular image scaled per pass
        mnclp = p['rgpassmean'] - 3.5 * p['rgpassstdev']
        mxclp = p['rgpassmean'] + 3.5 * p['rgpassstdev']
        dtim = dtfl - mnclp
        dvsor = (mxclp - mnclp)
        dtim = (dtim / dvsor) * 255
        dtim[dtim > 255] = 255
        dtim[dtim < 0] = 0
        dt08 = np.array(dtim, dtype='uint8')
        im = Image.fromarray(dt08)
        flname = createfilename('regular', 'png', p)
        flpath = op.join(rgimagesdir, flname)
        im.save(flpath)
        p['regularpath'] = flpath

        # regular image scaled per night
        mnclp = p['rgnightmean'] - 3.5 * p['rgnightstdev']
        mxclp = p['rgnightmean'] + 3.5 * p['rgnightstdev']
        dtim = dtfl - mnclp
        dvsor = (mxclp - mnclp)
        dtim = (dtim / dvsor) * 255
        dtim[dtim > 255] = 255
        dtim[dtim < 0] = 0
        dt08 = np.array(dtim, dtype='uint8')
        im = Image.fromarray(dt08)
        flname = createfilename('nightscaled-regular', 'png', p)
        flpath = op.join(rgimagesdir, flname)
        im.save(flpath)
        p['nightscaled-regularpath'] = flpath

        # write no stars image
        flpath = p['nspicklepath']
        if os.access(flpath, os.R_OK):
            with open(flpath, 'rb') as pkinput:
                dtfl = cPickle.load(pkinput)
        # nostars image scaled per pass
        mnclp = p['nspassmin']
        mxclp = p['nspassmax']
        dtim = dtfl - mnclp
        dvsor = (mxclp - mnclp)
        dtim = (dtim / dvsor) * 255
        dtim[dtim > 255] = 255
        dtim[dtim < 0] = 0
        dt08 = np.array(dtim, dtype='uint8')
        im = Image.fromarray(dt08)
        flname = createfilename('nostars', 'png', p)
        flpath = op.join(nsimagesdir, flname)
        im.save(flpath)
        p['nostarspath'] = flpath
        # append posn with image paths to catalog
        cat00.append(p)

    if writecat:
        pkname = 'catalog.pk'
        pkpath = op.join(metadir, pkname)
        with open(pkpath, 'wb') as pkfile:
            cPickle.dump(cat00, pkfile)

    return cat00

# done after calling writepositionimages
# pass in catalog that is returned by writepositionimages
def writecollageimages(catalog):
    cat = []
    if isinstance(catalog, list) and len(catalog) > 0:
        cat = catalog
    elif isinstance(catalog, basestring) and op.isfile(catalog):
        if os.access(catalog, os.R_OK):
            with open(catalog, 'rb') as catinput:
                cat = cPickle.load(catinput)
    else:
        raise RuntimeError('bad data location information: not dir or list of img files')

    # dataproducts/images/regular
    # dataproducts/images/nostars
    # dataproducts/images/collage
    imagesdir = op.dirname(op.dirname(op.abspath(cat[0]['regularpath'])))
    climagesdir = op.join(imagesdir, 'collage')
    if not op.isdir(climagesdir):
        os.makedirs(climagesdir)

    catsplit = splitsames(cat, lambda a, b: a['passid'] == b['passid'])

    imgnrows = cat[0]['FrameSizeY']
    imgncols = cat[0]['FrameSizeX']
    nrows = imgnrows
    ncols = imgncols
    fov = 15
    pixpdeg = ncols / fov
    minels = min([x['el'] for x in cat])
    totdegrs = 140
    if minels == 0:
        totdegrs = 170
    totdeg = totdegrs
    sz = totdeg * pixpdeg
    #sz = 9 * IMGNROWS * 1.3
    bigimsz = (sz, sz)
    monofontsm = ImageFont.load_default()
    monofontbg = ImageFont.load_default()
    smfontsz = imgnrows / 10
    bgfontsz = smfontsz * 3
    if sys.platform != 'win32':
        fontpath = '/usr/share/fonts/gnu-free/FreeMono.ttf'
        monofontsm = ImageFont.truetype(fontpath, smfontsz)
        monofontbg = ImageFont.truetype(fontpath, bgfontsz)
    # try instantiating these outside of loop for performance???
    # im, imcl, imadj, immsk, bigim
    im = Image.open(cat[0]['regularpath'])
    imcl = im.convert('RGB')
    imadj = appazel2(cat[0]['az'], cat[0]['el'], imcl)
    immsk = imadj.convert('L')
    bigim = Image.new('RGB', bigimsz)
    ncolgs = len(catsplit)
    for i, pas in enumerate(catsplit):
        bigim = Image.new('RGB', bigimsz)
        lssrmean = 0
        for p in pas:
            impt = p['regularpath']
            im = Image.open(impt)
            #print('convert im to RGB')
            #sys.stdout.flush()
            imcl = im.convert('RGB')
            #f = ImageFont.load_default()
            d = ImageDraw.Draw(imcl)
            d.text( (0, 0), u'{0} ({1}, {2})'.format(round(p['nsmean'], 2), round(p['az'], 1), round(p['el'], 1)), font=monofontsm, fill='#00ff00')
            #print('appazel2 imcl')
            #sys.stdout.flush()
            el = p['el']
            if el == 0:
                el = 15
            imadj = appazel2(p['az'], el, imcl)
            #print('convert imcl to L')
            #sys.stdout.flush()
            immsk = imadj.convert('L')
            #print('calc mask values')
            #sys.stdout.flush()
            immsk.putdata(map(lambda x: 255 if x > 0 else 0, immsk.getdata()))
            #print('paste into bigim')
            #sys.stdout.flush()
            #bigim.putdata(map(lambda a, b: (a[0] + b[0], a[1] + b[1], a[2] + b[2]), bigim.getdata(), imadj.getdata()))
            bigim.paste(imadj, (0, 0), immsk)
            #print('pasted ({0}, {1})'.format(round(p['az'], 1), round(p['el'], 1)))
            sys.stdout.flush()
            #bigim = Image.composite(bigim, imadj)
            
        p = pas[0]

        d = ImageDraw.Draw(bigim)
        avgstr = 'mean:{0}'.format(round(p['nspassmean'], 2))
        passstr = 'pass:{0:0>3}'.format(p['passid'])
        datestr = '{0}-{1:0>2}-{2:0>2}'.format(p['date_year'], p['date_month'], p['date_day'])
        timestr = '{0:0>2}:{1:0>2}:{2:0>2}'.format(p['date_hours'], p['date_minutes'], p['date_seconds'])
        d.text( (0, 0), avgstr + ' ' + passstr + ' ' + datestr + ' ' + timestr, font=monofontbg, fill='#00ff00')
        bimnm = 'collage-{1}{2:0>2}{3:0>2}-{4:0>2}{5:0>2}{6:0>2}-{0:0>3}.png'.format(p['passid'], p['date_year'], p['date_month'], p['date_day'], p['date_hours'], p['date_minutes'], p['date_seconds'])
        bimpt = op.join(climagesdir, bimnm)
        bigim.save(bimpt)
        print('{0:3d}/{1:3d}   {2}'.format(i, ncolgs, bimpt))
        sys.stdout.flush()

    for i, pas in enumerate(catsplit):
        bigim = Image.new('RGB', bigimsz)
        lssrmean = 0
        for p in pas:
            impt = p['nightscaled-regularpath']
            im = Image.open(impt)
            #print('convert im to RGB')
            #sys.stdout.flush()
            imcl = im.convert('RGB')
            #f = ImageFont.load_default()
            d = ImageDraw.Draw(imcl)
            d.text( (0, 0), u'{0} ({1}, {2})'.format(round(p['nsmean'], 2), round(p['az'], 1), round(p['el'], 1)), font=monofontsm, fill='#00ff00')
            #print('appazel2 imcl')
            #sys.stdout.flush()
            el = p['el']
            if el == 0:
                el = 15
            imadj = appazel2(p['az'], el, imcl, totdegrs)
            #print('convert imcl to L')
            #sys.stdout.flush()
            immsk = imadj.convert('L')
            #print('calc mask values')
            #sys.stdout.flush()
            immsk.putdata(map(lambda x: 255 if x > 0 else 0, immsk.getdata()))
            #print('paste into bigim')
            #sys.stdout.flush()
            #bigim.putdata(map(lambda a, b: (a[0] + b[0], a[1] + b[1], a[2] + b[2]), bigim.getdata(), imadj.getdata()))
            bigim.paste(imadj, (0, 0), immsk)
            #print('pasted ({0}, {1})'.format(round(p['az'], 1), round(p['el'], 1)))
            sys.stdout.flush()
            #bigim = Image.composite(bigim, imadj)
            
        p = pas[0]

        d = ImageDraw.Draw(bigim)
        avgstr = 'mean:{0}'.format(round(p['nspassmean'], 2))
        passstr = 'pass:{0:0>3}'.format(p['passid'])
        datestr = '{0}-{1:0>2}-{2:0>2}'.format(p['date_year'], p['date_month'], p['date_day'])
        timestr = '{0:0>2}:{1:0>2}:{2:0>2}'.format(p['date_hours'], p['date_minutes'], p['date_seconds'])
        d.text( (0, 0), avgstr + ' ' + passstr + ' ' + datestr + ' ' + timestr, font=monofontbg, fill='#00ff00')
        bimnm = 'nightscaled-collage-{1}{2:0>2}{3:0>2}-{4:0>2}{5:0>2}{6:0>2}-{0:0>3}.png'.format(p['passid'], p['date_year'], p['date_month'], p['date_day'], p['date_hours'], p['date_minutes'], p['date_seconds'])
        bimpt = op.join(climagesdir, bimnm)
        bigim.save(bimpt)
        print('{0:3d}/{1:3d}   {2}'.format(i, ncolgs, bimpt))
        sys.stdout.flush()

def appazel2(az, el, im, totdegrs, fov=15, sc=0.25):
    ncols, nrows = im.size
    #affarg = imaff(az, el, nrows, ncols)
    pixpdeg = ncols / fov
    totdeg = totdegrs
    sz = totdeg * pixpdeg
    #sz = 9 * IMGNROWS * 1.3
    newsize = (sz, sz)
    #print('ncols, nrows = ', im.size)
    #print('newsize = ', newsize)
    im2 = Image.new(im.mode, newsize)
    #print(im2.size)
    #im.paste(im2)
    # paste location
    #pl_n = sz/2 - nrows/2 - (totdeg / 2 - el) * pixpdeg
    pl_n = sz/2 - nrows/2 - (90 - el) * pixpdeg
    pl_w = sz/2 - ncols/2
    pl_s = pl_n + im.size[1]
    pl_e = pl_w + im.size[0]
    pasteloc = (pl_w, pl_n, pl_e, pl_s)
    #print('pasteloc = ', pasteloc)
    im2.paste(im, pasteloc)
    
    im3 = im2.rotate(az)
#    for i in xrange(20):
#        for j in xrange(20):
#            im3.putpixel((sz/2-10+i, sz/2-10+j), 255)
    for i in xrange(sz):
        im3.putpixel((sz/2-1, i), 255)
        im3.putpixel((sz/2, i), 255)
        im3.putpixel((sz/2+1, i), 255)

        im3.putpixel((i, sz/2-1), 255)
        im3.putpixel((i, sz/2), 255)
        im3.putpixel((i, sz/2+1), 255)

        #im3.putpixel((sz/2+(15*pixpdeg)-1, i), 255)
        #im3.putpixel((sz/2+(15*pixpdeg), i), 255)
        #im3.putpixel((sz/2+(15*pixpdeg)+1, i), 255)
        
        #im3.putpixel((sz/2-(15*pixpdeg)-1, i), 255)
        #im3.putpixel((sz/2-(15*pixpdeg), i), 255)
        #im3.putpixel((sz/2-(15*pixpdeg)+1, i), 255)
        
    return im3

# done after calling writecollageimages
# pass in catalog that is returned by writepositionimages
def writecatalogcollage(catalog):
    cat = []
    if isinstance(catalog, list) and len(catalog) > 0:
        cat = catalog
    elif isinstance(catalog, basestring) and op.isfile(catalog):
        if os.access(catalog, os.R_OK):
            with open(catalog, 'rb') as catinput:
                cat = cPickle.load(catinput)
    else:
        raise RuntimeError('bad data location information: not dir or list of img files')

    # dataproducts/images/regular
    # dataproducts/images/nostars
    # dataproducts/images/collage
    # dataproducts/catalogs/collage
    datprddir = op.dirname(op.dirname(op.dirname(op.abspath(cat[0]['regularpath']))))

    imagesdir = op.join(datprddir, 'images')
    climagesdir = op.join(imagesdir, 'collage')

    catlogdir = op.join(datprddir, 'catalogs')
    clcatlogdir = op.join(catlogdir, 'collage')

    if not op.isdir(clcatlogdir):
        os.makedirs(clcatlogdir)

    tex = \
"""% build a pdf like this:
% $ pdflatex file.tex
\\documentclass[letterpaper,12pt]{article}
%\\usepackage[top=1in, bottom=1in, left=1in, right=1in]{geometry} 
\\usepackage{fullpage}
\\usepackage{float}
\\usepackage{graphicx}
\\newfloat{program}{thp}{lop}
\\floatname{program}{Program}
\\setcounter{section}{0}

\\DeclareGraphicsExtensions{.png}
"""

    datestr = '{0}-{1:0>2}-{2:0>2}'.format(cat[0]['date_year'], cat[0]['date_month'], cat[0]['date_day'])

    tex += u'\\title{SHAPS Collages Catalog ' + datestr + u'}\n'

    tex += \
"""
\\author{Jason Addison\\\\
\\small Textron Systems Corporation, Maui\\\\
\\small \\texttt{jaddison@systems.textron.com}\\\\
}
"""

    tex += u'\\date{' + datetime.date.today().strftime('%B %d, %Y') + u'}\n'

    tex += u'\\begin{document}\n'
    tex += u'\\maketitle\n'
    tex += u'\\pagebreak\n'
    tex += u'\n'
    tex += u'\n'
    tex += u'\\pagestyle{myheadings}\n'
    tex += u'\\markright{Textron Systems Corporation, Maui, 2010\\hfill}\n'
    tex += u'\n'
    tex += u'\\setcounter{section}{-1}\n'

    colflnms = glob.glob(op.join(climagesdir, '*.png'))

    for fn in colflnms:
        tex += u'\\begin{figure}[!b]\n'
        tex += u'\\begin{center}\n'
        tex += u'\\includegraphics[width=7in]{../../images/collage/' + op.basename(fn) + u'}\n'
        tex += u'\\end{center}\n'
        tex += u'\\end{figure}\n'
        tex += u'\\pagebreak\n'
        tex += u'\\clearpage\n'

    tex += u'\\end{document}\n'

    datestr2 = '{0}{1:0>2}{2:0>2}'.format(cat[0]['date_year'], cat[0]['date_month'], cat[0]['date_day'])

    with open(op.join(clcatlogdir, 'catalog-collage-' + datestr2 + '.tex'), 'w') as outfile:
        outfile.write(tex)

def writecatalogpositions(catalog):
    cat = []
    if isinstance(catalog, list) and len(catalog) > 0:
        cat = catalog
    elif isinstance(catalog, basestring) and op.isfile(catalog):
        if os.access(catalog, os.R_OK):
            with open(catalog, 'rb') as catinput:
                cat = cPickle.load(catinput)
    else:
        raise RuntimeError('bad data location information: not dir or list of img files')

    # dataproducts/images/regular
    # dataproducts/images/nostars
    # dataproducts/images/collage
    # dataproducts/catalogs/collage
    # dataproducts/catalogs/positions
    datprddir = op.dirname(op.dirname(op.dirname(op.abspath(cat[0]['regularpath']))))
    catlogdir = op.join(datprddir, 'catalogs')
    pscatlogdir = op.join(catlogdir, 'positions')
    if not op.isdir(pscatlogdir):
        os.makedirs(pscatlogdir)

    tex = \
"""% build a pdf like this:
% $ pdflatex file.tex
\\documentclass[letterpaper,12pt]{article}
%\\usepackage[top=1.3in, bottom=1in, left=1in, right=1in]{geometry} 
\\usepackage{fullpage}
\\usepackage{float}
\\usepackage{graphicx}
\\newfloat{program}{thp}{lop}
\\floatname{program}{Program}

\\setlength{\\voffset}{-72pt}
\\setlength{\\topmargin}{36pt}
\\setlength{\\headheight}{12pt}
\\setlength{\\headsep}{18pt}
\\setlength{\\textheight}{690pt}



\\DeclareGraphicsExtensions{.png}
"""

    datestr = '{0}-{1:0>2}-{2:0>2}'.format(cat[0]['date_year'], cat[0]['date_month'], cat[0]['date_day'])

    tex += u'\\title{SHAPS Positions Catalog ' + datestr + u'}\n'

    tex += \
"""
\\author{Jason Addison\\\\
\\small Textron Systems, Maui\\\\
\\small \\texttt{jaddison@systems.textron.com}\\\\
}
"""

    tex += u'\\date{' + datetime.date.today().strftime('%B %d, %Y') + u'}\n'

    tex += u'\\begin{document}\n'
    tex += u'\\maketitle\n'
    tex += u'\\pagebreak\n'
    tex += u'\n'
    tex += u'\n'
    tex += u'\\pagestyle{myheadings}\n'
    tex += u'\\markright{Textron Systems Corporation, Maui, 2010\\hfill}\n'
    tex += u'\n'
    tex += u'\\setcounter{section}{-1}\n'


    catsplit = splitsames(cat, lambda a, b: a['passid'] == b['passid'])

    for pas in catsplit:
        p = pas[0]
        timestr = '{0:0>2}:{1:0>2}:{2:0>2}'.format(p['date_hours'], p['date_minutes'], p['date_seconds'])
        tex += u'\\section{Pass ' + repr(p['passid']) + ', time:' + timestr + ', ' + repr(len(pas)) + ' Positions}\n' 
        tex += u'\n'
        tex += u'\n'
        tex += u'\\begin{table}[b]\n'
        tex += u'\\begin{center}\n'
        tex += u'\\begin{tabular} {||r|r|r|r|r||} \\hline\n'
        tex += u'\\multicolumn{1}{||c}{}& \\multicolumn{1}{c}{min}& \\multicolumn{1}{c}{max}& \\multicolumn{1}{c}{mean}& \\multicolumn{1}{c||}{stdev}\\\\ \\hline\n'
        #print("type(p['rgpassmin']) = ", type(p['rgpassmin']))
        #print("type(p['rgpassmax']) = ", type(p['rgpassmax']))
        #print("type(p['rgpassmean']) = ", type(p['rgpassmean']))
        #print("type(p['rgpassstdev']) = ", type(p['rgpassstdev']))
        tex += u'{0}&{1:.2f}&{2:.2f}&{3:.2f}&{4:.2f}\\\\\n'.format('with stars', float(p['rgpassmin']), float(p['rgpassmax']), p['rgpassmean'], p['rgpassstdev'])
        tex += u'{0}&{1:.2f}&{2:.2f}&{3:.2f}&{4:.2f}\\\\ \\hline\n'.format('without stars', float(p['nspassmin']), float(p['nspassmax']), p['nspassmean'], p['nspassstdev'])
        tex += u'\\end{tabular}\n'
        tex += u'\\end{center}\n'
        tex += u'\\end{table}\n'
        tex += u'\n'
        tex += u'\\setcounter{subsection}{-1}\n'
        tex += u'\n'
        tex += u'\\pagebreak\n'
        tex += u'\\clearpage\n'
        tex += u'\n'
        tex += u'\n'
        for p in pas:
            # subsection
            # azel date time basename(filename)
            azelstr = 'azel:({0:.1f}, {1:.1f})'.format(float(p['az']), float(p['el']))
            datestr = '{0}-{1:0>2}-{2:0>2}'.format(p['date_year'], p['date_month'], p['date_day'])
            timestr = '{0:0>2}:{1:0>2}:{2:0>2}'.format(p['date_hours'], p['date_minutes'], p['date_seconds'])
            #fnixstr = '{0} index:{1}'.format(op.basename(p['ix'][0]), p['ix'][1])
            filestr = op.basename(p['rep_frame']['filename']).replace('_', '\_')
            indxstr = '{0}'.format(p['rep_frame']['index'])
            statstr = '(with stars) min, max, mean, stdev = {0:.2f}, {1:.2f}, {2:.2f}, {3:.2f}'.format(float(p['rgmin']), float(p['rgmax']), p['rgmean'], p['rgstdev'])
            nsstatstr = '(without stars) min, max, mean, stdev = {0:.2f}, {1:.2f}, {2:.2f}, {3:.2f}'.format(float(p['rgmin']), float(p['rgmax']), p['rgmean'], p['rgstdev'])
            rgpth = '../../images/regular/' + op.basename(p['regularpath'])
            nspth = '../../images/nostars/' + op.basename(p['nostarspath'])
            # date time
            # filename index
            # rg min max mean stdev
            # ns min max mean stdev

            tex += u'\\subsection{' + azelstr + u', time:' + timestr
            tex += u', file:' + filestr + u', index:' + indxstr + u'}\n'
            tex += u'\n'
            #tex += u'\\begin{figure}[!b]\n'
            tex += u'\\begin{figure}[h]\n'
            tex += u'\\begin{center}\n'
            tex += u'\\includegraphics[width=3.8in]{' + rgpth + u'}\n'
            tex += u'\\end{center}\n'
            tex += u'\\caption{' + statstr + '}\n'
            tex += u'\\end{figure}\n'
            tex += u'\n'
            #tex += u'\\begin{figure}[!b]\n'
            tex += u'\\begin{figure}[h]\n'
            tex += u'\\begin{center}\n'
            tex += u'\\includegraphics[width=3.8in]{' + nspth + u'}\n'
            tex += u'\\end{center}\n'
            tex += u'\\caption{' + nsstatstr + '}\n'
            tex += u'\\end{figure}\n'
            tex += u'\n'
            tex += u'\\pagebreak\n'
            tex += u'\\clearpage\n'
            tex += u'\n'
            tex += u'\n'
            tex += u'\n'
            tex += u'\n'
            tex += u''

    tex += u'\\end{document}\n'

    datestr2 = '{0}{1:0>2}{2:0>2}'.format(cat[0]['date_year'], cat[0]['date_month'], cat[0]['date_day'])

    with open(op.join(pscatlogdir, 'positions-' + datestr2 + '.tex'), 'w') as outfile:
        outfile.write(tex)

# pass in catalog from writepositionimages
def writeimagesforvideo(catalog, writecat=False):
    dostarremoval = True
    cat = []
    if isinstance(catalog, list) and len(catalog) > 0:
        cat = catalog
    elif isinstance(catalog, basestring) and op.isfile(catalog):
        if os.access(catalog, os.R_OK):
            with open(catalog, 'rb') as catinput:
                cat = cPickle.load(catinput)
    else:
        raise RuntimeError('bad data location information: not dir or list of img files')


    # dataproducts/images/regular
    # dataproducts/images/nostars
    # dataproducts/images/collage
    # dataproducts/catalogs/collage
    # dataproducts/catalogs/positions
    topdir = op.dirname(op.dirname(op.dirname(op.abspath(cat[0]['regularpath']))))
    metadir = op.join(topdir, 'meta')
    cachesdir = op.join(metadir, 'caches')
    vicachesdir = op.join(cachesdir, 'vidimages')
    if not op.isdir(vicachesdir):
        os.makedirs(vicachesdir)
	''' 	#watermark block
    wmpath = ''
    if sys.platform != 'win32':
        wmpath = '/home/jra/Documents/TEXTRON-logos/TEXTRONSystems-logo-noaa-87-grey.png'
    else:
        wmpath = 'C:\Documents and Settings\jra\My Documents\TEXTRON-logos\TEXTRONSystems-logo-noaa-87-grey.png'
    wmor = Image.open(wmpath)
    #wmsm = wmor.resize((87,11))
    wmsm = reduce_opacity(wmor, 0.25)
    # TODO
    imgnrows = cat[0]['FrameSizeY']
    imgncols = cat[0]['FrameSizeX']
    xpos = imgncols - 3 - 87
    ypos = imgnrows - 2 - 11


    catalogsec = []

    cntr = 0
	'''#end of watermark block

    for p in cat:
        # create list of frames to write
        lastltime = 0
        framelist = []
        for frameloc in p['framelocs']:
            uadata = ud.UAVData(frameloc['filename'])
            for ix in range(frameloc['begix'], frameloc['endix']):
                fm = uadata.framemeta(ix)
                if fm['LTime'] != lastltime:
                    framelist.append({'filename': frameloc['filename'],
                                      'index': ix})
                lastltime = fm['LTime']
        
        lastfilename = framelist[0]['filename']
        uadata = ud.UAVData(lastfilename)

        # get the star energy
        starirrad = p['rgmean'] - p['nsmean']
        fnt = ImageFont.load_default()
        if sys.platform != 'win32':
            fnt = ImageFont.truetype('/usr/share/fonts/gnu-free/FreeMonoBold.ttf', 12)

        mnclp = p['rgpassmean'] - 3 * p['rgpassstdev']
        mxclp = p['rgpassmean'] + 3 * p['rgpassstdev']

        print('cntr = ', cntr)
        cntr += 1
        print('first frame = ', framelist[0])
        print('last  frame = ', framelist[-1])
        print('az el = ', p['az'], ', ', p['el'])
        sys.stdout.flush()
        for fnix in framelist:
            psec = p
            # do we need to open a new datasource?
            if fnix['filename'] != lastfilename:
                uadata = ud.UAVData(fnix['filename'])
            lastfilename = fnix['filename']
            fd = uadata.frame(fnix['index'])
            dtim = np.array(fd['Data'], dtype='float32')
            irradpcount = 0.105 # nW / cm2 / um  per  count
            dtim *= irradpcount
            dtim.shape = (fd['FrameSizeY'], fd['FrameSizeX'])
            dtmean = dtim.mean() - starirrad
            psec['filename'] = fnix['filename']
            psec['frindex'] = ix
            psec['frmean'] = dtmean
            psec['frmax'] = dtim.max()
            psec['frmin'] = dtim.min()
            psec['frstdev'] = dtim.std()
            dtim -= mnclp
            dvsor = (mxclp - mnclp)
            dtim = (dtim / dvsor) * 255
            dtim[dtim > 255] = 255
            dtim[dtim < 0] = 0
            dt08 = np.array(dtim, dtype='uint8')
            im = Image.fromarray(dt08)
            imcl = im.convert('RGB')
            d = ImageDraw.Draw(imcl)
            avgstr = 'mean: {0:0>6.2f}'.format(round(dtmean, 2))
            passstr = 'pass: {0:0>3}'.format(p['passid'])
            ts = time.localtime(fd['LTime'])
            datestr = time.strftime('%Y%m%d-%H:%M:%S', ts) + '.' + '{0:0>3d}'.format(fd['MSTime'])
            azelstr = 'az el: {0: >5.1f}, {1: >5.1f}'.format(p['az'], p['el'])
            d.text( (5, 0), avgstr + ' ' + passstr + ' ' + datestr, font=fnt, fill='#00ff00')
            d.text( (5, 14), azelstr, font=fnt, fill='#00ff00')

            imcl.paste(wmsm, (xpos, ypos), wmsm)

            fdatestr = time.strftime('%Y%m%d-%H%M%S', ts) + '{0:0>3d}'.format(fd['MSTime'])

            flname = 'regular-'
            flname += fdatestr + '-'
            flname += '{0:0>3}'.format(p['passid']) + '-'
            flname += '{0:0>4d}-{1:0>4d}'.format(int(p['az']*10), int(p['el']*10))
            flname += '.png'
            flpath = op.join(vicachesdir, flname)
            imcl.save(flpath)

            timestamp = time.localtime(fd['LTime'])

            psec['date_year'] = timestamp.tm_year
            psec['date_month'] = timestamp.tm_mon
            psec['date_day'] = timestamp.tm_mday
            psec['date_hours'] = timestamp.tm_hour
            psec['date_minutes'] = timestamp.tm_min
            psec['date_seconds'] = float(timestamp.tm_sec) + float(fd['MSTime']) / 1000

            catalogsec.append(psec)
            print('.', end='', sep= '')
            sys.stdout.flush()
        print('')

    if writecat:
        pkname = 'catalogsec.pk'
        pkpath = op.join(vicachesdir, pkname)
        with open(pkpath, 'wb') as pkfile:
            cPickle.dump(catalogsec, pkfile)

    return catalogsec
        
def writecatalogsectext(catalog, textfilename):
    topdatdir = ''
    cat = []
    if isinstance(catalog, list) and len(catalog) > 0:
        cat = catalog
    elif isinstance(catalog, basestring) and op.isfile(catalog):
        if os.access(catalog, os.R_OK):
            with open(catalog, 'rb') as catinput:
                cat = cPickle.load(catinput)
    else:
        raise RuntimeError('bad data location information: not dir or list of img files')

    textdir = op.dirname(textfilename)

    if not op.isdir(textdir):
        os.makedirs(textdir)

    # filename
    # date
    # time
    # pass

    # passbegix
    # passendix
    # indexrepr
    # indexfr

    # passminest
    # passmaxest
    # passmeanest
    # passstdevest
    # nspassminest
    # nspassmaxest
    # nspassmeanest
    # nspassstdevest

    # minrepr
    # maxrepr
    # meanrepr
    # stdevrepr
    # nsminrepr
    # nsmaxrepr
    # nsmeanrepr
    # nsstdevrepr

    # frmin
    # frmax
    # frmean
    # frstdev

    # az
    # el

    dat = u''
    # write headers
    dat += u'filename indexfr date time pass '
    dat += u'passfile01 passbegix01 passendix01 '
    dat += u'passfile02 passbegix02 passendix02 ' # these will be blanks, "", if only one file
    dat += u'reprfilename reprindex '
    dat += u'passminest passmaxest passmeanest passstdevest '
    dat += u'nspassminest nspassmaxest nspassmeanest nspassstdevest '
    dat += u'minrepr maxrepr meanrepr stdevrepr '
    dat += u'nsminrepr nsmaxrepr nsmeanrepr nsstdevrepr '
    dat += u'frmin frmax frmean frstdev '
    dat += u'az el'
    dat += u'\n'
    lines = [dat]
    for p in cat:
        flfnstr = op.basename(p['filename'])
        datestr = u'{0}-{1:0>2d}-{2:0>2d}'.format(p['date_year'], p['date_month'], p['date_day'])
        timestr = u'{0:0>2d}:{1:0>2d}:{2:0>6.3f}'.format(p['date_hours'], p['date_minutes'], p['date_seconds'])
        azstr = u'{0:.1f}'.format(p['az'])
        elstr = u'{0:.1f}'.format(p['el'])
        if 'frindex' in p:
            indexfr = p['frindex']
        else:
            indexfr = u'" "'

        #print(azstr, 'type(azstr) = ', type(azstr))
        #print(elstr, 'type(elstr) = ', type(elstr))

        datline = u''
        datline += flfnstr + u' '
        datline += str(indexfr) + u' '
        datline += datestr + u' '
        datline += timestr + u' '
        datline += str(p['passid']) + u' '
        # only handling cases for 1 and 2
        if len(p['framelocs']) == 1:
            datline += str(p['framelocs'][0]['filename']) + u' '
            datline += str(p['framelocs'][0]['begix']) + u' '
            datline += str(p['framelocs'][0]['endix']) + u' '
            datline += '"" "" ""' + u' '
        if len(p['framelocs']) == 2:
            datline += str(p['framelocs'][0]['filename']) + u' '
            datline += str(p['framelocs'][0]['begix']) + u' '
            datline += str(p['framelocs'][0]['endix']) + u' '
            datline += str(p['framelocs'][1]['filename']) + u' '
            datline += str(p['framelocs'][1]['begix']) + u' '
            datline += str(p['framelocs'][1]['endix']) + u' '
        datline += str(p['rep_frame']['filename']) + u' '
        datline += str(p['rep_frame']['index']) + u' '
        datline += str(p['rgpassmin']) + u' '
        datline += str(p['rgpassmax']) + u' '
        datline += str(p['rgpassmean']) + u' '
        datline += str(p['rgpassstdev']) + u' '
        datline += str(p['nspassmin']) + u' '
        datline += str(p['nspassmax']) + u' '
        datline += str(p['nspassmean']) + u' '
        datline += str(p['nspassstdev']) + u' '
        datline += str(p['rgmin']) + u' '
        datline += str(p['rgmax']) + u' '
        datline += str(p['rgmean']) + u' '
        datline += str(p['rgstdev']) + u' '
        datline += str(p['nsmin']) + u' '
        datline += str(p['nsmax']) + u' '
        datline += str(p['nsmean']) + u' '
        datline += str(p['nsstdev']) + u' '
        datline += str(p['frmin']) + u' '
        datline += str(p['frmax']) + u' '
        datline += str(p['frmean']) + u' '
        datline += str(p['frstdev']) + u' '
        datline += u'{0} {1}\n'.format(azstr, elstr)

        lines.append(datline)

    with open(textfilename, 'w') as outfile:
        outfile.writelines(lines)

def addwatermark(imglob, imgncols, imgnrows):
    wmpath = '/home/jra/Documents/TEXTRON-logos/TEXTRONSystems-logo-noaa-87-grey.png'
    wmor = Image.open(wmpath)
    #wmsm = wmor.resize((87,11))
    wmsm = reduce_opacity(wmor, 0.25)
    impths = glob.glob(imglob)
    xpos = imgncols - 3 - 87
    ypos = imgnrows - 2 - 11
    impth = impths[0]
    imdir = op.dirname(impth)
    wmimdir = op.join(imdir, 'watermarked')
    if not op.isdir(wmimdir):
        os.makedirs(wmimdir)
    for impth in impths:
        imor = Image.open(impth)

        #imor = imor.convert('RGBA')
        #layer = Image.new('RGBA', imor.size, (0,0,0,0))
        #layer.paste(wmsm, (xpos, ypos))
        #imor = Image.composite(layer, imor, layer)

        imor.paste(wmsm, (xpos, ypos), wmsm)

        #imor.save(impth)
        #imsp = op.splitext(impth)
        imor.save(op.join(wmimdir, op.basename(impth)))

        print('.', sep='', end='')
        sys.stdout.flush()
    print('')

def reduce_opacity(im, opacity):
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy('RGBA')
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im

# sg.createpassvideos('/media/lavag/dataproducts/20100308/meta/caches/vidimages', '/media/lavag/dataproducts/20100308/video')
def createpassvideos(imgdir, viddir):
    if not op.isdir(imgdir):
        raise RuntimeError('createposnvideos: imgdir dne: ', imgdir)
    if not op.isdir(viddir):
        os.makedirs(viddir)
    imgsglb = op.join(imgdir, '*.png')
    imgpths = glob.glob(imgsglb)
    if len(imgpths) == 0:
        raise RuntimeError('createposnvideos: no files in imgdir')
    imgpths.sort()
    imgbnm = op.basename(imgpths[0])
    imgprf = imgbnm[:16]

    cmnd = r'/usr/bin/mencoder'
    mfarg = r'mf://' + imgsglb
    fparg0 = '-mf'
    fparg1 = 'fps=10'
    otarg0 = '-o'
    otarg1 = op.join(viddir, imgprf + '-200kbs.avi')
    enarg0 = '-ovc'
    enarg1 = 'lavc'
    enarg2 = '-lavcopts'
    enarg3 = 'vcodec=msmpeg4v2:vbitrate=200'

    print('cmnd mfarg fparg otarg enarg = ')
    print(cmnd, mfarg, fparg0, fparg1, otarg0, otarg1, enarg0, enarg1, enarg2, enarg3)
    sys.stdout.flush()

    try:
        subprocess.check_call([cmnd, mfarg, fparg0, fparg1, otarg0, otarg1, enarg0, enarg1, enarg2, enarg3])
    except subprocess.CalledProcessError:
        print('FAILURE')
        print('createposnvideos: CalledProcessError on azel: ', azel)
    else:
        print('SUCCESS')
        print('')

# sg.createposnvideos('/media/LAVAE/data20091214/dataproducts/caches/vidimages/watermarked', 
#                     '/media/LAVAE/data20091214/dataproducts/video')
def createposnvideos(imgdir, viddir):
    if not op.isdir(imgdir):
        raise RuntimeError('createposnvideos: imgdir dne: ', imgdir)
    if not op.isdir(viddir):
        os.makedirs(viddir)
    imgpths = glob.glob(op.join(imgdir, '*.png'))
    if len(imgpths) == 0:
        raise RuntimeError('createposnvideos: no files in imgdir')
    imgpths.sort()
    imgbnm = op.basename(imgpths[0])
    imgprf = imgbnm[:16]
    for azel in positions:
        # build az-el string
        azelstr = '{0:0>4d}-{1:0>4d}'.format(int(azel[0]*10), int(azel[1]*10))
        imgsglb = 'regular-*-*-*-' + azelstr + '.png'
        if len(glob.glob(op.join(imgdir, imgsglb))) == 0:
            continue
        cmnd = r'/usr/bin/mencoder'
        mfarg = r'mf://' + op.join(imgdir, imgsglb)
        fparg0 = '-mf'
        fparg1 = 'fps=10'
        otarg0 = '-o'
        otarg1 = op.join(viddir, imgprf + '-' + azelstr + '-200kbs.avi')
        enarg0 = '-ovc'
        enarg1 = 'lavc'
        enarg2 = '-lavcopts'
        enarg3 = 'vcodec=msmpeg4v2:vbitrate=200'



        print('cmnd mfarg fparg otarg enarg = ')
        print(cmnd, mfarg, fparg0, fparg1, otarg0, otarg1, enarg0, enarg1, enarg2, enarg3)
        sys.stdout.flush()

        try:
            subprocess.check_call([cmnd, mfarg, fparg0, fparg1, otarg0, otarg1, enarg0, enarg1, enarg2, enarg3])
        except subprocess.CalledProcessError:
            print('FAILURE')
            print('createposnvideos: CalledProcessError on azel: ', azel)
            continue
        else:
            print('SUCCESS')
            print('')


# mencoder "mf://../caches/vidimages/watermarked/*.png" -mf fps=10 -o regular-20100119-200kbs.avi -ovc lavc -lavcopts vcodec=msmpeg4v2:vbitrate=200
        



















positions = \
[(   0.0,      90.0), \
 ( 270.0,      75.0), \
 ( 180.0,      75.0), \
 (  90.0,      75.0), \
 (   0.0,      75.0), \
 (   0.0,      75.0), \
 (  90.0,      60.0), \
 (  45.0,      60.0), \
 (   0.0,      60.0), \
 ( 315.0,      60.0), \
 ( 270.0,      60.0), \
 ( 135.0,      60.0), \
 ( 135.0,      60.0), \
 ( 180.0,      60.0), \
 ( 225.0,      60.0), \
 ( 270.0,      45.0), \
 ( 247.5,      45.0), \
 ( 225.0,      45.0), \
 ( 202.5,      45.0), \
 ( 180.0,      45.0), \
 ( 180.0,      45.0), \
 ( 157.5,      45.0), \
 ( 135.0,      45.0), \
 ( 112.5,      45.0), \
 (  90.0,      45.0), \
 (  90.0,      45.0), \
 ( 292.5,      45.0), \
 ( 315.0,      45.0), \
 ( 315.0,      45.0), \
 ( 337.5,      45.0), \
 (   0.0,      45.0), \
 (  22.5,      45.0), \
 (  45.0,      45.0), \
 (  67.5,      45.0), \
 (  90.0,      30.0), \
 (  67.5,      30.0), \
 (  45.0,      30.0), \
 (  22.5,      30.0), \
 (  22.5,      30.0), \
 (   0.0,      30.0), \
 ( 337.5,      30.0), \
 ( 315.0,      30.0), \
 ( 292.5,      30.0), \
 ( 270.0,      30.0), \
 ( 270.0,      30.0), \
 ( 112.5,      30.0), \
 ( 135.0,      30.0), \
 ( 157.5,      30.0), \
 ( 180.0,      30.0), \
 ( 202.5,      30.0), \
 ( 225.0,      30.0), \
 ( 225.0,      30.0), \
 ( 247.5,      30.0)]





















def buildcollage_old(fns, cat=None):
    nrows = IMGNROWS
    ncols = IMGNCOLS
    fov = 15
    pixpdeg = ncols / fov
    sz = 180 * pixpdeg
    bigimsz = (sz, sz)
    bigim = Image.new('L', bigimsz)
    azels = []

    class ImgDat:
        ix = 0
        az = 0
        el = 0
        # scaled by 0.105 nW / cm2 / um  per count
        mn = 0.
        mx = 0.
        av = 0.
        sd = 0.
        # scaled by 0.105 nW / cm2 / um  per count
        srmn = 0.
        srmx = 0.
        srav = 0.
        srsd = 0.

    for fn in fns:
        irradpcount = 0.105 # nW / cm2 / um  per  count
        uad = ud.UAVData(fn)
        aes = []
        # if we have a catalog, find entry for filename fn
        if cat:
            ent = next((e for e in cat if e[0] == fn), None)
            if ent:
                aes = ent[1]
        # if couldn't find in catalog, need to calc azelix (time consuming)
        if len(aes) == 0:
            print('MISSED!!')
            aes = azelix(uad, 0, uad.K)

        # select one index from each look (azel) position
        # get stats for middle frame
        aes_dat = []
        azels_onefile = []
        sumav = 0.
        sumsd = 0.
        for ae in aes:
            begix, endix = ae[0][0], ae[0][1]
            azel = ae[1]
            if azel in azels_onefile:
                continue
            azels_onefile.append(azel)
            print('begix, endix, az, el = ', begix, endix, az, el)
            ix = begix + (endix - begix + 1) / 2
            # begin populating elm with ix, az, el
            elm = ImgDat()
            elm.ix = ix
            elm.az = azel[0]
            elm.el = azel[1]
            # get raw data from file
            fr = uad.frame(ix)
            dtfl = np.array(fr['Data'], dtype='float32')
            # scale data
            dtfl *= irradpcount
            # calc stats for scaled data before removing stars
            elm.mn = dat.min()
            elm.mx = dat.max()
            elm.av = dat.mean()
            elm.sd = dat.std()
            # remove stars
            dtfl.shape = (fr['FrameSizeY'], fr['FrameSizeX'])
            dtflsr = medianfilt2(dtfl, 9)
            # calc stats for scaled data after removing stars
            elm.srmn = datstr.min()
            elm.srmx = datstr.max()
            elm.srav = datstr.mean()
            elm.srsd = datstr.std()

            # accum for image scaling stats
            sumav += elm.av
            sumsd += elm.sd
            
            aes_reduced.append(elm)

        # calc image scaling stats
        n = len(aes_reduced)
        avav = sumav / n
        avsd = sumsd / n
        mnclp = avav - 3 * avsd
        mxclp = avav + 3 * avsd

        for ae in aes_reduced:
            fr = uad.frame(ae.ix)
            M, N = fr['FrameSizeY'], fr['FrameSizeX']
            dat = np.array(fr['Data'], dtype='float32')
            dat *= irradpcount
            dat[dat < mnclp] = mnclp
            dat[dat > mxclp] = mxclp
            dat -= mnclp
            dt8 = np.array(dat / mxclp * 255, dtype='uint8')
            dt8.shape = (M, N) # = (fr['FrameSizeY'], fr['FrameSizeX'])
            # create png file
            im = Image.fromarray(dt8)
            f = ImageFont.load_default()
            d = ImageDraw.Draw(im)
            d.text( (0, 0), u'{0}'.format(ae.srav), font=f, fill=255)
            imadj = af.appazel2(ae.az, ae.el, im)
            print('compositing')
            bigim.putdata(map(lambda a, b: a + b, bigim.getdata(), imadj.getdata()))
            #bigim = Image.composite(bigim, imadj)

    #nsz = 110 * pixpdeg
    #bigim = bigim.crop((sz/2-nsz/2, sz/2-nsz/2, sz/2+nsz/2, sz/2+nsz/2))

    f = ImageFont.load_default()
    d = ImageDraw.Draw(bigim)
    d.text( (0, 0), u'avg: {0}'.format(avav), font=f, fill=255)
    
    return bigim

def writewebpage(fns, dr):
    # if dir doesn't exist, make it with all parents
    # writeimgs for each file to ./images, collecting results
    # write index.html
    if not op.isdir(dr):
        os.makedirs(dr)
    imdr = op.join(dr, 'images')
    if not op.isdir(imdr):
        os.makedirs(imdr)
    imginfo = []
    for fn in fns:
        imginfo.append(writeimgs(fn, imdr, writenostars=True))
    ixfl = io.open(op.join(dr, 'index.html'), 'w')
    ixfl.writelines([u'<html>', u'<body>\n'])
    for fl in imginfo:
        entry = ''
        entry += fl[0] + u'<br><br>\n'
        for im in fl[2]:
            # im like (ix, fn, (begendix, azel))
            ae = im[2]
            begix, endix = ae[0][0], ae[0][1]
            az, el = ae[1][0], ae[1][1]
            impt = im[1][0]
            entry += u'<img src="{0}" /><br>\n'.format(impt)
            entry += op.basename(impt) + u'<br>\n'
            if len(im[1]) == 2:
                im2pt = im[1][1]
                entry += u'<img src="{0}" /><br>\n'.format(im2pt)
                entry += op.basename(im2pt) + u'<br>\n'
            entry += u'begin, end indicies: {0}, {1}<br>\n'.format(begix, endix)
            entry += u'az, el: {0}, {1}<br>\n'.format(az, el)
            entry += u'<br><br>\n\n'
        ixfl.write(entry)
    ixfl.writelines([u'</html>', u'</body>\n'])

def writewebpage2(catalog):
    topdatadir = ''
    cat = []
    if isinstance(catalog, list) and len(catalog) > 0:
        cat = catalog
    elif isinstance(catalog, basestring) and op.isfile(catalog):
        if os.access(catalog, os.R_OK):
            with open(catalog, 'rb') as catinput:
                cat = cPickle.load(catinput)
    else:
        raise RuntimeError('bad data location information: not dir or list of img files')

    topdatadir = op.dirname(op.dirname(op.abspath(cat[0]['filename'][0])))

    ctpath = op.join(topdatadir, 'catalog')
    if not op.isdir(ctpath):
        os.makedirs(ctpath)

    catsplit = splitsames(cat, lambda a, b: a['passid'] == b['passid'])

    # first lines of index.html
    with open(op.join(ctpath, 'index.html'), 'w') as ixfl:
        ixfl.writelines([u'<html>', u'<body>\n'])
        for pas in catsplit:
            fstlk = pas[0]
            lsentry = ''
            lsentry += u'<h2>Pass: {0:0>3}</h2>\n'.format(fstlk['passid'])
            lsentry += u'with stars (mean, stdev): {0:5.3}, {1:5.3}<br>\n'.format(fstlk['rgpassmean'], fstlk['rgpassstdev'])
            lsentry += u'without stars (mean, stdev): {0:5.3}, {1:5.3}<br>\n'.format(fstlk['nspassmean'], fstlk['nspassstdev'])
            lsentry += u'begin end times: {0:0>2d}:{1:0>2d}:{2:0>2d}-{3:0>2d}:{4:0>2d}:{5:0>2d}<br>\n'.format(fstlk['date_hours'], fstlk['date_minutes'], fstlk['date_seconds'], pas[-1]['date_hours'], pas[-1]['date_minutes'], pas[-1]['date_seconds'])
            for lk in pas:
                entry = ''
                entry += u'<h3>{0}-{1:0>2d}-{2:0>2d} {3:0>2d}:{4:0>2d}:{5:0>2d}</h3>\n'.format(lk['date_year'], lk['date_month'], lk['date_day'], lk['date_hours'], lk['date_minutes'], lk['date_seconds'])
                entry += u'Pass: {0:0>3d}<br>\n'.format(lk['passid'])
                entry += u'AZ EL: {0:0>5.1f}, {1:0>5.1f}<br>\n'.format(lk['az'], lk['el'])
                entry += u'{0}   index:{1:0>6d}<br><br>\n'.format(lk['filename'][0], lk['ix'][1])
    
                entry += u'<img src="{0}" /><br>\n'.format(op.join('./regular', op.basename(lk['regularpath'])))
                entry += u'With stars<br>\n'
                entry += u'min, max, mean, stdev: {0: >3.3}, {1: >3.3}, {2: >3.3}, {3: >3.3}<br><br>\n'.format(lk['rgmin'], lk['rgmax'], lk['rgmean'], lk['rgstdev'])
            
                entry += u'<img src="{0}" /><br>\n'.format(op.join('./nostars', op.basename(lk['nostarspath'])))
                entry += u'Without stars<br>\n'
                entry += u'min, max, mean, stdev: {0: >3.3}, {1: >3.3}, {2: >3.3}, {3: >3.3}<br>\n'.format(lk['nsmin'], lk['nsmax'], lk['nsmean'], lk['nsstdev'])
                entry += u'<br><br><br>\n'
                lsentry += entry
            lsentry += u'<br><br><br>\n'
            ixfl.write(lsentry)
        ixfl.writelines([u'</html>', u'</body>\n'])

def writeimgs_old(fn, dr, aes=None, writenostars=False):
    if not op.isdir(dr):
        raise RuntimeError('writeimages requires an existing directory as second param')
    if not op.isfile(fn):
        raise RuntimeError('writeimages requires an existing file as first param')
    nm, dummy = op.splitext(op.basename(fn))
    ua = ud.UAVData(fn)
    if aes == None:
        aes = azelix(ua, 0, ua.K)
    rsl = [fn, list(aes), []]
    for ae in aes:
        begix, endix = ae[0][0], ae[0][1]
        az, el = ae[1][0], ae[1][1]
        print('begix, endix, az, el = ', begix, endix, az, el)
        ix = begix + (endix - begix + 1) / 2
        fr = ua.frame(ix)
        M, N = fr['FrameSizeY'], fr['FrameSizeX']
        dt16 = np.array(fr['Data'], dtype='uint16')
        dbpp = 12 # data  12 bpp
        ibpp = 8 # image  8 bpp
        cnv = 2.0 ** (dbpp - ibpp)
        dt8 = np.array(dt16 / cnv, dtype='uint8')
        dt8.shape = (M, N) # = (fr['FrameSizeY'], fr['FrameSizeX'])
        # create png file
        im = Image.fromarray(dt8)
        imnm = (nm + '-{0:0>6}-{1:0>5.1f}-{2:0>5.1f}').format(ix, az, el) + '.png'
        impt = op.join(dr, imnm)
        imgflnms = (impt)
        im.save(op.join(impt))
        if writenostars:
            dtf = np.array(dt16, dtype='float32')
            dtf.shape = (M, N)
            dtf = medianfilt2(dtf, 9)
            dtf -= dtf.min()
            dtf /= dtf.max()
            print('dtf min max = ', dtf.min(), dtf.max())
            dt8 = np.array(dtf * ((2**8)-1), dtype='uint8')
            print('dt8 min max = ', dt8.min(), dt8.max())
            im2 = Image.fromarray(dt8)
            im2nm = (nm + '-nostars-{0:0>6}-{1:0>5.1f}-{2:0>5.1f}').format(ix, az, el) + '.png'
            im2pt = op.join(dr, im2nm)
            imgflnms = (impt, im2pt)
            im2.save(op.join(im2pt))
            print(op.join(im2pt))
        rsl[2].append((ix, imgflnms, ae))
    return rsl

def catalog_old(flst):
    """given a list of files:
    return filename/begin/end/az/el catalog as a 2-tuple of
    (1) a nested list
        [ [fn1 [[b1, e1], [az1, el1]],  [[b2, e2], [az2, el2]],  ... ], ... ]
    (2) a list of strings
        [ '"/path/to/filename.img"   b1   e1   az1   el1', ... ]
    """

    catalog = []
    for fnm in flst:
        print(fnm) # just to see progress during exec
        sys.stdout.flush()
        try:
            sf = ud.UAVData(fnm)
        except RuntimeError:
            print('RuntimeError ctor for UAVData, just skip it as a bad file for now')

        aes = sg.azelix(sf, 0, sf.K)
        catalog.append([fnm, aes])

    catalogstrg = []
    for fnmaes in catalog:
        fnm = fnmaes[0]
        aes = fnmaes[1]
        for ae in aes:
            begix, endix = ae[0][0], ae[0][1]
            az, el = ae[1][0], ae[1][1]
            catalogstrg.append('"' + fnm + '"' + \
                               repr(begix).rjust(10) + repr(endix).rjust(10) + \
                               repr(az).rjust(10) + repr(el).rjust(10))

    return catalog, catalogstrg

def splitcat(cat):
    newcat = []
    newcat.append([])
    lkset = 0
    lastel = 0
    for fl in cat:
        fn = fl[0]
        for lk in fl[1]:
            # a look set starts with azel = 0, 90
            # and ends with azels = xx, 30
            thisel = lk[1][1]
            if lastel == 30 and thisel != 30:
                lkset += 1
                newcat.append([])
            lastel = thisel
            newcat[-1].append((fn, lk))
    return newcat

# use cat generated from splitcat
def writestatsimages(cat, wdir):
    fn = cat[0][0][0]
    print('fn = ', fn)
    uad = ud.UAVData(fn)
    cate = []
    lookset = 0
    dosr = True
    for lks in cat:

        print('*' * 80)
        print('lookset = ', lookset)
        sys.stdout.flush()

        summeans = 0
        sumstdevs = 0
        srminmin = 2 ** 32
        srmaxmax = 0

        sumsrmeans = 0
        sumsrstdevs = 0

        catl = []

        for lk in lks:

            #print('  lk = ', lk)
            #sys.stdout.flush()

            elm = dict()

            elm['lookset'] = lookset

            # (fn, ((b, e), (az, el)))
            #thisfn = lk[0]
            #if fn != thisfn:
            #    uad = ud.UAVData(fn)
            #    fn = thisfn
            # sgYYYYMMDD-HH:MM:SS-LS-AZ-EL.png
            #   r12bpp
            #   starrm
            #   histst
            
            fn = lk[0]

            uad = ud.UAVData(fn)

            begix, endix = lk[1][0][0], lk[1][0][1]
            azel = lk[1][1]
            ix = begix + (endix - begix + 1) / 2

            #print(fn, ix, begix, endix, azel[0], azel[1])
            #sys.stdout.flush()

            elm['fn'] = fn
            elm['bg'] = begix
            elm['ed'] = endix
            elm['ix'] = ix

            fr = uad.frame(ix)

            elm['az'] = round(float(fr['TargetAzimuth']), 1)
            elm['el'] = round(float(fr['TargetElevation']), 1)

            while (elm['az'] != azel[0]) or (elm['el'] != azel[1]):
                ix -= 1
                fr = uad.frame(ix)
                elm['az'] = round(float(fr['TargetAzimuth']), 1)
                elm['el'] = round(float(fr['TargetElevation']), 1)
                #print('YIKES!')
                #print(elm['az'], elm['el'], ":", azel[0], azel[1])
                #raise RuntimeError('azels do not match')

            elm['ix'] = ix

            #filen = os.path.basename(fn)
            #elm['date_year'] = 2000 + int(filen[0:2])
            #elm['date_month'] = int(filen[2:4])
            #elm['date_day'] = int(filen[4:6])

            timestamp = time.localtime(fr['LTime'])

            elm['date_year'] = timestamp.tm_year
            elm['date_month'] = timestamp.tm_mon
            elm['date_day'] = timestamp.tm_mday
            elm['date_hours'] = timestamp.tm_hour
            elm['date_minutes'] = timestamp.tm_min
            elm['date_seconds'] = timestamp.tm_sec

            # get raw data from file
            dt16 = np.array(fr['Data'], dtype='uint16')
            dbpp = 12
            ibpp = 8
            cnv = 2.0 ** (dbpp - ibpp)
            dt08 = np.array(dt16 / cnv, dtype='uint8')
            dt08.shape = (fr['FrameSizeY'], fr['FrameSizeX'])

            # create r12bpp file
            im = Image.fromarray(dt08)
            imnm = 'sg-r12bpp-{0}{1:0>2d}{2:0>2d}-{3:0>2d}{4:0>2d}{5:0>2d}-{6:0>3}-{7:0>5.1f}-{8:0>5.1f}.png'.format(elm['date_year'], elm['date_month'], elm['date_day'], elm['date_hours'], elm['date_minutes'], elm['date_seconds'], elm['lookset'], elm['az'], elm['el'])
            impt = op.join(wdir, imnm)
            im.save(impt)

            elm['r12bpp_imagepath'] = impt

            print('  saved = ', impt)
            sys.stdout.flush()

            dtfl = np.array(fr['Data'], dtype='float32')
            # scale data
            irradpcount = 0.105 # nW / cm2 / um  per  count
            dtfl *= irradpcount
            dtfl.shape = (fr['FrameSizeY'], fr['FrameSizeX'])
            # calc stats for scaled data before removing stars
            elm['rgmin'] = dtfl.min()
            elm['rgmax'] = dtfl.max()
            elm['rgmean'] = dtfl.mean()
            elm['rgstdev'] = dtfl.std()

            # accum for image scaling stats
            summeans += elm['rgmean']
            sumstdevs += elm['rgstdev']

            if dosr:

                # remove stars
                dtflsr = medianfilt2(dtfl, 9)

                # pickle dtflsr to use later, because medianfilt2d takes a long time
                tmphndl, tmpflnm = tempfile.mkstemp(suffix='.pk', prefix='jrasr_')
                elm['srpickle'] = tmpflnm
                tmpfile = os.fdopen(tmphndl, 'w')
                cPickle.dump(dtflsr, tmpfile)
                tmpfile.close()
            
                # calc stats for scaled data after removing stars
                elm['srmin'] = dtflsr.min()
                elm['srmax'] = dtflsr.max()
                elm['srmean'] = dtflsr.mean()
                elm['srstdev'] = dtflsr.std()

                # accum for image scaling stats
                srminmin = min(srminmin, elm['srmin'])
                srmaxmax = max(srmaxmax, elm['srmax'])

                sumsrmeans += elm['srmean']
                sumsrstdevs += elm['srstdev']

            catl.append(elm)

        K = len(catl)
        meanmean = summeans / K
        meanstdev = sumstdevs / K
        mnclp = meanmean - 3 * meanstdev
        mxclp = meanmean + 3 * meanstdev

        if dosr:
            srmeanmean = srsummeans / K
            srmeanstdev = srsumstdevs / K

        print('^' * 80)
        sys.stdout.flush()
        

        for elm in catl:

            #print(elm['fn'], elm['ix'], elm['bg'], elm['ed'], elm['az'], elm['el'])
            #sys.stdout.flush()

            #thisfn = elm['fn']
            #if fn != thisfn:
            #    uad = ud.UAVData(fn)
            #    fn = thisfn

            fn = elm['fn']
            uad = ud.UAVData(fn)

            fr = uad.frame(elm['ix'])

            az = round(float(fr['TargetAzimuth']), 1)
            el = round(float(fr['TargetElevation']), 1)
            #print(az, el)
            #sys.stdout.flush()

            if (elm['az'] != round(float(fr['TargetAzimuth']), 1)) or \
               (elm['el'] != round(float(fr['TargetElevation']), 1)):
                raise RuntimeError('azels do not match (2)')
            
            dtfl = np.array(fr['Data'], dtype='float32')
            # scale data
            irradpcount = 0.105 # nW / cm2 / um  per  count
            dtfl *= irradpcount
            dtfl.shape = (fr['FrameSizeY'], fr['FrameSizeX'])

            elm['lsmean'] = meanmean
            elm['lsstdev'] = meanstdev
            elm['mnclp'] = mnclp
            elm['mxclp'] = mxclp

            dtim = dtfl - mnclp
            dvsor = (mxclp - mnclp)
            dtim = (dtim / dvsor) * 255
            dtim[dtim > 255] = 255
            dtim[dtim < 0] = 0
            dt08 = np.array(dtim, dtype='uint8')
            im = Image.fromarray(dt08)
            imnm = 'sg-histst-{0}{1:0>2d}{2:0>2d}-{3:0>2d}{4:0>2d}{5:0>2d}-{6:0>3}-{7:0>5.1f}-{8:0>5.1f}.png'.format(elm['date_year'], elm['date_month'], elm['date_day'], elm['date_hours'], elm['date_minutes'], elm['date_seconds'], elm['lookset'], elm['az'], elm['el'])
            impt = op.join(wdir, imnm)
            im.save(impt)

            elm['histst_imagepath'] = impt

            print('  saved = ', impt)
            sys.stdout.flush()

            if dosr:

                tempflnm = elm['srpickle']

                dtflsr = dtfl
                
                if os.access(tempflnm, os.R_OK):
                    with open(tempflnm, 'rb') as pkinput:
                        dtflsr = cPickle.load(pkinput)
                    os.remove(tempflnm)
                else:
                    print('SR TEMP MISS!!')
                    dtflsr = medianfilt2(dtfl, 9)

                elm['lssrmean'] = srmeanmean
                elm['lssrstdev'] = srmeanstdev
                elm['srmnclp'] = mnclp
                elm['srmxclp'] = mxclp

                dtim = dtflsr - srminmin
                dvsor = (srmaxmax - srminmin)# * 0.99
                dtim = (dtim / dvsor) * 255
                dtim[dtim > 255] = 255
                dtim[dtim < 0] = 0
                dt08 = np.array(dtim, dtype='uint8')
                im = Image.fromarray(dt08)
                imnm = 'sg-starrm-{0}{1:0>2d}{2:0>2d}-{3:0>2d}{4:0>2d}{5:0>2d}-{6:0>3}-{7:0>5.1f}-{8:0>5.1f}.png'.format(elm['date_year'], elm['date_month'], elm['date_day'], elm['date_hours'], elm['date_minutes'], elm['date_seconds'], elm['lookset'], elm['az'], elm['el'])
                impt = op.join(wdir, imnm)
                im.save(impt)

                elm['starrm_imagepath'] = impt

                print('  saved = ', impt)
                sys.stdout.flush()

        lookset += 1

        cate.append(catl)

    return cate


def azelix(udat, beg, end):
    """given a UAVData object, return list of beg/end indecies and az/els
    [ ((b1, e1), (az1, el1)),  ((b2, e2), (az2, el2)),  ... ]
    """
    # get a list of (ix, az, el) tuples
    # then split into a list of lists based on slewing frames (361,361)
    # [[(1, 0.0, 45.0), (2, 0.0, 45.0), ...] ...]
    tmp = splitfn([(x['FrameCounter'], \
                   round(x['TargetAzimuth'], 1), \
                   round(x['TargetElevation'], 1)) \
                       for x in [udat.framemeta(i) \
                                     for i in range(beg, end)]], \
                  lambda a: (a[1], a[2]) == (361.0, 361.0))
    rsl = []
    # combine each sublist into single entry
    # use the most frequent (az,el) as (az,el) for entire sublist
    for t in tmp:
        # count the occurance of each (az,el)
        counter = {}
        for e in t:
            ep = (e[1], e[2])
            if ep not in counter.keys():
                counter[ep] = 0
            counter[ep] += 1
        # find the highest
        maxk = counter.keys()[0]
        maxc = counter[maxk]
        for k in counter.keys():
            if counter[k] > maxc:
                maxk = k
                maxc = counter[k]
        # only count this sublist if it has a significant number of frames
        # otherwise it is probably bogus
        # 1-based to 0-based indexing
        begix = t[0][0] - 1
        endix = t[-1][0] - 1
        reqnfrms = 250
        if (endix - begix) > reqnfrms:
            rsl.append(((begix, endix), maxk))
    return rsl

def splitsames(seq, cmpfn=operator.eq):
    curval = seq[0]
    rsl = []
    for x in seq:
        if not cmpfn(x, curval):
            rsl.append([])
        curval = x
        if len(rsl) == 0:
            rsl.append([])
        rsl[-1].append(x)
    return rsl

def split(seq, vals):
    rsl = []
    flag = False # True iff last was real elem (not split elem)
    for x in seq:
        if x in vals: # split elem
            flag = False
        else: # real elem
            if not flag:
                rsl.append([])
            flag = True
            rsl[-1].append(x)
    return rsl
    
def splitfn(seq, cmpr):
    rsl = []
    flag = False # True iff last was real elem (not split elem)
    for x in seq:
        if cmpr(x): # split elem
            flag = False
        else: # real elem
            if not flag:
                rsl.append([])
            flag = True
            rsl[-1].append(x)
    return rsl
    
def extractdf(fr, mx=4096):
    # copy incomming array and convert to float64
    rs = np.array(fr['Data'], dtype=np.float64)
    rs = rs / mx
    rs.shape = (fr['FrameSizeY'], fr['FrameSizeX'])
    return rs

def removestars(image, mt=1, th=0.95, sz=7):
    img = np.array(image, dtype=np.float64)
    imin = img.min()
    img = img - imin
    imax = img.max()
    img = img / imax

    kr = np.ones((sz, sz))
    kr[1:-1, 1:-1] = 0
    kr /= sz * 4 - 4

    avgs = ic.convolve2d(img, kr)

    dif = abs(a - avgs)
    dif = setborder(dif, dif.mean(), int(sz/2))
    
    wts = nd.arange(1,512)
    hdf = st.histogram(dif, numbins=512, weights=wts)

    tot = hdf.sum()
    cof = 0
    cum = 0

    #cums = hdf.cumsum()

    for i in xrange(len(hdf)):
        cum += hdf[i]
        if cum / tot >= th:
            cof = i
            break

    pks = dif > (cof / 512)

    wch = np.array(pks)
    wm, wn = wch.shape
    wch[:, 0:wn-1] = wch[:, 1:wn] + pks[:, 1:wn]
    wch[:, 1:wn] = wch[:, 1:wn-1] + pks[:, 0:wn-1]
    wch[0:wm-1, :] = wch[1:wm, :] + pks[1:wm, :]
    wch[1:wm, :] = wch[0:wm-1, :] + pks[0:wm-1, :]

    img[wch] = 0.
    avgs[~wch] = 0.
    img = img + avgs
    
    return img * imax + imin

def setborder(a, b, n):
    r = np.array(a)
    M, N = r.shape
    r[0:n, :] = b # n
    r[M-n:M, :] = b # s
    r[:, 0:n] = b # w
    r[:, N-n:N] = b # e
    return r

def kmeanshist(ar, n):
    N = ar.size
    print('N = ', N)
    ks = np.zeros(n)
    for i in range(len(ks)):
        ks[i] = float(N) / (2 * n) - 0.5 + i * N / float(n)
    print('ks = ', ks)
    flag = True
    bail = 0
    while flag:
        ds = []
        for i in range(len(ks)-1):
            ds.append((ks[i] + ks[i+1]) / 2)
        newks = np.zeros(n)
        for i in range(len(ks)):
            if i == 0: beg = 0
            else: beg = int(ds[i-1])
            if i == len(ks)-1: end = N
            else: end = int(ds[i])
            sums = 0.
            cnts = 0.
            for j in range(beg, end):
                sums += j * ar[j]
                cnts += ar[j]
            newks[i] = sums / cnts
        diff = np.abs(newks - ks).sum()
        print('diff = ', diff)
        flag = diff
        ks = newks
        bail += 1
        if bail > 4: flag = False
    print('bail = ', bail)
    print('ks = ', ks)

def kmeans(arin, n):
    ar = arin.ravel()
    N = ar.size
    # init ks
    amin = ar.min()
    amax = ar.max()
    ks = np.linspace(amin, amax, num=n)

    lbls = np.zeros(N, dtype=np.int32)

    flag = True
    bail = 0
    while flag:
        # lable 'em
        for i in xrange(lbls.size):
            lbls[i] = 0
            for j in range(ks.size):
                if abs(ar[i] - ks[j]) < abs(ar[i] - ks[lbls[i]]):
                    lbls[i] = j

        # get new avgs for groups
        #kstat = range(ks.size)
        kstat = [[0, 0] for i in range(ks.size)]
        for i in xrange(lbls.size):
            kstat[lbls[i]][0] += ar[i]
            kstat[lbls[i]][1] += 1

        newks = np.array(ks)
        for j in range(ks.size):
            newks[j] = kstat[j][0] / kstat[j][1]

        diff = np.abs(newks - ks).sum()
        print('diff = ', diff)
        flag = diff
        ks = newks
        bail += 1
        if bail > 4: flag = False

    print('bail = ', bail)
    print('ks = ', ks)

def findsplit(hist):
    amx = hist.argmax()
    mx = hist.max()
    mn = hist.min()
    av = hist.mean()
    N = len(hist)
    # radius over which to calc test average
    rad = int(N * 0.005 / 2)
    # find a nice min value to cmpr test average
    nicemin = (hist[0] + hist[-1]) / 2. + (av - mn) * 0.1
    # keep track of index, i
    i = int(amx + N * 0.02)
    while 1:
        if hist[i-rad:i+rad].mean() < nicemin or i >= N * 0.15:
            break
        i += 1
    print('nicemin = ', nicemin)
    print('rng = ', hist[i-rad:i+rad])
    print('avg = ', hist[i-rad:i+rad].mean())
    return i

def killstars(imgin, thr):
    img = np.array(imgin)
    idiam = 10
    odiam = 15
    loradi = (odiam) / 2
    roradi = (odiam+1) / 2
    kr = circ2d(odiam)
    inner = pad(circ2d(idiam), (odiam, odiam), center=True)
    kr += inner * -1
    count = 0
    M, N = img.shape
    for i in xrange(img.shape[0]):
        for j in xrange(img.shape[1]):
            if i > 10 and i < (M-10) and \
               j > 10 and j < (N-10) and \
               img[i,j] >= thr:
                slc = imgin[i-loradi:i+roradi, j-loradi:j+roradi]
                img[i,j] = (slc * kr).sum() / kr.sum()
                count += 1
    return img

def circ2d(x, y=None):
    if y == None:
        y = x
    if (isnumeric(x) and isnumeric(y)):
        x = np.linspace(-y/2., y/2., y, endpoint=False) / x
        y = x
    X, Y = np.meshgrid(x, y)
    z = np.zeros_like(X)
    R = X**2 + Y**2
    w = R <= 0.25
    z[w] = 1
    n = w.sum()
    return z

def isnumeric(obj): 
    # consider only ints and floats numeric 
    return isinstance(obj,int) or isinstance(obj,float) 


# if(nargin < 2) y = x; end;   % allow for easy symmetry
# if(length(x) == 1 & length(y) == 1)  % specify width and number for centered array
#   x = linspace0(-y/2,y/2,y) / x;     % circ2d(5,128) is 128x128 with diameter~=5
#   y = x;
# end;
# 
# % uncentered circle
# if(nargin == 3)
#   c0 = ceil([length(y) length(x)] / 2 + 1); 
#   if(isempty(c)) c = c0; end;
#   x = vshift(x, c(1)-c0(1));
#   y = vshift(y, c(2)-c0(2));
# end;
#   
# [X,Y] = meshgrid(x, y);
# z=zeros(size(X));
# R = sq(X)+sq(Y);
# w = R <= .25;   % .25 == .5^2
# z(w) = 1;
# n = sum(w(:));

    
def avgdev(narr):
  return (np.fabs(narr - narr.mean())).mean()

def pad(orgarr, newshp, padval=0, center=False):

  # returns a list of all indecies in an array with shape, shp, as lists
  def genidx(shp):
    if len(shp) == 1:
      return [[x] for x in range(shp[0])]
    else:
      return [[n] + x for x in genidx(shp[1:]) for n in range(shp[0])]

  # list of lists to list of tuples
  def ll2lt(ll):
    return [tuple(x) for x in ll]

  # the original array
  orgtyp = orgarr.dtype
  orgshp = orgarr.shape
  orgdim = len(orgshp)
  # the new, result, array
  newdim = len(newshp)
  newarr = np.zeros(newshp, orgtyp)
  # the mask array
  mskshp = newshp
  mskdim = newdim
  mskarr = np.ones(mskshp, dtype=np.bool)
  # intersection of original and new shapes
  minshp = filter(lambda x: x != None, map(min, orgshp, newshp)) # a py array
  mindim = len(minshp)
  # clear the mask where original values will go
  for idx in genidx(minshp):
    # pad index if needed
    adjidx = [0] * mskdim
    adjidx[-mindim:] = idx
    # clear mask
    mskarr[tuple(adjidx)] = False
  # replace 0's in new array with pad value where mask is True
  for idx in ll2lt(genidx(mskshp)):
    if mskarr[idx] == True:
      newarr[idx] = padval
  # copy the original data into the new array
  for idx in genidx(minshp):
    # pad index if needed
    oadidx = [0] * orgdim
    oadidx[-mindim:] = idx
    nadidx = [0] * newdim
    nadidx[-mindim:] = idx
    newarr[tuple(nadidx)] = orgarr[tuple(oadidx)]

  if center:
    # index of new origin of original data
    newidx = [0] * newdim
    # extended minimum shape, shape of minimum array padded for new dimensions
    # pad with 1's for following calculation, (shape not index)
    emishp = [1] * newdim
    emishp[-mindim:] = minshp
    # newidx = (newshp - minshp) / 2
    newidx = map(lambda x: reduce(lambda y, z: (y - z) / 2, x), zip(newshp, emishp))
    # if the new origin is the same as old, [0,0,...], skip
    if reduce(lambda x, y: x + y, newidx) != 0:
      idxlst = genidx(minshp)
      idxlst.reverse()
      for idx in idxlst:
        frmidx = [0] * newdim
        frmidx[-mindim:] = idx
        # zip with plus
        tooidx = map(lambda x: reduce(lambda y, z: y + z, x), zip(frmidx, newidx))
        newarr[tuple(tooidx)] = newarr[tuple(frmidx)]
        newarr[tuple(frmidx)] = padval

  return newarr


def dice(side = 6, dimn = 5, typp = np.float32):
  dimn = int(dimn)

  n2a = (dimn * 1 / 2)
  n4a = (dimn * 1 / 4)
  n4b = (dimn * 3 / 4)

  r = np.zeros((dimn, dimn), type = typp)

  if (side % 2 == 1):
    r[n2a, n2a] = 1
  if (side > 1):
    r[n4a, n4b] = 1
    r[n4b, n4a] = 1
  if (side > 3):
    r[n4a, n4a] = 1
    r[n4b, n4b] = 1
  if (side > 5):
    r[n2a, n4a] = 1
    r[n2a, n4b] = 1

  return r

def iseven(val):
    return isinstance(val, int) and val % 2 == 0

def medianfilt2(imgin, ksize):
    M, N = imgin.shape
    ksz = int(ksize)
    lkrad = ksz / 2
    rkrad = ksz - lkrad

    imgmed = np.median(imgin)

    Mp = M + ksz - 1
    Np = N + ksz - 1
    
#     print('M = ', M)
#     print('N = ', N)
#     print('Mp = ', Mp)
#     print('Np = ', Np)
#     print('ksz = ', ksz)
#     print('lkrad = ', lkrad)
#     print('rkrad = ', rkrad)
#     print('imgmed = ', imgmed)

    imgpad = pad(imgin, (Mp, Np), padval=imgmed, center=True)

#     print('imgpad[:10, :10] = ', imgpad[:10, :10])

    imgout = np.zeros_like(imgin)

    for i in xrange(lkrad, Mp - rkrad + 1):
        for j in xrange(lkrad, Np - rkrad + 1):
            slc = imgin[i-lkrad:i+rkrad, j-lkrad:j+rkrad].ravel()
            imgout[i-lkrad, j-lkrad] = np.median(slc)
            
    return imgout
