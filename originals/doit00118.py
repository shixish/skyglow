import glob
import skyglow as sg
fls100118 = glob.glob('/media/New Volume/Data_20100118/*/*.img')
fls100118.sort()
cat100118 = sg.catalog_new(fls100118, True)
cat100118aug = sg.writeimages_new(cat100118, True)
sg.writewebpage2(cat100118aug)
sg.buildcollage2(cat100118aug)
