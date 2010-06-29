import datetime, time, sys
import os.path as op
import uavdata as ud
import sqlite3

import testfunc as tf
import matplotlib.pyplot as plt

import fnmatch, os
def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


#######################
#GET COMMAND-LINE ARGS#
#######################
from optparse import OptionParser
parser = OptionParser()
parser.add_option("--dir", help="STRING: Directory in which to find the img files.")
parser.add_option("--clean", action="store_true", help="BOOL: Run error correction to clean the results.")
parser.add_option("--rebuild", action="store_true", help="BOOL: set this if the database is already made, but you want to remake it.")
parser.add_option("--graph", action="store_true", help="BOOL: Shows a graph of the data.")
(options, args) = parser.parse_args()

rootdir = os.path.abspath(os.curdir)
if options.dir:
	print options.dir
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

#------------------#
#Refresh the tables#
#------------------#
if options.rebuild:
	c.execute("drop table positions")
c.execute("create table `positions` (az SMALLINT, el SMALLINT, start DOUBLE UNIQUE, end DOUBLE UNIQUE, count SMALLINT)")

if options.rebuild:
	c.execute("drop table frames")
c.execute("create table `frames` (ltms DOUBLE UNIQUE, az SMALLINT, el SMALLINT, file TEXT, ix INT)")
#c.execute("create table `frames` (LTime SMALLINT,MSTime SMALLINT,FrameCounter SMALLINT,DroppedFrames SMALLINT,FrameSizeX SMALLINT,FrameSizeY SMALLINT,TargetRange SMALLINT,Altitude SMALLINT,FocusStepOffset SMALLINT,BytesPerPixel SMALLINT,OffsetToImageData SMALLINT,CameraUsed SMALLINT,FilterWheelPosition SMALLINT,FocusMotorIndex SMALLINT,IntegrationTimeNS SMALLINT,TargetDeltaRange SMALLINT,TargetAzimuth INT,TargetElevation INT,TargetLatitude INT,TargetLongitutde INT,TargetAltitude INT,AircraftLatitude INT,AircraftLongitude INT,AircraftAltitude INT)")


imgfiles = []
imgfiles[:] = locate('*.img', rootdir)
imgfiles.sort()
print (imgfiles)


positions = dict()
lastel = 0
lastaz = 0
lastltms = 0
passid = 0
posStart = 0
passStart = 0
count=0
#d['time'] = time.localtime(md['LTime'])
first = True
for img in imgfiles:
	uadata = ud.UAVData(img)
	print "Data Entries: ", len(uadata)
	#positions = dict()
	then = time.time()
	for x in range(len(uadata)):
		d = uadata.framemeta(x)
		az = round(d['TargetAzimuth'], 1)
		el = round(d['TargetElevation'], 1)
		ltms = d['LTime']*1000+d['MSTime']
		if first:
			first = False
			lastaz = az
			lastel = el
			posStart = ltms
			passStart = ltms
		
		#this doesnt work because there are errors in the data 
		# this gets fixed later on
		if (az != lastaz or el != lastel):
			#print "new position detected"
			#c.execute("select * from `positions` where `start`='?' and `end`='?'", posStart, lastlt)
			values = [lastaz, lastel, posStart, lastltms, count]
			#print values
			#if count < 120:
				#print "Suspicious!"
			c.execute("insert into `positions` (az, el, start, end, count) VALUES(?,?,?,?,?)",values)
			posStart = ltms
			count = 0
		else:
			count += 1
		
		#if az == 361 and el == 361:
			#print "slewing frame"

		#if el - lastel > 0:
		#	print "+1", passid
		#	passid += 1

		#this should take a frame every second
		#if lastlt != lt:	

		values = [ltms, az, el, img, x]
		c.execute("insert or ignore into `frames` (ltms,az,el,file,ix) VALUES(?,?,?,?,?)", values)

