import datetime, time, sys
import os
import os.path as op
import uavdata as ud
import sqlite3
import testfunc as tf

import numpy as np
import matplotlib.pyplot as plt

from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageEnhance

#######################
#GET COMMAND-LINE ARGS#
#######################
from optparse import OptionParser
parser = OptionParser()
parser.add_option("--dir", help="directory to find the img files")
(options, args) = parser.parse_args()

rootdir = os.path.abspath(os.curdir)
if options.dir:
	if op.isdir(options.dir):
		rootdir = options.dir
	else:
		raise RuntimeError('testing: invalid directory supplied (--dir [location])')
#else:
#	raise RuntimeError('testing: no data directory supplied (--dir [location])')


###################
#CONNECT TO THE DB#
###################
conn = sqlite3.connect(op.join(rootdir, 'sql'))
c = conn.cursor()
c.row_factory = sqlite3.Row

################
#DATA RETRIEVAL#
################


#  "bad frames"
#c.execute("select frames.* from `positions`,`frames` where (positions.count < 120) and (frames.lt >= positions.start and frames.lt <= positions.end) GROUP BY (frames.lt)")


c.execute("drop table passes")
c.execute("create table `passes` (start DOUBLE UNIQUE, end DOUBLE UNIQUE)")

#start running some stats
c.execute("select rowid,* from `positions` where az != 361 and el != 361")
data = tf.sqlDict(c)
firstdata = data[0]
counts = []
lastdata = data[0]
passdata = []
for i, e in enumerate(data):
	counts.append(e['el'])
	if e['el'] > lastdata['el']: #new pass
		print "pass from: ", firstdata['start'], "to", lastdata['end']
		c.execute("insert into `passes` (start, end) values (?,?)", (firstdata['start'], lastdata['end']))
		firstdata = e
	lastdata = e
c.execute("insert into `passes` (start, end) values (?,?)", (firstdata['start'], lastdata['end']))
print "last pass from: ", firstdata['start'], "to", lastdata['end']

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(counts)
plt.show()


'''
dmin = 0
dmax = 0
first = True
for entry in data:
	uadata = ud.UAVData(entry['file'])
	fm = uadata.frame(entry['ix'])
	dtfl = np.array(fm['Data'], dtype='float32')
	# scale data
	irradpcount = 0.105 # nW / cm2 / um  per  count
	dtfl *= irradpcount
	dtfl.shape = (fm['FrameSizeY'], fm['FrameSizeX'])
	# calc stats for scaled data before removing stars
	print entry
	tmin = dtfl.min()
	tmax = dtfl.max()
	tmean = dtfl.mean()
	tstd =  dtfl.std()
	print 'rgmin:', tmin
	print 'rgmax:', tmax
	print 'rgmean:', tmean
	print 'rgstdev:', tstd
	if first:
		first = False
		dmin = tmin
		dmax = tmax
	else:
		if dmin > tmin:
			dmin = tmin
		elif dmax < tmax:
			dmax = tmax
	
print "Max value:", dmax
print "Min value:", dmin
'''

'''
for entry in data:
	uadata = ud.UAVData(entry['file'])
	fm = uadata.frame(entry['ix'])
	print fm['FrameSizeY'], fm['FrameSizeX'], fm['FrameSizeY']*fm['FrameSizeX'], len(fm['Data'])
	dtfl = np.array(fm['Data'], dtype='float32')
	fig = plt.figure()
	ax = fig.add_subplot(111)
	#ax.plot(dtfl)
	(n, bins) = np.histogram(dtfl, bins=50)
	ax.plot(.5*(bins[1:]+bins[:-1]), n)
	tmin = dtfl.min()
	tmax = dtfl.max()
	tmean = dtfl.mean()
	tstd =  dtfl.std()
	print 'rgmin:', tmin
	print 'rgmax:', tmax
	print 'rgmean:', tmean
	print 'rgstdev:', tstd
	plt.show()
'''


#print plotvals

##CALCULATIONS
#      26022 (total) - 20185 (salvaged) = 5837
#  5837 total frames lost
# -3726 known slewing frames
#--------
#  2111 possible good frames lost
#			This is 8.1123665%
#			Acceptable loss?
#TODO::build these frames, visually inspect their quality. (possibly salvageable)
#- some of the frames look ok


'''
c.execute("select az,el,(az+el) from `frames`")
vals = c.fetchall()
print "frames: ", len(vals)
count = 0
lastx = vals[0]
for x in vals:
	if (lastx[1] - x[1] > 0):
		print "New Pass?"
	if (lastx != x):
		print lastx, "x", count
		lastx = x
		count = 0
	else:
		count += 1
		lastx = x
'''

#conditional insert commands
#INSERT INTO <table> (field1, field2...) VALUES (value1, value2...) WHERE (SELECT COUNT(*) FROM <table> WHERE <ColumnToCheck> = <ValueToCompare>) > 0;




######################
#FUNCTION DEFINITIONS#
######################
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

