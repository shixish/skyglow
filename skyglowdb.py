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
reload(skyglowdb); bdb = skyglowdb.DB("/media/lavag")
'''

import time, sys
from datetime import datetime as dt
#i made this one to help with manipulating the time info
import dbtime
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
	def build(self, rebuild = False):
		imgfiles = []
		imgfiles[:] = self.locate('*.img', self.rootdir)
		imgfiles.sort()
		print (imgfiles)

		if rebuild:
			self.c.execute("drop table positions")
		self.c.execute("create table `positions` (az SMALLINT, el SMALLINT, start INT, end INT, count SMALLINT)")

		if rebuild:
			self.c.execute("drop table frames")
		self.c.execute("create table `frames` (lt SMALLINT, ms SMALLINT, az SMALLINT, el SMALLINT, file TEXT, ix INT, mean SMALLINT, std SMALLINT)")
		lastel = 0
		lastaz = 0
		lastlt = 0
		startlt = 0
		first = True
		count = 0
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
					lastel = el
					lastaz = az
					lastlt = lt
					first = False

				#this should take a frame every second
				if lastlt != lt:
					dtfl = np.array(d['Data'], dtype='float32')
					tmean = dtfl.mean()
					tstd = dtfl.std()
					values = [lt, ms, az, el, os.path.relpath(img, start=self.rootdir), x, tmean, tstd]
					#print values
					self.c.execute("insert into `frames` (lt,ms,az,el,file,ix,mean,std) VALUES(?,?,?,?,?,?,?,?)", values)
					if tmean < 250: #static frames
						az = 361
						el = 361
				
				#this doesnt work because there are errors in the data, so i'll fix the data later
				if (az != lastaz or el != lastel): #new position detection
					values = [lastaz, lastel, startlt, lastlt, count]
					#print values
					self.c.execute("insert into `positions` (az, el, start, end, count) VALUES(?,?,?,?,?)", values)
					startlt = lt
					count = 0
			
				lastel = el
				lastaz = az
				lastlt = lt
				count += 1
				lastlt = lt
			now = time.time()
			bench = (now - then)
			print bench, " seconds"
			sys.stdout.flush()
		# Save (commit) the changes
		self.conn.commit()
		return self #allows for chaining

	#################
	#end of build db#
	#################

	def doPasses(self, rebuild = False):
		if rebuild:	
			self.c.execute("drop table passes")
		self.c.execute("create table `passes` (start INT UNIQUE, end INT UNIQUE)")

		#start running some stats
		data = self.query("select rowid,* from `positions` where az != 361 and el != 361")
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
		return self #allows for chaining

	def doNights(self, rebuild = False):
		if rebuild:	
			self.c.execute("drop table nights")
		self.c.execute("create table `nights` (start INT UNIQUE, end INT UNIQUE)")
		days = self.query("SELECT lt from frames where lt%30=0 group by strftime('%Y-%m-%d', lt, 'unixepoch', 'localtime')")
		#throwing this in just incase there is something before noon on the first detected day...		
		justincase = dbtime.dbtime(days[0]['lt'])
		justincase["day"]-=1
		days.insert(0,{"lt":int(justincase)})
		for x in days:
			local = dbtime.dbtime(x['lt'])
			start = int(local.set({"hour":12, "min":0, "sec":0}))
			local["day"]+=1
			end = int(local)
			format = '%Y-%m-%d %H:%M:%S'
			#print start, end
			#frames = self.query("select count(*) from frames where lt >= ? and lt <= ?", (start, end))
			#print "Found", frames, "elements"
			firstdata = self.query("SELECT lt from frames where ? < lt and lt <= ? order by lt asc limit 1", (start, end))
			lastdata = self.query("SELECT lt from frames where ? < lt and lt <= ? order by lt desc limit 1", (start, end))
			print "Between", dbtime.dbtime(start).strftime(format)[0], "and", dbtime.dbtime(end).strftime(format)[0]
			#print "from", firstdata, "to", lastdata
			if len(firstdata):
				print "   First:", dbtime.dbtime(firstdata[0]['lt']).strftime(format)[0], "Last:", dbtime.dbtime(lastdata[0]['lt']).strftime(format)[0]
				vals = (firstdata[0]['lt'], lastdata[0]['lt'])
				self.query("insert into `nights` (start, end) values (?,?)", vals)
			else:
				print "   Nothing"
		return self #allows for chaining
			
	'''
	This wont really work... Needs greater detail than what 1 second frames can give...
	def doPositions(self, rebuild = False):
		if rebuild:
			self.c.execute("drop table positions")
		self.c.execute("create table `positions` (az SMALLINT, el SMALLINT, start INT, end INT, count SMALLINT)")
		frames = self.query("SELECT * from frames order by lt")
		lastel = 0
		lastaz = 0
		lastlt = 0
		startlt = 0
		first = True
		count = 0
		for x in frames:
			az = x['az']
			el = x['el']
			lt = x['lt']
			if first:
				lastel = el
				lastaz = az
				lastlt = lt
				first = False
			if x['mean'] < 250: #static frames
				az = 361
				el = 361
			#this doesnt work because there are errors in the data, so i'll fix the data later
			if (az != lastaz or el != lastel): #new position detection
				values = [lastaz, lastel, startlt, lastlt, count]
				#print values
				self.c.execute("insert into `positions` (az, el, start, end, count) VALUES(?,?,?,?,?)", values)
				startlt = lt
				count = 0
			
			count += x['count']
			
			lastel = el
			lastaz = az
			lastlt = lt
	'''
	
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
				if e['count'] < 200 and e['az'] != 361 and e['el'] != 361: #small fragment that is not a slewing frame
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
		return self #allows for chaining

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
		return self #allows for chaining

	#Data cleanup algorithms
	def imgRegular(self, dtfl, options):
		return np.clip(dtfl,options['mean']-options['std']*options['thresh'],options['mean']+options['std']*options['thresh'])

	def imgNostar(self, dtfl, options):
		return medianfilt2(dtfl, 9)
	
	def imgSpikeless(self, dtfl, options):
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

	def imgHisto(self, dtfl, options):
		'''
		fig = plt.figure()
		ax = fig.add_subplot(111)
		(n, bins) = np.histogram(dtfl, bins=100)
		#ax.plot(.5*(bins[1:]+bins[:-1]), n)
		plt.show()
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


	# this takes data (from sql) in sqlDict() form: [{'a':1, 'b':2}, {'a':3,'b':4}, ...]
	# entry is expected to contain "file", and "ix"
	# write images (normal, and nostar) to file
	# options = dict('mean':None, 'std':None, 'thresh':5, 'az':None, 'el':None, 'dir':None)
	#  if these values are not set, it will use appropriate defaults...
	def writeimage(self, entry, imgtype, resultsdir = None, options = {}):
		#dostarremoval = Truev =
		#image types:
		#regular
		#nostar
		#collage
		imgtype = imgtype.lower() #enforce lower case
		valid = {"regular":self.imgRegular, "nostar":self.imgNostar}
		if not imgtype in valid:
			raise RuntimeError('writeimage: Invalid image type. Valid entries:', keys(valid))
		if type(entry) == list:#if given the whole list, just do all of them recursively
			if len(entry):
				if len(entry) > 1:
					self.writeimage(entry[1:], imgtype, options)
				entry = entry[0]
			else:
				raise RuntimeError('writeimage: Entry variable is invalid.')

		if not 'az' in options and not 'el' in options:
			if 'az' in entry and 'el' in entry:
				options['az'] = entry['az']
				options['el'] = entry['el']
			else:
				raise RuntimeError('writeimage: No azel supplied for image.')
		if not 'thresh' in options:
			options['thresh'] = 5

		if not 'dir' in options:
			imagesdir = op.join(self.rootdir, 'images')
		else:
			imagesdir = options['dir']
		if not op.isdir(imagesdir):
		  os.makedirs(imagesdir)
		usedir = op.join(imagesdir, imgtype)
		if not op.isdir(usedir):
		  os.makedirs(usedir)

		#open the file
		uadata = ud.UAVData(op.join(self.rootdir, entry['file']))
		fm = uadata.frame(entry['ix'])
		#make it into a numpy array
		dtfl = np.array(fm['Data'], dtype='float32')
		irradpcount = 0.105 # nW / cm2 / um  per  count
		dtfl *= irradpcount
		dtfl.shape = (fm['FrameSizeY'], fm['FrameSizeX'])


		if not 'mean' in options or not 'std' in options: #if some scale factor isnt supplied, use whatever works for this image
			options['mean'] = dtfl.mean()
			options['std'] =  dtfl.std()
		else:
			options['mean'] *= irradpcount
			options['std'] *= irradpcount

		'''
		print "--", entry['idx'], "--"
		print 'rgmin:', regular.min()
		print 'rgmax:', regular.max()
		print 'rgmean:', regular.mean()
		print 'rgstdev:', regular.std()
		'''

		use = valid[imgtype](dtfl, options) #apply the appropriate filter

		if 'graph' in options:
			fig = plt.figure()
			ax = fig.add_subplot(111)
			
	
			ax.plot(use)
			ax.plot([use.mean()+use.std()]*len(use), linewidth=2, color="b")
			ax.plot([use.mean()-use.std()]*len(use), linewidth=2, color="b")
		
			ax.plot([use.mean()+use.std()*options['thresh']]*len(use), linewidth=2, color="r")
			ax.plot([use.mean()-use.std()*options['thresh']]*len(use), linewidth=2, color="r")		
	
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

		#stretch values across 0-255
		#tmin = use.min()
		#tmax = use.max()
		tmin = options['mean']-options['std']*options['thresh']
		tmax = options['mean']+options['std']*options['thresh']
		use = use - tmin
		dvsor = (tmax - tmin)
		use = (use / dvsor) * 255

		im = Image.fromarray(np.array(use, dtype='uint8'))
		flname = imgtype+'-'+time.strftime("%Y%m%d-%H%M%S", time.localtime(fm['LTime']))+'-'+str(fm['MSTime'])+'.png'
		im.save(op.join(usedir, flname))
		return self #allows for chaining

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
		return self #allows for chaining

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
