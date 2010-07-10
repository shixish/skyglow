######################################
#Code written by: Andrew Wessels 2010#
#------------------------------------#
#This code is used to produce
# and manipulate a sqlite database
# for working with skyglow

'''
#Useful for getting set up in terminal:
import skyglowdb
reload(skyglowdb); db = skyglowdb.DB("/home/drew/prj/data/", True)
reload(skyglowdb); bdb = skyglowdb.DB("/media/lavag", True)

A test of the slewing frame cleanup, and command chaining:
db.restore().fixPositions(graph=1).graphPositions()
This will restore the db using the backup, fix the data, and show two graphs...
'''

#self.c.execute("create table `frames` (LTime SMALLINT,MSTime SMALLINT,FrameCounter SMALLINT,DroppedFrames SMALLINT,FrameSizeX SMALLINT,FrameSizeY SMALLINT,TargetRange SMALLINT,Altitude SMALLINT,FocusStepOffset SMALLINT,BytesPerPixel SMALLINT,OffsetToImageData SMALLINT,CameraUsed SMALLINT,FilterWheelPosition SMALLINT,FocusMotorIndex SMALLINT,IntegrationTimeNS SMALLINT,TargetDeltaRange SMALLINT,TargetAzimuth INT,TargetElevation INT,TargetLatitude INT,TargetLongitutde INT,TargetAltitude INT,AircraftLatitude INT,AircraftLongitude INT,AircraftAltitude INT)")
#["LTime","MSTime","FrameCounter","DroppedFrames","FrameSizeX","FrameSizeY","TargetRange","Altitude","FocusStepOffset","BytesPerPixel","OffsetToImageData","CameraUsed","FilterWheelPosition","FocusMotorIndex","IntegrationTimeNS","TargetDeltaRange","TargetAzimuth","TargetElevation","TargetLatitude","TargetLongitutde","TargetAltitude","AircraftLatitude","AircraftLongitude","AircraftAltitude"]
#self.c.execute("insert into `frames` VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [round(d[x],1) for x in names])


import time, sys
from datetime import datetime as dt
#i made this one to help with manipulating the time info
import dbtime
import os
import os.path as op
import uavdata as ud
import sqlite3

import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import shutil

#used for vids
import glob
import subprocess

#used for images
from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageEnhance

import fnmatch, os

class q:
	def __init__(self, ok):
		print ok

