import glob
import cPickle
import skyglow as sg

glbs = ['/media/LAVAH/data20100211/*/*.img',
        '/media/LAVAH/data20100217/*/*.img',
        '/media/LAVAH/data20100218/*/*.img']

print 'glbs = ', glbs

cats = []
for glb in glbs:
    print('>>>  catalog')
    print('glb = ', glb)
    fls = glob.glob(glb)
    fls.sort()
    cat = sg.catalog(fls, True)
    cats.append(cat)

catims = []
for cat in cats:
    print('>>>  writepositionimages')
    print("cat[0]['filename'] = ", cat[0]['filename'])
    catim = sg.writepositionimages(cat, True)
    catims.append(catim)

for cat in catims:
    print('>>>  buildcollage')
    print("cat[0]['filename'] = ", cat[0]['filename'])
    sg.buildcollage(cat)

for cat in catims:
    print('>>>  writecatalogcollage')
    print("cat[0]['filename'] = ", cat[0]['filename'])
    sg.writecatalogcollage(cat)

for cat in catims:
    print('>>>  writecatalogpositions')
    print("cat[0]['filename'] = ", cat[0]['filename'])
    sg.writecatalogpositions(cat)

catsecs = []
for cat in catims:
    print('>>>  writeimagesforvideo')
    print("cat[0]['filename'] = ", cat[0]['filename'])
    catsec = sg.writeimagesforvideo(cat, True)
    catsecs.append(catsec)

#catsecs = []
#catsecpths = ['/media/LAVAE/data20091215/dataproducts/caches/catalogsec.pk',
#              '/media/LAVAE/data20091216/dataproducts/caches/catalogsec.pk',
#              '/media/LAVAE/data20100118/dataproducts/caches/catalogsec.pk',
#              '/media/LAVAE/data20100119/dataproducts/caches/catalogsec.pk',
#              '/media/LAVAF/data20100120/dataproducts/caches/catalogsec.pk',
#              '/media/LAVAF/data20100121/dataproducts/caches/catalogsec.pk']
#for pth in catsecpths:
#    print('pth = ', pth)
#    with open(pth) as infile:
#        catsecs.append(cPickle.load(infile))

for cat in catsecs:
    print('>>>  writecatalogsectext')
    print("cat[0]['filename'] = ", cat[0]['filename'])
    sg.writecatalogsectext(cat)

#def createpassvideos(imgdir, viddir):
#def createposnvideos(imgdir, viddir):

