from uavdata import UAVData
from os.path import abspath, split
import unittest

class TestConstructors(unittest.TestCase):
    
    def testfile(self):
        tfil = './testdata/uavdata/09May11_234741.img'
        md = UAVData(tfil)
        #tdir, dum = split(tfil)
        #self.assertEqual(md.finfo.fdir, abspath(tdir))
        self.assertEqual(md.K, 7)
        self.assertEqual(md.M, 480)
        self.assertEqual(md.N, 640)

    def testframe(self):
        tfil = './testdata/uavdata/09May11_234741.img'
        md = UAVData(tfil)
        #tdir, dum = split(tfil)
        #self.assertEqual(md.finfo.fdir, abspath(tdir))
        self.assertEqual(md.K, 7)
        self.assertEqual(md.M, 480)
        self.assertEqual(md.N, 640)
        data = md.frame(0)

if __name__ == '__main__':
    unittest.main()
