from multidata import MultiData
from os.path import abspath, split
import unittest

class TestConstructors(unittest.TestCase):
    
#    def testdefault(self):
#        md = MultiData()
#        self.assertEqual(md.K, 0)
#        self.assertEqual(md.M, 0)
#        self.assertEqual(md.N, 0)
#        self.assertEqual(md.finfo.fdir, 1)

    def testdir(self):
        tdir = './testdata/pngfileseq'
        md = MultiData(tdir)
        self.assertEqual(md.finfo.fdir, abspath(tdir))
        self.assertEqual(md.K, 11)

    def testfile(self):
        tfil = './testdata/pngfileseq/gems1.png'
        md = MultiData(tfil)
        tdir, dum = split(tfil)
        self.assertEqual(md.finfo.fdir, abspath(tdir))
        self.assertEqual(md.K, 1)

    def testlst(self):
        tlst = ['./testdata/pngfileseq/gems10.png',
                './testdata/pngfileseq/gems3.png',
                './testdata/pngfileseq/gems4.png',
                './testdata/pngfileseq/gems1.png']
        md = MultiData(tlst)
        tdir, dum = split(tlst[0])
        self.assertEqual(md.finfo.fdir, abspath(tdir))
        self.assertEqual(md.K, 4)

    def testglob(self):
        tglb = './testdata/pngfileseq/*.png'
        md = MultiData(tglb)
        tdir, dum = split(tglb)
        self.assertEqual(md.finfo.fdir, abspath(tdir))
        self.assertEqual(md.K, 11)


if __name__ == '__main__':
    unittest.main()
