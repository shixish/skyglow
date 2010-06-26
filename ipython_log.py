#log# Automatic Logger file. *** THIS MUST BE THE FIRST LINE ***
#log# DO NOT CHANGE THIS LINE OR THE TWO BELOW
#log# opts = Struct({'__allownew': True, 'logfile': 'ipython_log.py', 'pylab': 1})
#log# args = []
#log# It is safe to make manual edits below here.
#log#-----------------------------------------------------------------------
import numpy as np
import skyglow as sg
import uavdata as ud
sg00 = ud.UAVData('/media/FreeAgent Drive/skyglowdec03/091203_004.img')
fm = sg.framemeta(0)
fm = sg00.framemeta(0)
fm
fm = sg00.framemeta(1)
fm
sg00.K
azel = findazelranges(sg00)
azel = sg.findazelranges(sg00)
reload(sg)
azel = sg.findazelranges(sg00)
azel
type(azel)
reload(sg)
azel = sg.findazelranges(sg00)
azel
azel.values()
azel.values().sort()
sort(azel.values())
azelvl = azel.values()
azelvl.sort()
azelvl
sg00.framemeta(0)['TragetAzimuth']
(sg00.framemeta(0))['TragetAzimuth']
fm00 = sg00.framemeta(0)
fm00['TargetAzimuth']
(sg00.framemeta(0))['TargetAzimuth']
[sg00.framemeta(i)['TargetAzimuth'] for i in range(0,3)]
[sg00.framemeta(i)['TargetAzimuth'] for i in range(0,10)]
reload(sg)
azel = sg.findazelranges(sg00)
reload(sg)
azel = sg.findazelranges(sg00)
azel
azelvl = azel.values()
azelvl.sort()
azelvl
round(4.4705, 1)
reload(sg)
azel = sg.findazelranges(sg00)





azel = sg.findazelranges(sg00)
reload(sg)
azel = sg.findazelranges(sg00)
azel
azelvl = azel.values()
azelvl.sort()
azelvl
sg00.finfo.fspec
[sg00.framemeta(i)['TargetAzimuth'] for i in range(0,10)]
[sg00.framemeta(i)['TargetAzimuth'] for i in range(1623,1625)]
[sg00.framemeta(i)['TargetAzimuth'] for i in range(1620,1630)]
[(x['TargetAzimuth'], x['TargetElevation']) for x in [sg00.framemeta(i) in range(1620,1630)]]
[(x['TargetAzimuth'], x['TargetElevation']) for x in [sg00.framemeta(i) for i in range(1620,1630)]]
[(x['TargetAzimuth'], x['TargetElevation']) for x in [sg00.framemeta(i) for i in range(0,30)]]
reload(sg)
azel(0,10)
sg.azel(0,10)
reload(sg)
sg.azel(sg00,0,10)
azelvl
reload(sg)
sg.findazelranges(sg00)





reload(sg)
sg.findazelranges(sg00)
azelvl = azel.value()
azel = sg.findazelranges(sg00)
azelvl = azel.values()
azelvl.sort()
azelvl
[x['FrameCounter'] for x in [sg00.framemeta(i) for i in range(0,30)]]
reload(sg)
xseq = [3,2,5,1,3,7,5]
xseq[-1]
xseq.push(8)
xseq.append(8)
xseq
xseq.append([])
xseq
xseq[-1].append(12)
xseq
reload(sg)
sg.splitsames([3,3,3,2,2,5,5,5,5,5,1,1])
reload(sg)
sg.splitsames([3,3,3,2,2,5,5,5,5,5,1,1])
operator.eq(2,3)
reload(sg)
reload(sg)
reload(sg)
sg.splitsames([3,3,3,2,2,5,5,5,5,5,1,1])
sg.splitsames([3,3,3,2,2,5,5,5,5,5,1,1], lambda x,y: abs(x-y)<=1)
reload(sg)
reload(sg)
azels = ixazel(sg00, 0, sg00.K)
azels = sg.ixazel(sg00, 0, sg00.K)
azels[0:12]
azelsp = splitsames(ixazels, lambda: a,b:(a[1],a[2])==(b[1],b[2]))
azelsp = splitsames(ixazels, lambda a,b:(a[1],a[2])==(b[1],b[2]))
azelsp = sg.splitsames(ixazels, lambda a,b:(a[1],a[2])==(b[1],b[2]))
azelsp = sg.splitsames(azels, lambda a,b:(a[1],a[2])==(b[1],b[2]))
azelsp[0:12]
azelsp[0]
reload(sg)
reload(sg)
azel = sg.findazelranges(sg00)
azel
reload(sg)
azel = sg.findazelranges(sg00)
reload(sg)
azel = sg.findazelranges(sg00)
azel
_ip.magic("logstart ")

1+2
_ip.magic("hist ")
_ip.magic("hist 0")
_ip.magic("hist 4")
_ip.magic("hist 129")
quit()