#["LTime","MSTime","FrameCounter","DroppedFrames","FrameSizeX","FrameSizeY","TargetRange","Altitude","FocusStepOffset","BytesPerPixel","OffsetToImageData","CameraUsed","FilterWheelPosition","FocusMotorIndex","IntegrationTimeNS","TargetDeltaRange","TargetAzimuth","TargetElevation","TargetLatitude","TargetLongitutde","TargetAltitude","AircraftLatitude","AircraftLongitude","AircraftAltitude"]
		#c.execute("insert into `frames` VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [round(d[x],1) for x in names])

		lastel = el
		lastaz = az
		lastltms = ltms
	now = time.time()
	bench = (now - then)
	print bench, " seconds"


##############
#DATA CLEANUP#
##############
#TODO::
#	this needs work, i made it so it will do one sided swaps, not just double sided.
#	i need to work through this logic again...

if options.clean:
	print "Cleaning up the data"

	c.execute("select rowid,* from `positions` ")
	data = tf.sqlDict(c)

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
			if e['count'] < 100:
				# i want the first pass to just fill up the blanks in the slewing frames
				if passnum < 2:
					if pe['az'] == ne['az'] and pe['el'] == ne['el'] and pe['az'] == 361 and pe['el'] == 361:
						e['count'] += pe['count'] + ne['count']
						e['start'] = pe['start']
						e['end'] = ne['end']
						e['az'] = ne['az']
						e['el'] = ne['el']					
						c.execute("delete from `positions` where rowid=? or rowid=?",(pe['rowid'],ne['rowid']))
						del data[next], data[prev]
				else:
					if pe['az'] == ne['az'] and pe['el'] == ne['el']:
						e['count'] += pe['count'] + ne['count']
						e['start'] = pe['start']
						e['end'] = ne['end']
						e['az'] = ne['az']
						e['el'] = ne['el']					
						c.execute("delete from `positions` where rowid=? or rowid=?",(pe['rowid'],ne['rowid']))
						del data[next], data[prev]
					elif e['az'] == ne['az'] and e['el'] == ne['el']:
						e['az'] = ne['az']
						e['el'] = ne['el']
						e['end'] = ne['end']
						e['count'] += ne['count']
						c.execute("delete from `positions` where rowid=?",(ne['rowid'],))
						del data[next]
					elif e['az'] == pe['az'] and e['el'] == pe['el']:
						e['az'] = pe['az']
						e['el'] = pe['el']
						e['count'] += pe['count']
						e['start'] = pe['start']
						c.execute("delete from `positions` where rowid=?",(pe['rowid'],))
						del data[prev]
					elif ne['az'] == 361 and ne['el'] == 361:
						e['az'] = ne['az']
						e['el'] = ne['el']
						e['end'] = ne['end']
						e['count'] += ne['count']
						c.execute("delete from `positions` where rowid=?",(ne['rowid'],))
						del data[next]
					elif pe['az'] == 361 and pe['el'] == 361:
						e['az'] = pe['az']
						e['el'] = pe['el']
						e['count'] += pe['count']
						e['start'] = pe['start']
						c.execute("delete from `positions` where rowid=?",(pe['rowid'],))
						del data[prev]
					else:
						e['az'] = 361
						e['el'] = 361
				c.execute("update `positions` set "+tf.sqlDataString(e)+" where rowid=?", (e['rowid'],))
					
			
			'''
			#this doesnt work for some reason
			if e['az'] == ne['az'] and e['el'] == ne['el'] and i != next:
				e['count'] += ne['count']
				e['end'] = ne['end']
				c.execute("delete from `positions` where rowid=?",(ne['rowid'],))
				del data[next]
				c.execute("update `positions` set "+tf.sqlDataString(e)+" where rowid=?", (e['rowid'],))
			elif e['az'] == pe['az'] and e['el'] == pe['el'] and i != prev:
				e['count'] += pe['count']
				e['start'] = pe['start']
				c.execute("delete from `positions` where rowid=?",(pe['rowid'],))
				del data[prev]
				c.execute("update `positions` set "+tf.sqlDataString(e)+" where rowid=?", (e['rowid'],))
			'''
	if options.graph:	
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

	#_END OF DATA CLEANUP_#



if options.graph:
	#this gathers data for the graph
	c.execute("select rowid,* from `positions` where az != 361 ")
	data = tf.sqlDict(c)
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


# Save (commit) the changes
conn.commit()

# We can also close the cursor if we are done with it
c.close()
conn.close()
