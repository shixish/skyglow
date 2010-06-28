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
c.execute("create table `positions` (az SMALLINT, el SMALLINT, start DOUBLE, end DOUBLE, count SMALLINT)")

if options.rebuild:
	c.execute("drop table frames")
c.execute("create table `frames` (ltms DOUBLE, az SMALLINT, el SMALLINT, file TEXT, ix INT)")
#c.execute("create table `frames` (LTime SMALLINT,MSTime SMALLINT,FrameCounter SMALLINT,DroppedFrames SMALLINT,FrameSizeX SMALLINT,FrameSizeY SMALLINT,TargetRange SMALLINT,Altitude SMALLINT,FocusStepOffset SMALLINT,BytesPerPixel SMALLINT,OffsetToImageData SMALLINT,CameraUsed SMALLINT,FilterWheelPosition SMALLINT,FocusMotorIndex SMALLINT,IntegrationTimeNS SMALLINT,TargetDeltaRange SMALLINT,TargetAzimuth INT,TargetElevation INT,TargetLatitude INT,TargetLongitutde INT,TargetAltitude INT,AircraftLatitude INT,AircraftLongitude INT,AircraftAltitude INT)")


imgfiles = []
imgfiles[:] = locate('*.img', rootdir)
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
		c.execute("insert into `frames` (ltms,az,el,file,ix) VALUES(?,?,?,?,?)", values)

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
		original.append(0)	
	
	prev = 0
	next = 0
	#this loop will do this pass a few times, and remove the smaller values first
	for size in range(20, 121, 20):
		#go through the list of dictionaries
		#if size == 120:
			#c.execute("update `positions` set `az`=361,`el`=361 where count<120")
		for i, e in enumerate(data):
			if i == len(data)-1:
				next = i
			else:
				next = i+1
			ne = data[next]
			pe = data[prev]
			#use = prev #default is to extend the previous entry
			#rem = i
			if e['count'] < size:
				if pe['az'] == ne['az'] and pe['el'] == ne['el']:
					data[i]['count'] = pe['count'] + e['count'] + ne['count']
					data[i]['start'] = pe['start']
					data[i]['end'] = ne['end']
					data[i]['az'] = ne['az']
					data[i]['el'] = ne['el']					
					c.execute("delete from `positions` where rowid=? or rowid=?",(data[prev]['rowid'],data[next]['rowid']))
			
					c.execute("update `positions` set "+tf.sqlDataString(data[i])+" where rowid=?", (data[i]['rowid'],))
					del data[next], data[prev]
				else:
					if e['az'] == ne['az'] and e['el'] == ne['el']:
						data[i]['count'] += ne['count']
						data[i]['end'] = ne['end']
						c.execute("delete from `positions` where rowid=?",(data[next]['rowid'],))
						del data[next]			
			
					if e['az'] == pe['az'] and e['el'] == pe['el']:
						data[i]['count'] += pe['count']
						data[i]['start'] = pe['start']
						c.execute("delete from `positions` where rowid=?",(data[prev]['rowid'],))
						del data[prev]
				'''
				print "########"
				print pe, e, ne
				#if pe['az']==ne['az'] and pe['el']==ne['el']: #default: either side would be fine
				#lowest priority goes first...
				if ne['az'] == 361 and ne['el'] == 361:
					use = next
				if pe['az'] == 361 and pe['el'] == 361:
					use = prev

				if ne['az'] == e['az'] and ne['el'] == e['el']:
					use = next
				if pe['az'] == e['az'] and pe['el'] == e['el']:
					use = prev

				if i == 0: #incase looking at first entry
					use = next
				print "------"
				print data[use]
				start
				if use == next:
					if pe['az'] = ne['az'] and pe['el'] = ne['el']: #if this is true i can merge both sides
						data[use]['start'] = pe['start']
					else:
						data[use]['start'] = e['start']
					if i != 0:
						data[use]['count'] += pe['count']
						rem = prev
				else:
					data[use]['end'] = ne['end']
					if i != len(data)-1: #not the last element
						data[use]['count'] += ne['count']
						rem = next
				data[use]['count'] += e['count']
				print data[use]
				#print "e:", e
				c.execute("update `positions` set "+tf.sqlDataString(data[use])+" where rowid=?", (data[use]['rowid'],))
				c.execute("delete from `positions` where rowid=? or rowid=?",(e['rowid'], data[rem]['rowid']))
				if rem != i:
					del data[i], data[rem]
				else:
					del data[i]
				'''
			prev = i

	show = list()
	for x in data:
		for z in range(x['count']):
			show.append(x['az']+x['el'])
		show.append(0)	
	#draw the graph
	fig = plt.figure()
	ax = fig.add_subplot(111)
	ax.plot(show, linewidth=2)
	ax.plot(original)
	plt.show()

	#_END OF DATA CLEANUP_#


if options.graph:
	#this gathers data for the graph
	c.execute("select rowid,* from `positions` ")
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
