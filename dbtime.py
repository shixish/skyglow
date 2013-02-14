#from time import struct_time#, sys
import time
#from datetime import datetime as dt

'''
dbtime class was created to extend python's built-in time manipulation functionality.
useage: newtime = dbtime.dbtime(...)
The class can be initialized in several ways:
	-None; it can be left blank. If so, it initializes to '2000-01-01 00:00:00'
	-LTime variable (see: time.mktime())
	-Dict {"year", "mon", "month", "day" ...}
		ex: dbtime.dbtime({"year":2010,"mon":3,"day":6,"hour":5,"min":24,"sec":59})
	-List or time.struct_time as produced by time.localtime()
You can set values after initialization by using the .set method or using square brackets:
	ex: 	mytime["year"] = 2009
			mytime["day"] += 1
You can get individual values by using square brackets as above.
'''
class dbtime:
	valmap = {"year":0, "mon":1, "month":1, "day":2, "mday":2, "hour":3, "hours":3, "minute":4, "minutes":4, "min":4, "second":5, "seconds":5, "sec":5, "wday":6, "yday":7, "isdst":8}
	maxes = [2038,12,31,24,60,60]
	vals = [0,0,0,0,0,0,0,0,0]
	def __init__(self, new = None):
		if type(new) == dict:
			self.set(new)
		elif type(new) == int or type(new) == float:
			self.vals = list(time.localtime(new))
		elif type(new) == time.struct_time:
			self.vals = list(new)
		elif type(new) == list and len(new) == 9:
			self.vals = new
		elif new:
			raise RuntimeError('dbtime: Unknown initialization type.')

	#use either of these three to produce an integer representation of the date/time
	def __str__(self):
		return str(time.mktime(self.get()))
	
	def __int__(self):
		return int(time.mktime(self.get()))

	def __float__(self):
		return time.mktime(self.get())
	
	#This system assumes every month has 31 days. 
	#Ideally you wouldn't rely on this to fix the input.
	#I mainly did this so i can add and subtract hours, and it carries over to the next or previous day.
	def fix(self):
		for i,x in enumerate(self.maxes):
			n = len(self.maxes)-i-1
			extra = int(self.vals[n]/(self.maxes[n]+1))
			#print self.vals[n], "/", self.maxes[n], extra
			if n != 0 and extra:
				self.vals[n-1] += extra
				self.vals[n] = self.vals[n]%self.maxes[n]
		return self
			

	#copycat function for time.strftime()
	def strftime(self, format = None):
		if not format:
			format = '%Y-%m-%d %H:%M:%S'
		return time.strftime(format, self.get())

	#This function allows you to set multiple values at once.
	#Accepts:
	#	-Dict {"year", "mon", "month", "day" ...}
	#		ex: mytime.set({"year":2010,"mon":3,"day":6,"hour":5,"min":24,"sec":59})
	#	-List, Number: this will set all of the values specified by "List" to the value of "Number"
	#		ex: mytime.set(["year","mon"],0)
	#	-List, List: a mapping of keys to values
	#		ex: mytime.set(["year","mon"], [2010,4])
	def set(self, k, val = None):
		if type(k) == dict:
			for x in k:
				if x in self.valmap:
					self.vals[self.valmap[x]] = int(k[x])
		elif type(k) == list:
			if type(val) == list:
				if len(k) == len(val):
					for x in k:
						if x in self.valmap:
							self.vals[self.valmap[x]] = int(val[x])
				else:
					raise RuntimeError('dbtime: Set requires that both lists be the same length.')
			else:
				for x in k:
					if x in self.valmap:
						self.vals[self.valmap[x]] = int(val)
		elif type(k) == str and k.lower() in self.valmap:
			pos = self.valmap[k.lower()]
			self.vals[pos] = int(val)
		else:
			raise RuntimeError('dbtime: Cannot set: ' + str(k))
		self.fix()
		return self
	
	#returns a time.struct_time data structure which is used for python's built-in time functionality
	def get(self):
		return time.struct_time(self.vals)

	def __setitem__(self, k, val):
		if k.lower() in self.valmap:
			pos = self.valmap[k.lower()]
			self.vals[pos] = int(val)
			self.fix()
			return self
		else:
			raise RuntimeError('dbtime: Cannot set: ' + str(k))

	def __getitem__(self, k):
		if k.lower() in self.valmap:
			pos = self.valmap[k.lower()]
			return self.vals[pos]
		else:
			raise RuntimeError('dbtime: Cannot get: ' + str(k))
		
