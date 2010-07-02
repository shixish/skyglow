######################################
#Code written by: Andrew Wessels 2010#
#------------------------------------#
#This code is used to produce
# and manipulate a sqlite database
# for working with skyglow

#Useful for getting set up in terminal:
'''
import skyglowdb
reload(skyglowdb); db = skyglowdb.DB("/home/drew/prj/data/")
'''

import time, sys
from datetime import datetime as dt
import os
import os.path as op
import uavdata as ud
import sqlite3

import numpy as np
import matplotlib.pyplot as plt

import shutil

#used for vids
import glob
import subprocess

#used for images
from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageEnhance

import fnmatch, os

class DB:
	def __init__(self, rootdir=None):
		if rootdir == None:
			rootdir = os.path.abspath(os.curdir)
		self.rootdir = rootdir
		self.conn = sqlite3.connect(op.join(self.rootdir, 'sql'))
		self.c = self.conn.cursor()

	def __del__(self):
		# Save (commit) any changes
		self.conn.commit()
		# close the cursor, and connection
		self.c.close()
		self.conn.close()

	def locate(self, pattern, root=None):
		if not root:
			root = self.rootdir
		'''Locate all files matching supplied filename pattern in and below supplied root directory.'''
		for path, dirs, files in os.walk(os.path.abspath(root)):
			for filename in fnmatch.filter(files, pattern):
				yield os.path.join(path, filename)

	def backup(self):
		print "Are you sure you want to overwrite any previous backup?"
		answer = raw_input()
		if len(answer) > 0 and answer[0].lower() == "y" or answer == "1":
			shutil.copy(op.join(self.rootdir, 'sql'), op.join(self.rootdir, 'sql.bak'))
			print "Done."
		else:
			print "Unchanged."

	def restore(self):
		print "Are you sure you want to overwrite the current database with the backup?"
		answer = raw_input()
		if len(answer) > 0 and answer[0].lower() == "y" or answer == "1":
			shutil.copy(op.join(self.rootdir, 'sql.bak'), op.join(self.rootdir, 'sql'))
			print "Done."
		else:
			print "Unchanged."

	def sqlDict(self, c = None):
		if c == None:
			c = self.c
		c.row_factory = sqlite3.Row
		ret = list()
		for f in c.fetchall():
			x = 0
			vals = dict()
			for i in f.keys():
				vals[i] = f[x]
				x+=1
			ret.append(vals)
		return ret

	def sqlDataString(self, data):
		ret = ''
		first = True
		for i in data:
			if first:
				first = False
			else:
				ret+=','
			ret += "`"+str(i)+"`="+"'"+str(data[i])+"'"
		return ret	#this stuff isn't of any use atm, might be in the future...
	#self.c.execute("create table `frames` (LTime SMALLINT,MSTime SMALLINT,FrameCounter SMALLINT,DroppedFrames SMALLINT,FrameSizeX SMALLINT,FrameSizeY SMALLINT,TargetRange SMALLINT,Altitude SMALLINT,FocusStepOffset SMALLINT,BytesPerPixel SMALLINT,OffsetToImageData SMALLINT,CameraUsed SMALLINT,FilterWheelPosition SMALLINT,FocusMotorIndex SMALLINT,IntegrationTimeNS SMALLINT,TargetDeltaRange SMALLINT,TargetAzimuth INT,TargetElevation INT,TargetLatitude INT,TargetLongitutde INT,TargetAltitude INT,AircraftLatitude INT,AircraftLongitude INT,AircraftAltitude INT)")

	#["LTime","MSTime","FrameCounter","DroppedFrames","FrameSizeX","FrameSizeY","TargetRange","Altitude","FocusStepOffset","BytesPerPixel","OffsetToImageData","CameraUsed","FilterWheelPosition","FocusMotorIndex","IntegrationTimeNS","TargetDeltaRange","TargetAzimuth","TargetElevation","TargetLatitude","TargetLongitutde","TargetAltitude","AircraftLatitude","AircraftLongitude","AircraftAltitude"]
	#self.c.execute("insert into `frames` VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [round(d[x],1) for x in names])

	###################################
	# buildDB                         #
	#---------------------------------#
	# this builds the database..      #
	#  it populates the frames table, #
	#  and the positions table.       #
	###################################
	def buildDB(self, rebuild = False):
		imgfiles = []
		imgfiles[:] = self.locate('*.img', self.rootdir)
		imgfiles.sort()
		print (imgfiles)

		if rebuild:
			self.c.execute("drop table positions")
		self.c.execute("create table `positions` (az SMALLINT, el SMALLINT, start INT, end INT, count SMALLINT)")

		if rebuild:
			self.c.execute("drop table frames")
		self.c.execute("create table `frames` (idx INT PRIMARY_KEY, lt SMALLINT, ms SMALLINT, az SMALLINT, el SMALLINT, file TEXT, ix INT, mean SMALLINT, std SMALLINT)")
		last = dict()
		startid = 0
		lastid = 0
		lastaz= 0
		lastel = 0
		lastlt = 0
		count = 0
		idx = 0
		#d['time'] = time.localtime(md['LTime'])
		first = True
		for img in imgfiles:
			uadata = ud.UAVData(img)
			print "Data Entries: ", len(uadata)
			#positions = dict()
			then = time.time()
			for x in range(len(uadata)):
				d = uadata.frame(x)
				az = round(d['TargetAzimuth'], 1)
				el = round(d['TargetElevation'], 1)
				lt = d['LTime']
				ms = d['MSTime']
				if first: #initialize values
					lastaz = az
					lastel = el
					lastlt = lt
					first = False

				#this should take a frame every second
				if lastlt != lt:
					dtfl = np.array(d['Data'], dtype='float32')
					tmean = dtfl.mean()
					tstd = dtfl.std()
					values = [idx, lt, ms, az, el, img, x, tmean, tstd]
					self.c.execute("insert or ignore into `frames` (idx,lt,ms,az,el,file,ix,mean,std) VALUES(?,?,?,?,?,?,?,?,?,?)", values)
					if tmean < 250: #static frames
						az = 361
						el = 361
			
				#this doesnt work because there are errors in the data, so i'll fix the data later
				if (az != lastaz or el != lastel): #new position
					#print "new position detected"
					#self.c.execute("select * from `positions` where `start`='?' and `end`='?'", posStart, lastlt)
					values = [lastaz, lastel, startid, lastid, count]
					#print values
					#if count < 120:
						#print "Suspicious!"
					self.c.execute("insert into `positions` (az, el, start, end, count) VALUES(?,?,?,?,?)", values)
					firstpos = dict(d)
					startid = idx
					count = 0
				else:
					count += 1

				lastaz = az
				lastel = el
				lastlt = lt
				lastid = idx
				idx += 1
			now = time.time()
			bench = (now - then)
			print bench, " seconds"
		# Save (commit) the changes
		self.conn.commit()

	#################
	#end of build db#
	#################

	def buildPassData(self, rebuild = False):
		if rebuild:	
			self.c.execute("drop table passes")
		self.c.execute("create table `passes` (start DOUBLE UNIQUE, end DOUBLE UNIQUE)")

		#start running some stats
		self.c.execute("select rowid,* from `positions` where az != 361 and el != 361")
		data = self.sqlDict()
		firstdata = data[0]
		counts = []
		lastdata = data[0]
		passdata = []
		for i, e in enumerate(data):
			counts.append(e['el'])
			if e['el'] > lastdata['el']: #new pass
				print "pass from: ", firstdata['start'], "to", lastdata['end']
				self.c.execute("insert into `passes` (start, end) values (?,?)", (firstdata['start'], lastdata['end']))
				firstdata = e
			lastdata = e
		self.c.execute("insert into `passes` (start, end) values (?,?)", (firstdata['start'], lastdata['end']))
		print "last pass from: ", firstdata['start'], "to", lastdata['end']

		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.plot(counts)
		plt.show()
		# Save (commit) the changes
		self.conn.commit()

	def getDays(self):
		days = self.query("SELECT distinct strftime('%Y-%m-%d', lt, 'unixepoch', 'localtime') as day from frames")
		#self.query("SELECT strftime('%H:%M:%S', lt, 'unixepoch', 'localtime') as day, idx from frames order by idx asc limit 1")
			#this will return the first entry

		#self.query("SELECT strftime('%H:%M:%S', lt, 'unixepoch', 'localtime') as day, idx from frames order by idx desc limit 1")
			#this will return the last entry

	
	#This function is intended to be used to merge positions
	#TODO:: Fix this
	#c = database connection
	#dat = list of dictionary data from db
	#i = index of thing to merge
	#direction = 
	#	{
	#		 0 : merge both sides
	#		+1 : merge right
	#		-1 : merge left
	#	}
	def merge(self, c, data, i, direction):
		use = 0
		if direction == 0: #do both sides
			use = i+1
		else:
			use = i+(abs(direction)/direction) #i+1 or i-1
		data[i]['az'] = data[use]['az']
		data[i]['el'] = data[use]['el']
		if (direction < 0):
			data[i]['start'] = data[i-1]['start']
			data[i]['count'] += data[i-1]['count']
		if (direction > 0):
			data[i]['end'] = data[i+1]['end']
			data[i]['count'] += data[i+1]['count']
		if direction == 0:
			self.c.execute("delete from `positions` where rowid=? or rowid=?",(data[i-1]['rowid'],data[i+1]['rowid']))
			del data[i+1], data[i-1]
		else:
			self.c.execute("delete from `positions` where rowid=?",(data[use]['rowid'],))
			del data[use]
		return data

	#if options.clean:
	def fixPositions(self, perm = True, graph = False):
		print "Cleaning up the data"
		self.c.execute("select rowid,* from `positions` ")
		data = self.sqlDict()
		if not perm:
			graph=True
		if graph:
			#use this later to graph the original data
			original = list()
			for x in data:
				for z in range(x['count']):
					original.append(x['az']+x['el'])
				#original.append(0)
	
		prev = 0
		next = 0
		#this loop will make the algorithm do a few passes
		for passnum in range(5):
			#go through the list of dictionaries
			for i, e in enumerate(data):
				if i == len(data)-1:
					next = i
				else:
					next = i+1
				if i == 0:
					prev = 0
				else:
					prev = i-1
				ne = data[next]
				pe = data[prev]
				#use = prev #default is to extend the previous entry
				#rem = i
				if e['count'] < 100: #tiny fragment
					# i want the first pass to just fill up the blanks in the slewing frames
					if passnum < 2:
						if pe['az'] == ne['az'] and pe['el'] == ne['el'] and pe['az'] == 361 and pe['el'] == 361:
							e['count'] += pe['count'] + ne['count']
							e['start'] = pe['start']
							e['end'] = ne['end']
							e['az'] = ne['az']
							e['el'] = ne['el']
							if perm:
								self.c.execute("delete from `positions` where rowid=? or rowid=?",(pe['rowid'],ne['rowid']))
							del data[next], data[prev]
							#not working yet:						
							#data = merge(c, data, i, 0)
					else:
						if pe['az'] == ne['az'] and pe['el'] == ne['el']: #azel on either side are equivalent
							e['count'] += pe['count'] + ne['count']
							e['start'] = pe['start']
							e['end'] = ne['end']
							e['az'] = ne['az']
							e['el'] = ne['el']
							if perm:
								self.c.execute("delete from `positions` where rowid=? or rowid=?",(pe['rowid'],ne['rowid']))
							del data[next], data[prev]
						elif e['az'] == ne['az'] and e['el'] == ne['el']: #same azel as right side
							e['az'] = ne['az']
							e['el'] = ne['el']
							e['end'] = ne['end']
							e['count'] += ne['count']
							if perm:
								self.c.execute("delete from `positions` where rowid=?",(ne['rowid'],))
							del data[next]
						elif e['az'] == pe['az'] and e['el'] == pe['el']: #same azel as left side
							e['az'] = pe['az']
							e['el'] = pe['el']
							e['count'] += pe['count']
							e['start'] = pe['start']
							if perm:
								self.c.execute("delete from `positions` where rowid=?",(pe['rowid'],))
							del data[prev]
						elif ne['az'] == 361 and ne['el'] == 361: #next position is a slewing frame
							e['az'] = ne['az']
							e['el'] = ne['el']
							e['end'] = ne['end']
							e['count'] += ne['count']
							if perm:
								self.c.execute("delete from `positions` where rowid=?",(ne['rowid'],))
							del data[next]
						elif pe['az'] == 361 and pe['el'] == 361: #prev position is a slewing frame
							e['az'] = pe['az']
							e['el'] = pe['el']
							e['count'] += pe['count']
							e['start'] = pe['start']
							if perm:
								self.c.execute("delete from `positions` where rowid=?",(pe['rowid'],))
							del data[prev]
						else: #dont know what else to do with you, so just make it into slewing frames
							e['az'] = 361
							e['el'] = 361
					if perm:
						self.c.execute("update `positions` set "+self.sqlDataString(e)+" where rowid=?", (e['rowid'],))

		if graph:
			show = list()
			for x in data:
				for z in range(x['count']):
					show.append(x['az']+x['el'])
				#show.append(0)	
			#draw the graph
			fig = plt.figure()
			ax = fig.add_subplot(111)
			ax.plot(show, linewidth=2)
			ax.plot(original, linewidth=1)
			plt.show()
	
		# Save (commit) the changes
		self.conn.commit()

	def getFrames(self, frm, to):
		self.query("select idx, file, ix from `frames` where idx>=? and idx<=? order by idx", (frm, to))

	def query(self, query, var = []):
		if len(var) > 0:	
			self.c.execute(query, var)
		else:
			self.c.execute(query)
		ret = self.sqlDict()
		# Save (commit) the changes
		self.conn.commit()
		return ret

	#if options.graph:
	def graphPositions(self):
		#this gathers data for the graph
		data = self.query("select rowid,* from `positions` where az != 361 and el != 361")
		show = list()
		for x in data:
			for z in range(x['count']):
				show.append(x['az']+x['el'])
			show.append(0)

		#draw the graph
		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.plot(show, linewidth=1)
		plt.show()

	# this takes data (from sql) in sqlDict() form: [{'a':1, 'b':2}, {'a':3,'b':4}, ...]
	# write images (normal, and nostar) to file
	def writeimage(self, entry, resultsdir, mean = -1, std = -1, thresh = 5, az = -1, el = -1):
		#dostarremoval = True
		if az==-1 and el==-1:
			if 'az' in entry and 'el' in entry:
				az = entry['az']
				el = entry['el']
			else:
				raise RuntimeError('error: No azel supplied for image.')

		imagesdir = op.join(resultsdir, 'images')
		if not op.isdir(imagesdir):
		  os.makedirs(imagesdir)

		rgimagesdir = op.join(imagesdir, 'regular')
		if not op.isdir(rgimagesdir):
		  os.makedirs(rgimagesdir)
		'''
		usedir = op.join(rgimagesdir, str(el)+"-"+str(az))
		if not op.isdir(usedir):
		  os.makedirs(usedir)
		'''
		usedir = rgimagedir;
		'''
		nsimagesdir = op.join(imagesdir, 'nostars')
		if not op.isdir(nsimagesdir):
		  os.makedirs(nsimagesdir) 
		sys.stdout.flush()
		'''

		#open the file
		uadata = ud.UAVData(entry['file'])
		fm = uadata.frame(entry['ix'])
		#make it into a numpy array
		dtfl = np.array(fm['Data'], dtype='float32')
		irradpcount = 0.105 # nW / cm2 / um  per  count
		#dtfl *= irradpcount
		dtfl.shape = (fm['FrameSizeY'], fm['FrameSizeX'])
	
		#the data contains bad pixels, this is a mediocre way of removing them, and normalizing the data...
		if mean == -1 or std == -1: #if some scale factor isnt supplied, use whatever works for this image
			mean = dtfl.mean()
			std =  dtfl.std()
		#thresh = 5

		#this gets rid of extranious values, and just keeps the good stuff
		regular = np.clip(dtfl,mean-std*thresh,mean+std*thresh)

		'''
		#this one gets rid of the spikes...
		#leaves artifacts. no good really...
		spikeless = dtfl
		factor = 3
		for c,y in enumerate(spikeless):
			for i,e in enumerate(y):
				if e > tmean+tstd*factor or e < tmean-tstd*factor:
					spikeless[c][i] = tmean
				
					#print i, e
		'''
	
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
		print "--", entry['idx'], "--"
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
		use = regular
	
		ax.plot(use)
		ax.plot([use.mean()+use.std()]*len(use), linewidth=2)
		ax.plot([use.mean()-use.std()]*len(use), linewidth=2)
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
		#plt.show()
	

		# regular image scaled per pass
		
		#mnclp = p['rgpassmean'] - 3.5 * p['rgpassstdev']
		#mxclp = p['rgpassmean'] + 3.5 * p['rgpassstdev']

		use = regular
		prefix = "rg"
		#if az!=-1 and el!=-1:
		#	prefix += "-"+str(el)+"-"+str(az)

		#stretch values across 0-255
		#tmin = use.min()
		#tmax = use.max()
		tmin = mean-std*thresh
		tmax = mean+std*thresh
		use = use - tmin
		dvsor = (tmax - tmin)
		use = (use / dvsor) * 255

		im = Image.fromarray(np.array(use, dtype='uint8'))
		#not sure if i should use gmtime() or localtime()
		#looks like it needs to be localtime()
		#time.mktime() can be used to make these timestamps...
		# print time.mktime(time.localtime(ts)), ts
		flname = prefix+'-'+time.strftime("%Y%m%d-%H%M%S", time.localtime(fm['LTime']))+'-'+str(entry['MSTime'])+'.png'
		#flname = prefix+'-'+str(fm['LTime'])+'-'+str(fm['MSTime'])+'.png'
		im.save(op.join(usedir, flname))

	def makevid(self, imgdir, viddir = ''):
		if viddir == '':
			viddir = imgdir
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

##END OF DB CLASS##

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
