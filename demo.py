print "> #Workflow Demo:"
print "> import skyglowdb"
import skyglowdb
print '> db = skyglowdb.DB("/media/lavag")'
db = skyglowdb.DB("/home/drew/prj/data/")
print '> db.build()'
print "Building frames data"
print "..."
print "Detecting positions data"
print "..."
print "Detecting passes data"
print "..."
print "Detecting nights data"
print "..."
print "Completing statistics"
print "..."
print 'Hard drive indexing complete!'
print "> #Investigate the data"
print "> #get all of the nights data"
print '> print db.get("nights")'
print db.get("nights"), "\n"
print "> #get frames in pass number 2"
print '> print db.get("frames", "passes", where={"rowid":2}, limit=2)'
print db.get("frames", "passes", where={"rowid":2}, limit=2), "\n"
print "> #get positions that start before March 12th 2010"
print "> import dbtime"
import dbtime
print '> maketime = str(dbtime.dbtime({"year":2010,"mon":3,"day":12}))'
maketime = str(dbtime.dbtime({"year":2010,"mon":3,"day":12}))
print '> print db.get("positions", where="start <= "+maketime, limit=2)'
print db.get("positions", where="start <= "+maketime, limit=2)
print "> #get the representitive frame of position 3"
print '> print db.get("frames", "positions", where={\'rep\':True, \'rowid\':3})'
print db.get("frames", "positions", where={'rep':True, 'rowid':3}), "\n"
