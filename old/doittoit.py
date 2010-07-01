import skyglowtest as sg
import datetime
import cPickle
import os
import os.path as op

conn = sqlite3.connect('/tmp/example')

#handle command line arguements
from optparse import OptionParser
parser = OptionParser()
parser.add_option("--dir", help="directory to find the img files")
parser.add_option("--results", help="location of directory to put the results")
(options, args) = parser.parse_args()
rootdir = '/'

if options.dir and op.isdir(options.dir):
	rootdir = options.dir
elif not op.isdir(options.dir):
	raise RuntimeError('doittoit: invalid directory supplied (--dir [location])')
else:
	raise RuntimeError('doittoit: no data directory supplied (--dir [location])')

resultsdir = op.join(rootdir, 'shaps')
#if options.dir:
#	resultsdir = options.result
#else if not op.isdir(options.dir):
#	raise RuntimeError('doittoit: invalid results directory supplied (--results [location])')

if not op.isdir(resultsdir):
	os.makedirs(resultsdir)

#rootdir = '/media/shaps03'

# find all of the img files
imgfiles = []
imgfiles[:] = sg.locate('*.img', rootdir)
#
# pull out all of the unique directories containing img files
datdirs = set([op.dirname(x) for x in imgfiles])
#
cats = dict()
bigcat = []

for datdir in datdirs:
	print('datdir = ', datdir)
	cats[datdir] = sg.catalog(datdir, '', True)
	bigcat += cats[datdir]

##this is only useful if you start the script after the catalog files are already made
#catpaths = []
#catpaths[:] = sg.locate('catalog.pk', op.join(rootdir, 'data'))

#bigcat = []
#for catpath in catpaths:
#	with open(catpath) as catfile:
#		bigcat += cPickle.load(catfile)

#len(bigcat)
#reduce(lambda x, y: x + y, [len(cats[x]) for x in cats])

def posndatetime(p):
	return datetime.datetime(p['date_year'], p['date_month'], p['date_day'], p['date_hours'], p['date_minutes'], p['date_seconds'])
#
def timecmp(x, y):
	return posndatetime(x) < posndatetime(y)
#
bigcat.sort(cmp=timecmp)
#
nights = dict()
for posn in bigcat:
	night = datetime.datetime(posn['date_year'], posn['date_month'], posn['date_day'])
	midday = night.replace(hour=12)
	if posndatetime(posn) < midday:
		night = night.replace(day=night.day - 1)
	if not nights.has_key(night):
		nights[night] = []
	nights[night].append(posn)
for night in nights:
	nights[night].sort(cmp=timecmp)
	nights[night] = sg.redopasses(nights[night])


dpcats = dict()

#resultsdir = '/home/jra/shaps/201004'

# write position images
for k, ncat in nights.iteritems():
	dname = k.strftime('%Y%m%d')
	#print(op.join(resultsdir, 'dataproducts', dname))
	pth = op.join(resultsdir, 'dataproducts', dname)
	dpcats[k] = sg.writepositionimages(ncat, pth, True)

# build dpcats from dataproducts catalogs files
# (incase need to start over, we don't want to have to redo writepositionimages
catpaths = []
catpaths[:] = sg.locate('catalog.pk', op.join(resultsdir, 'dataproducts'))

print('catpaths = ', catpaths)

for catpath in catpaths:
	with open(catpath) as catfile:
		nightcat = cPickle.load(catfile)
		posn = nightcat[0]
		night = datetime.datetime(posn['date_year'], posn['date_month'], posn['date_day'])
		dpcats[night] = nightcat
'''
# write collage images
for k, dpcat in dpcats.iteritems():
	sg.writecollageimages(dpcat)

# write tex for collage catalogs
for k, dpcat in dpcats.iteritems():
	sg.writecatalogcollage(dpcat)

# write tex for position catalogs
for k, dpcat in dpcats.iteritems():
	sg.writecatalogpositions(dpcat)

seccats = dict()
'''

# write images for videos
for k, dpcat in dpcats.iteritems():
	seccats[k] = sg.writeimagesforvideo(dpcat, True)

# write detail data
for seccat in seccats:
	dname = k[4:]
	pth = op.join(rootdir, dname, 'detaildata.txt')
	writecatalogsectext(seccat, pth)