class DB:
	def __init__(self, rootdir=None, debug=False):
		if rootdir == None:
			rootdir = os.path.abspath(os.curdir)
		self.rootdir = rootdir
		self.conn = sqlite3.connect(op.join(self.rootdir, 'sql'))
		self.c = self.conn.cursor()
		self.debug = debug

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
		return self

	def restore(self):
		print "Are you sure you want to overwrite the current database with the backup?"
		answer = raw_input()
		if len(answer) > 0 and answer[0].lower() == "y" or answer == "1":
			shutil.copy(op.join(self.rootdir, 'sql.bak'), op.join(self.rootdir, 'sql'))
			print "Done."
		else:
			print "Unchanged."
		return self

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

	def sqlDataString(self, data, prefix = ""):
		ret = ''
		first = True
		for i in data:
			if first:
				first = False
			else:
				ret+=','
			if prefix != "" and prefix[-1] != ".":
				prefix += "."
			ret += prefix+str(i)+"="+str(data[i])
		return ret	#this stuff isn't of any use atm, might be in the future...
	
	def findFiles(self):
		self.imgfiles = []
		self.imgfiles[:] = self.locate('*.img', self.rootdir)
		self.imgfiles.sort()
		print (self.imgfiles)

	def getFrames(self, frm, to):
		return self.query("select * from `frames` where lt>=? and lt<=? order by lt", (frm, to))

	#This is a powerful accessor function that allows you to pull out specific data.
	#General Notes:
	#		Both "one" and "two" (if used) need to be valid table names.
	#		"where" can be an SQL string or a dictionary which may contain multiple conditions.
	#		if "where" is an SQL string, variables should be prefixed with the second table's name if using two tables:
	#			ex: "passes.rowid = 2 and passes.start = ..."
	#		"limit" can be specified to limit the number of results
	#Examples:
	#	"get frames in pass number 2"
	#		translates to: db.get("frames", "passes", {"rowid":2})
	#	"get positions in the night where start = 1268118808"
	#		translates to: db.get("positions", "nights", {"start":1268118808})
	#Reversed direction
	#	"get the passes that include position 3" (only one will exsist)
	#		translates to: db.get("passes", "positions", {"rowid":3})
	#Single table selection
	#	"get positions where rowid = 1"
	#		translates to: db.get("positions", where={"rowid":3})
	#					  or:	db.get("positions", "", {"rowid":3})
	#					  or:	db.get("positions", "positions", {"rowid":3})
	#More Advanced Queries
	#	"get positions that start after 1268118808"
	#		db.get("positions", where="positions.start >= 1268118808")
	#	"get positions that start before March 12th 2010"
	#		maketime = str(dbtime.dbtime({"year":2010,"mon":3,"day":12}))
	#		db.get("positions", where="start <= "+maketime)
	#		Note: Read the documentation on dbtime for more variation here...
	#				Also, notice "positions." can be omitted from "positions.start"
	#					since the query deals with only one table.
	def get(self, one, two = "", where={}, limit=""):
		single = ("lt", "lt")
		double = ("start", "end")
		vals = {"frames":single, "positions":double, "passes":double, "nights":double}
		#unfortunately vals.keys() wont work, because it doesn't retain its order.
		chain = ["frames", "positions", "passes", "nights"]
		if two == "":
			two = one
		if type(where) == dict:
			where = where.copy() #it passes by reference, and im destroying values...
			wherestr = ""
			if where.has_key('slewing'):
				if where['slewing']:
					wherestr += two+".az = 361 and "+two+".el = 361 and "
				else:
					wherestr += two+".az != 361 and "+two+".el != 361 and "
				del where['slewing']
			
			if where.get('rep', 0):
				middle = "ROUND(("+two+"."+vals[two][0]+"+"+two+"."+vals[two][1]+")/2, 0)"
				wherestr += one+"."+vals[one][0]+" <= "+middle+" and "+one+"."+vals[one][1]+" >= "+middle + " and "			
			else:
				try:
					oix = chain.index(one)
					tix = chain.index(two)
				except ValueError:
					raise RuntimeError("get: Table does not exsist.")
				small = one
				big = two
				if oix > tix:
					big = one
					small = two
				wherestr += small+"."+vals[small][0]+" >= "+big+"."+vals[big][0]+" and "+small+"."+vals[small][1]+" <= "+big+"."+vals[big][1]+" and "
			if where.has_key('rep'):
				del where['rep']
			if where.has_key('between'):
				if (type(where['between']) == tuple or type(where['between']) == list):
					wherestr += two+"."+vals[two][0]+" >= "+str(where['between'][0])+" and "+two+"."+vals[two][1]+" <= "+str(where['between'][1])+" and "
				del where['between']
			wherestr += self.sqlDataString(where, two)
		else:
			wherestr = where
		if limit != "":
			limit = " limit " + str(limit)
		query = "select "+one+".* from "+one
		if one != two:
			query += ","+two
			if wherestr == "":
				raise RuntimeError("Get: Cant process two tables with no condition.")
		if wherestr[-5:] == " and ":
			wherestr = wherestr[:-5]
		if wherestr != "":
			query += " where "+wherestr
		query += limit
		print query
		#old = 'select frames.* from frames, positions where frames.lt <= ROUND((positions.start+positions.end)/2, 0) and frames.lt >= ROUND((positions.start+positions.end)/2, 0) and positions.el != 361 and positions.az != 361 and positions.start >= 15 and positions.end <= 20"'
		#print old, query==old
		return self.query(query)

	def getFrameInfo(self, lt):
		return self.query("select frames.*,positions.rowid as position,passes.rowid as pass,nights.rowid as night from frames,positions,passes,nights where frames.lt=? and (lt between positions.start and positions.end) and (lt between passes.start and passes.end) and (lt between nights.start and nights.end)", (lt,))

	def getAvgStats(self, start, end, table = "frames"):
		if table == "frames":
			return self.query("select sum(mean)/count(lt) as mean, sum(std)/count(lt) as std, sum(min)/count(lt) as min, sum(max)/count(lt) as max from "+table+" where lt>=? and lt<=?", (start,end))[0]
		elif table == "positions" or table == "passes" or table == "nights":
			return self.query("select sum(mean)/count(start) as mean, sum(std)/count(start) as std, sum(min)/count(start) as min, sum(max)/count(start) as max from "+table+" where start>=? and end<=?", (start,end))[0]
		else:
			raise RuntimeError("getAvgStats: Cannot accept table: " + str(table))

	def query(self, query, var = []):
		if len(var) > 0:	
			self.c.execute(query, var)
		else:
			self.c.execute(query)
		ret = self.sqlDict()
		# Save (commit) the changes
		self.conn.commit()
		return ret


	###################################
	# buildDB                         #
	#---------------------------------#
	# This builds the database..      #
	#  It begins the complete process #
	#  of indexing a drive            #
	###################################
	def build(self, rebuild = False, fix = True):
		self.findFiles()
		self.doFrames(rebuild)
		self.doPositions(rebuild)
		if fix:
			self.redoPositions()
		self.doPasses(rebuild)
		self.doNights(rebuild)
		self.doStats()
		print 'Hard drive indexing complete!'
		return self #allows for chaining

	def doFrames(self, rebuild = False):
		print "Building frames data"
		if rebuild:
			self.c.execute("drop table frames")
		self.c.execute("create table `frames` (lt SMALLINT, ms SMALLINT, az SMALLINT, el SMALLINT, file TEXT, ix INT, mean FLOAT, std FLOAT, min SMALLINT, max SMALLINT)")
		lastlt = 0
		irradpcount = 0.105 # nW / cm2 / um  per  count
		for img in self.imgfiles:
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

				#this should take a frame every second
				if lastlt != lt:
					dtfl = np.array(d['Data'], dtype='float32')
					tmean = dtfl.mean()*irradpcount
					tstd = dtfl.std()*irradpcount
					tmin = int(dtfl.min()*irradpcount)
					tmax = int(dtfl.max()*irradpcount)
					values = [lt, ms, az, el, os.path.relpath(img, start=self.rootdir), x, tmean, tstd, tmin, tmax]
					#print values
					self.c.execute("insert into `frames` (lt,ms,az,el,file,ix,mean,std,min,max) VALUES(?,?,?,?,?,?,?,?,?,?)", values)

				lastlt = lt
			print (time.time() - then), " seconds"
			sys.stdout.flush()
		# Save (commit) the changes
		self.conn.commit()
		return self #allows for chaining


	def doPositions(self, rebuild = False):
		print "Detecting positions data"
		start = time.time()
		if rebuild:
			self.c.execute("drop table positions")
		self.c.execute("create table `positions` (az SMALLINT, el SMALLINT, start INT, end INT, count SMALLINT, mean FLOAT, std FLOAT, min FLOAT, max FLOAT)")
		frames = self.query("SELECT * from frames order by lt")
		lastel = 0
		lastaz = 0
		lastlt = 0
		startlt = 0
		first = True
		#tallymean = 0
		#tallystd = 0
		#tallymin = 0
		#tallymax = 0
		count = 0
		for x in frames:
			count += 1
			az = x['az']
			el = x['el']
			lt = x['lt']
			if first:
				lastel = el
				lastaz = az
				lastlt = lt
				startlt = lt
				first = False
			if x['mean'] < 25: #static frames
				az = 361
				el = 361
			#this doesnt work because there are errors in the data, so i'll fix the data later
			if az != lastaz or el != lastel: #new position detection
				values = [lastaz, lastel, startlt, lastlt, count]
				self.c.execute("insert into `positions` (az, el, start, end, count) VALUES(?,?,?,?,?)", values)
				startlt = lt
				count = 0
			lastel = el
			lastaz = az
			lastlt = lt
		#catch the last values
		values = [lastaz, lastel, startlt, lastlt, count]
		self.c.execute("insert into `positions` (az, el, start, end, count) VALUES(?,?,?,?,?)", values)
		# Save (commit) the changes
		self.conn.commit()
		print "Done! (", (time.time() - start), "seconds )"
		return self

	#passes will exclude some slewing frames, since slewing frames in between passes cannot be easilly accounted for.
	def doPasses(self, rebuild = False):
		print "Detecting passes data"
		start = time.time()
		if rebuild:	
			self.c.execute("drop table passes")
		self.c.execute("create table `passes` (start INT UNIQUE, end INT UNIQUE, mean FLOAT, std FLOAT, min FLOAT, max FLOAT)")

		#start running some stats
		data = self.query("select rowid,* from `positions` where az!=361 and el!=361")
		firstdata = data[0]
		counts = []
		lastdata = data[0]
		#passdata = []
		for i, e in enumerate(data):
			counts.append(e['el'])
			if e['el'] > lastdata['el']: #new pass
				print "pass from: ", firstdata['start'], "to", lastdata['end']
				self.c.execute("insert into `passes` (start, end) values (?,?)", (firstdata['start'], lastdata['end']))
				firstdata = e
			lastdata = e
		self.c.execute("insert into `passes` (start, end) values (?,?)", (firstdata['start'], lastdata['end']))
		print "last pass from: ", firstdata['start'], "to", lastdata['end']
		if self.debug:
			fig = plt.figure()
			ax = fig.add_subplot(111)
			ax.plot(counts)
			plt.show()
		# Save (commit) the changes
		self.conn.commit()
		print "Done! (", (time.time() - start), "seconds )"
		return self

	def doNights(self, rebuild = False):
		print "Detecting nights data"
		start = time.time()
		if rebuild:	
			self.c.execute("drop table nights")
		self.c.execute("create table `nights` (start INT UNIQUE, end INT UNIQUE, mean FLOAT, std FLOAT, min FLOAT, max FLOAT)")
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
		# Save (commit) the changes
		self.conn.commit()
		print "Done! (", (time.time() - start), "seconds )"
		return self
			
	def doStats(self):
		print "Completing statistics"
		chain = ["frames", "positions", "passes", "nights"]
		for c in range(1,len(chain)):
			for x in self.query("select * from "+chain[c]):
				stats = self.getAvgStats(x['start'], x['end'], chain[c-1])
				self.query("update `"+chain[c]+"` set "+self.sqlDataString(stats))
	
	#This function is intended to be used to merge positions
	#data = list of dictionary data from db
	#i = index of thing to merge
	#perm = to make the changes permanent (change the database)
	#direction = 
	#	{
	#		 0 : merge both sides
	#		+1 : merge right
	#		-1 : merge left
	#	}
	def merge(self, data, i, direction, perm = True):
		use = 0
		if direction == 0: #do both sides
			use = i+1
		else:
			use = i+(abs(direction)/direction) #i+1 or i-1
		data[i]['az'] = data[use]['az']
		data[i]['el'] = data[use]['el']
		if (direction <= 0):
			data[i]['start'] = data[i-1]['start']
			data[i]['count'] += data[i-1]['count']
		if (direction >= 0):
			data[i]['end'] = data[i+1]['end']
			data[i]['count'] += data[i+1]['count']
		if direction == 0:
			if perm:
				self.c.execute("delete from `positions` where rowid=? or rowid=?",(data[i-1]['rowid'],data[i+1]['rowid']))
			del data[i+1], data[i-1]
		else:
			if perm:
				self.c.execute("delete from `positions` where rowid=?",(data[use]['rowid'],))
			del data[use]
		return data


	def redoPositions(self, perm = True):
		print "Cleaning up positions data"
		start = time.time()
		self.c.execute("select rowid,az,el,count,start,end from `positions` ")
		data = self.sqlDict()
		graph = self.debug
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
				if e['count'] < 3 and e['az'] != 361 and e['el'] != 361: #small fragment that is not a slewing frame
					# i want the first few passes to just fill up the blanks in the slewing frames
					if passnum < 2:
						if pe['az'] == ne['az'] and pe['el'] == ne['el'] and pe['az'] == 361 and pe['el'] == 361:
							data = self.merge(data, i, 0, perm)
					else:
						if pe['az'] == ne['az'] and pe['el'] == ne['el']: #azel on either side are equivalent
							data = self.merge(data, i, 0, perm)
						elif e['az'] == ne['az'] and e['el'] == ne['el']: #same azel as right side
							data = self.merge(data, i, 1, perm)
						elif e['az'] == pe['az'] and e['el'] == pe['el']: #same azel as left side
							data = self.merge(data, i, -1, perm)
						elif ne['az'] == 361 and ne['el'] == 361: #next position is a slewing frame
							data = self.merge(data, i, 1, perm)
						elif pe['az'] == 361 and pe['el'] == 361: #prev position is a slewing frame
							data = self.merge(data, i, -1, perm)
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
		print "Done! (", (time.time() - start), "seconds )"
		return self

	#this will create a bar graph representing the positions data.
	#this may be useful when looking for errors.
	def graphPositions(self):
		fig = plt.figure()
		ax = fig.add_subplot(111)
		#this gathers data for the graph
		data = self.query("select rowid,* from `positions` where az != 361 and el != 361")
		x = 0
		for e in data:
			y = e['az']+e['el']
			ax.bar(x, y, e['count'])
			x += e['count']
		#draw the graph
		plt.show()
		return self #allows for chaining

	#Various data cleanup algorithms used by writeimage()
	def imgRegular(self, dtfl, opt):
		return np.clip(dtfl,opt['mean']-opt['std']*opt['thresh'],opt['mean']+opt['std']*opt['thresh'])

	def imgNostar(self, dtfl, opt):
		return medianfilt2(dtfl, 9)
	
	#this one gets rid of the spikes...
	#this one left a few artifacts from the removal, so i dont think its an ideal solution...
	def imgSpikeless(self, dtfl, opt):
		'''
		spikeless = dtfl
		factor = 3
		for c,y in enumerate(spikeless):
			for i,e in enumerate(y):
				if e > tmean+tstd*factor or e < tmean-tstd*factor:
					spikeless[c][i] = tmean
				
					#print i, e
		'''

	#this is my attempt at using the histogram data to clear up inconsistencies...
	def imgHisto(self, dtfl, opt):
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

	#Purpose: pull image data from IMG files, write out images as png after applying a filter.
	# entry = img data from sql
	#  - may be in sqlDict() form: [{'file':"file/loc.img", 'ix':123}, {'file':"file/loc.img", 'ix':321}, ...]
	#  - or it may be a dictionary in the form: {'file':"file/loc", 'ix':123}
	#  - "file", and "ix" are required fields
	#  - if this is a list of many entries (dictionaries), it will do each entry recursively.
	# imgtype defines which filter to use
	#  - can be either "regular" or "nostar" (possibly more to come)
	# opt = dict('mean':None, 'std':None, 'thresh':5, 'dir':None)
	#  - mean, std, thresh are used for scaling, these will be determined on a frame by frame basis if left blank.
	#  - dir is the directory where the images should go. Default is '...rootdir/images'
	def writeImg(self, entry, imgtype = "regular", opt = {}):
		if type(entry) == list: #if we have a list of entries, just do them all recursively...
				if len(entry):
					if len(entry) > 1:
						self.writeImg(entry[1:], imgtype, opt)
					entry = entry[0]
				else:
					raise RuntimeError('writeImg: Invalid list of entries.')
		imgdata = {}
		opt = opt.copy()
		
		if type(entry) == dict:#if just given one entry put it in a list...
			if entry.has_key("img"):
				imgdata = entry
			elif entry.has_key("file"):
				imgdata = self.getImg(entry, imgtype, opt)
			else:
				raise RuntimeError('writeImg: Invalid entry(dict) field.')
			opt['lt'] = opt.get("lt", entry.get("lt", None))
			opt['ms'] = opt.get("ms", entry.get("ms", None))
		elif isinstance(entry,Image.Image):
			imgdata['img'] = entry
			opt['lt'] = opt.get("lt", None)
			opt['ms'] = opt.get("ms", None)		
		else:
			raise RuntimeError("writeImg: Invalid entry field.")	
		
		if opt['lt'] and not opt.has_key('name'):
			opt['name'] = imgtype+'-'+time.strftime("%Y%m%d-%H%M%S", time.localtime(imgdata['lt']))
			if opt['ms']:
				opt['name'] += '-'+str(imgdata['ms'])

		opt['name'] = opt.get('name', "default")
		opt['name'] += ".png"
		if opt['lt']:
			night = time.strftime("%Y%m%d", time.localtime(opt['lt']))
		else:
			night = "unknown"
		
		datadir = opt.get("dir", op.join(self.rootdir, "dataproducts"))
		nightdir = op.join(datadir, night)
		imgdir = op.join(nightdir, 'images')
		usedir = op.join(imgdir, imgtype)
		if not op.isdir(usedir):
		  os.makedirs(usedir)

		imgdata['img'].save(op.join(usedir, opt['name']))
		return self #allows for chaining
	
	def writeCollage(self):
		passes = self.query("select rowid,* from passes")
		#pas = self.getFrames(passes[0]['start'], passes[0]['end'])
		#pas = self.getFrames(passes[0]['start'], passes[0]['start']+5)
		#this will simply grab a representative frame of each available position
		#cheap hack for now
		dimentions = (2940,2940)
		bigim = Image.new('RGB', dimentions)
		origin = (dimentions[0]/2, dimentions[0]/2) #middle of the image
		usepass = 0;
		#pas = self.query("select frames.* from frames, positions where frames.lt <= ROUND((positions.start+positions.end)/2, 0) and frames.lt >= ROUND((positions.start+positions.end)/2, 0) and positions.el != 361 and positions.az != 361 and positions.start >= ? and positions.end <= ?", (passes[usepass]['start'], passes[usepass]['end']))
		conditions = {'slewing':False, 'rep':True, 'between':(passes[usepass]['start'], passes[usepass]['end'])}		
		pas = self.get("frames", "positions", where=conditions)
		
		for n in range(len(pas)):#pas:
			p = pas[n]
			#print p
			imgdata = self.getImg(p)
	
			#print('convert im to RGB')
			#sys.stdout.flush()
	
			imcl = imgdata['img'].convert('RGBA')
			#f = ImageFont.load_default()

			irradpcount = 0.105 # nW / cm2 / um  per  count
			d = ImageDraw.Draw(imcl)
			d.text( (0, 0), u'{0} ({1}, {2})'.format(round(p['mean']*irradpcount, 2), round(p['az'], 1), round(p['el'], 1)), fill='#00ff00')
			#imcl.show()
	
			#rotation = 0
			#if p['el'] != 90:
				#rotation = -(p['az']-90)
			rotation = -(p['az']-90)
			imcl = imcl.rotate(rotation, expand = 1)
			#imcl.show()
			w,h = imcl.size
			#distance from the origin is related to the elevation
			distance = (90-p['el'])*22
			#print p['el'], p['az'], distance
			#imcl.show()
			#this code will get the distance from the origin...
			# the "- x/2" part is adjusting for the center of imcl,
			nx = origin[0] + math.cos(p['az']*math.pi/180)*distance - w/2
			ny = origin[1] + math.sin(p['az']*math.pi/180)*distance - h/2
			bigim.paste(imcl, (nx,ny), imcl)
		
			'''
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
			'''
		#bigim.show()
		self.writeImg(bigim, opt={"name":"collage"})
		'''
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
		'''

	def doImg(self):
		entry = self.query("select * from frames limit 158,5 ")
		for e in entry:
			img = self.getImg(e)
			self.writeImg(img)

 
	def getImg(self, entry, imgtype = "regular", opt={}):
		valid = {"regular":self.imgRegular, "nostar":self.imgNostar}
		if not imgtype.lower() in valid:
			raise RuntimeError('writeimage: Invalid image type. Valid entries:', keys(valid))

		opt['thresh'] = opt.get('thresh', 5)
		#open the file
		uadata = ud.UAVData(op.join(self.rootdir, entry['file']))
		fm = uadata.frame(entry['ix'])
		#make it into a numpy array
		dtfl = np.array(fm['Data'], dtype='float32')
		irradpcount = 0.105 # nW / cm2 / um  per  count
		dtfl *= irradpcount
		dtfl.shape = (fm['FrameSizeY'], fm['FrameSizeX'])

		if not opt.has_key('mean') in opt or not opt.has_key('std'): #if some scale factor isnt supplied, use whatever works for this image
			#this should be the same as entry['mean'], entry['std']...
			opt['mean'] = dtfl.mean()
			opt['std'] =  dtfl.std()

		use = valid[imgtype](dtfl, opt) #apply the appropriate filter
		#use = np.clip(dtfl,opt['mean']-opt['std']*opt['thresh'],opt['mean']+opt['std']*opt['thresh'])

		if opt.has_key('graph'):
			fig = plt.figure()
			ax = fig.add_subplot(111)
		
			ax.plot(use)
			ax.plot([use.mean()+use.std()]*len(use), linewidth=2, color="b")
			ax.plot([use.mean()-use.std()]*len(use), linewidth=2, color="b")
	
			ax.plot([use.mean()+use.std()*opt['thresh']]*len(use), linewidth=2, color="r")
			ax.plot([use.mean()-use.std()*opt['thresh']]*len(use), linewidth=2, color="r")
			

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
		tmin = opt['mean']-opt['std']*opt['thresh']
		tmax = opt['mean']+opt['std']*opt['thresh']
		use = use - tmin
		dvsor = (tmax - tmin)
		use = (use / dvsor) * 255
		entry['img'] = Image.fromarray(np.array(use, dtype='uint8'))
		#ret = {"lt":fm['LTime'], "ms":fm['MSTime'], "img":im}
		#im.show()
		return entry

	def makeVid(self, imgdir, viddir = ''):
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

#i'm leaving these out of the class because they don't really need to make use of any member variables,
#so i figured they don't need to exsist in every instance of the DB class...

#used for creating the "nostar" images in the writeimage() function
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

#used for creating the "nostar" images in the writeimage() function
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
