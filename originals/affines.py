from PIL import Image
import numpy as np
import math

def trn2d(xt, yt):
    res = np.identity(3)
    res[0,2] = xt
    res[1,2] = yt
    return res

def rot2d(theta):
    res = np.identity(3)
    th = theta * (np.pi / 180.)
    res[0,0] = math.cos(th)
    res[0,1] = math.sin(th)
    res[1,0] = -math.sin(th)
    res[1,1] = math.cos(th)
    return res

def scl2d(scl):
    res = np.identity(3)
    res[0,0] = scl
    res[1,1] = scl
    return res

def extract(mat):
    return (mat[0, 0], mat[0, 1], mat[0, 2], mat[1, 0], mat[1, 1], mat[1, 2])

def imaff(az, el, nrows=240, ncols=320, newsize=3780, fov=15):
    pixpdeg = ncols / fov

    print 'nrows = ', nrows
    print 'ncols = ', ncols
    print 'pixpdeg = ', pixpdeg

    trn1 = np.identity(3)
    rot1 = np.identity(3)
    trn2 = np.identity(3)
    trn3 = np.identity(3)

    # +ve is up / left
    # -ve is down / right
    trn1 = trn2d(ncols/2, nrows/2) # center at 0, 0
    trn2 = trn2d(0, (90 - el) * pixpdeg) # move up
    trn3 = trn2d(-newsize/2., -newsize/2.) # bring 0, 0 to center in new image
    rot1 = rot2d(az) # rotate

    res = np.identity(3)
    res = np.dot(trn1, res)
    #res = np.dot(trn2, res)
    res = np.dot(rot1, res)
    #res = np.dot(trn3, res)

    return extract(res)

def appazel(az, el, im, fov=15, sc=0.25):
    ncols, nrows = im.size
    affarg = imaff(az, el, nrows, ncols)
    pixpdeg = ncols / fov
    sz = 180 * pixpdeg
    newsize = (sz, sz)
    im2 = Image.new(im.mode, newsize)
    #print im2.size
    #im.paste(im2)
    im2.paste(im, (0, 0) + im.size)
    im3 = im2.transform(newsize, Image.AFFINE, affarg)
    print im3.size
    print sz
    print sz/2
#    for i in xrange(20):
#        for j in xrange(20):
#            im3.putpixel((sz/2-10+i, sz/2-10+j), 255)
    for i in xrange(sz):
        im3.putpixel((sz/2-1, i), 255)
        im3.putpixel((sz/2, i), 255)
        im3.putpixel((sz/2+1, i), 255)
        im3.putpixel((i, sz/2-1), 255)
        im3.putpixel((i, sz/2), 255)
        im3.putpixel((i, sz/2+1), 255)

        im3.putpixel((sz/2+(15*pixpdeg)-1, i), 255)
        im3.putpixel((sz/2+(15*pixpdeg), i), 255)
        im3.putpixel((sz/2+(15*pixpdeg)+1, i), 255)
        
    return im3

def appazel2(az, el, im, fov=15, sc=0.25):
    ncols, nrows = im.size
    #affarg = imaff(az, el, nrows, ncols)
    pixpdeg = ncols / fov
    totdeg = 140
    sz = totdeg * pixpdeg
    #sz = 9 * 240 * 1.3
    newsize = (sz, sz)
    im2 = Image.new(im.mode, newsize)
    #print im2.size
    #im.paste(im2)
    # paste location
    #pl_n = sz/2 - nrows/2 - (totdeg / 2 - el) * pixpdeg
    pl_n = sz/2 - nrows/2 - ((totdeg / 2) - el) * pixpdeg
    pl_w = sz/2 - ncols/2
    pl_s = pl_n + im.size[1]
    pl_e = pl_w + im.size[0]
    pasteloc = (pl_w, pl_n, pl_e, pl_s)
    #print 'pasteloc = ', pasteloc
    im2.paste(im, pasteloc)
    
    im3 = im2.rotate(az)
#    for i in xrange(20):
#        for j in xrange(20):
#            im3.putpixel((sz/2-10+i, sz/2-10+j), 255)
    for i in xrange(sz):
        im3.putpixel((sz/2-1, i), 255)
        im3.putpixel((sz/2, i), 255)
        im3.putpixel((sz/2+1, i), 255)

        im3.putpixel((i, sz/2-1), 255)
        im3.putpixel((i, sz/2), 255)
        im3.putpixel((i, sz/2+1), 255)

        #im3.putpixel((sz/2+(15*pixpdeg)-1, i), 255)
        #im3.putpixel((sz/2+(15*pixpdeg), i), 255)
        #im3.putpixel((sz/2+(15*pixpdeg)+1, i), 255)
        
        #im3.putpixel((sz/2-(15*pixpdeg)-1, i), 255)
        #im3.putpixel((sz/2-(15*pixpdeg), i), 255)
        #im3.putpixel((sz/2-(15*pixpdeg)+1, i), 255)
        
    return im3