# this takes data (from sql) in sqlDict() form: [{'a':1, 'b':2}, {'a':3,'b':4}, ...]
# write images (normal, and nostar) to file
def writeimage(entry, resultsdir):
	dostarremoval = True
	imagesdir = op.join(resultsdir, 'images')
	rgimagesdir = op.join(imagesdir, 'regular')
	nsimagesdir = op.join(imagesdir, 'nostars')
	if not op.isdir(imagesdir):
	  os.makedirs(imagesdir)
	if not op.isdir(rgimagesdir):
	  os.makedirs(rgimagesdir)
	if not op.isdir(nsimagesdir):
	  os.makedirs(nsimagesdir) 
	sys.stdout.flush()

	#open the file
	uadata = ud.UAVData(entry['file'])
	fm = uadata.frame(entry['ix'])
	#make it into a numpy array
	dtfl = np.array(fm['Data'], dtype='float32')
	irradpcount = 0.105 # nW / cm2 / um  per  count
	dtfl *= irradpcount
	dtfl.shape = (fm['FrameSizeY'], fm['FrameSizeX'])
	
	##p = the current catalog

	#this gets rid of extranious values, and just keeps the good stuff
	#the data contains bad pixels, this is a mediocre way of removing them, and normalizing the data...
	tmean = dtfl.mean()
	tstd =  dtfl.std()
	threshold = 5
	regular = np.clip(dtfl,tmean-tstd*threshold,tmean+tstd*threshold)
	
	#this also works...	
	'''
	(n, bins) = np.histogram(dtfl, bins=100)
	tmin = 0
	tmax = 0
	findmin = True
	for i,e in enumerate(bins):
		if n[i] > 5:
			findmin = False
		if n[i] <= 5:
			if findmin:			
				tmin = i
			else:
				tmax = i
				break
	print "min:", bins[tmin], "max:", bins[tmax]
	
	histodata = np.clip(dtfl,bins[tmin],bins[tmax])
	'''
	
	#more complicated, more data lost
	#nostar = medianfilt2(dtfl, 9)
	
	'''
	print 'rgmin:', regular.min()
	print 'rgmax:', regular.max()
	print 'rgmean:', regular.mean()
	print 'rgstdev:', regular.std()
	'''

	'''
	fig = plt.figure()
	ax = fig.add_subplot(111)
	(n, bins) = np.histogram(dtfl, bins=100)
	#ax.plot(.5*(bins[1:]+bins[:-1]), n)
	plt.show()
	'''
	'''
	fig = plt.figure()
	ax = fig.add_subplot(111)
	#ax.plot(regular)
	#ax.plot([bins[tmin]]*len(regular), linewidth=2)
	#ax.plot([bins[tmax]]*len(regular), linewidth=2)
	ax.plot([regular.mean()+regular.std()]*len(regular), linewidth=2)
	ax.plot([regular.mean()-regular.std()]*len(regular), linewidth=2)
	'''
	'''
	ax.plot(histodata)
	ax.plot([histodata.mean()+histodata.std()]*len(histodata), linewidth=2)
	ax.plot([histodata.mean()-histodata.std()]*len(histodata), linewidth=2)
	'''

	'''
	ax.plot(nostar)
	ax.plot([nostar.mean()+nostar.std()]*len(nostar), linewidth=2)
	ax.plot([nostar.mean()-nostar.std()]*len(nostar), linewidth=2)
	'''	
	plt.show()
	

	# regular image scaled per pass
		
	#mnclp = p['rgpassmean'] - 3.5 * p['rgpassstdev']
	#mxclp = p['rgpassmean'] + 3.5 * p['rgpassstdev']
	'''
	mnclp = tmean - 1.5 * tstd
	mxclp = tmean + 1.5 * tstd
	dtim = dtfl - mnclp
	dvsor = (mxclp - mnclp)
	dtim = (dtim / dvsor) * 255
	dtim[dtim > 255] = 255
	dtim[dtim < 0] = 0
	dt08 = np.array(dtim, dtype='uint8')
	'''

	use = regular
	prefix = "rg"
	#stretch values across 0-255
	tmin = use.min()
	tmax = use.max()
	use = use - tmin
	dvsor = (tmax - tmin)
	use = (use / dvsor) * 255

	im = Image.fromarray(np.array(use, dtype='uint8'))
	flname = str(entry['ix'])+'-'+prefix+'-'+time.strftime("%Y%m%d-%H%M%S", time.localtime(fm['LTime']))+'.png'
	im.save(op.join(rgimagesdir, flname))
	#p['regularpath'] = flpath
	'''
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

	return cat00
	'''
c.execute("select rowid,* from `frames` LIMIT 1000,200")
data = tf.sqlDict(c)
print "New data loaded: ", len(data)
for x in data:
	writeimage(x, rootdir)


# Save (commit) the changes
conn.commit()

# We can also close the cursor if we are done with it
c.close()
conn.close()
