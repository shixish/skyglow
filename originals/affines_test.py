import affines as af
import numpy as np
import unittest

class TestAffines(unittest.TestCase):
    
#    def testdefault(self):
#        md = MultiData()
#        self.assertEqual(md.K, 0)
#        self.assertEqual(md.M, 0)
#        self.assertEqual(md.N, 0)
#        self.assertEqual(md.finfo.fdir, 1)

    def arraysclose(self, a, b, delta = 0.0000001):
        return np.all(np.abs(a - b) < delta)

    def testtrn(self):
        p1 = np.array( [0., 0., 1.] )
        p2 = np.array( [1., 1., 1.] )
        p3 = np.array( [-1., 1., 1.] )
        p4 = np.array( [-1., -1., 1.] )
        p5 = np.array( [1., -1., 1.] )
        self.assert_(np.all(p2 == np.dot(af.trn2d(1., 1.), p1)))
        self.assert_(np.all(p3 == np.dot(af.trn2d(-1., 1.), p1)))
        self.assert_(np.all(p4 == np.dot(af.trn2d(-1., -1.), p1)))
        self.assert_(np.all(p5 == np.dot(af.trn2d(1., -1.), p1)))

    def testrot(self):
        p000 = np.array( [0., 1., 1.] )

        p030 = np.array( [np.sin(np.pi / 6), np.cos(np.pi / 6), 1.] )
        p045 = np.array( [np.sin(np.pi / 4), np.cos(np.pi / 4), 1.] )
        p060 = np.array( [np.sin(np.pi / 3), np.cos(np.pi / 3), 1.] )
        p090 = np.array( [1., 0., 1.] )

        p120 = np.array( [np.sin(np.pi / 3), -np.cos(np.pi / 3), 1.] )
        p135 = np.array( [np.sin(np.pi / 4), -np.cos(np.pi / 4), 1.] )
        p150 = np.array( [np.sin(np.pi / 6), -np.cos(np.pi / 6), 1.] )
        p180 = np.array( [0., -1., 1.] )

        p210 = np.array( [-np.sin(np.pi / 6), -np.cos(np.pi / 6), 1.] )
        p225 = np.array( [-np.sin(np.pi / 4), -np.cos(np.pi / 4), 1.] )
        p240 = np.array( [-np.sin(np.pi / 3), -np.cos(np.pi / 3), 1.] )
        p270 = np.array( [-1., 0., 1.] )

        p300 = np.array( [-np.sin(np.pi / 3), np.cos(np.pi / 3), 1.] )
        p315 = np.array( [-np.sin(np.pi / 4), np.cos(np.pi / 4), 1.] )
        p330 = np.array( [-np.sin(np.pi / 6), np.cos(np.pi / 6), 1.] )
        p360 = np.array( [0., 1., 1.] )

        p3 = np.array( [1., 0., 1.] )
        p4 = np.array( [0., -1., 1.] )
        p5 = np.array( [-1., 0., 1.] )
        print 'p000 = ', p000

        print 'p030 = ', p030
        print 'p045 = ', p045
        print 'p060 = ', p060
        print 'p090 = ', p090

        print 'p120 = ', p120
        print 'p135 = ', p135
        print 'p150 = ', p150
        print 'p180 = ', p180

        print 'p210 = ', p210
        print 'p225 = ', p225
        print 'p240 = ', p240
        print 'p270 = ', p270

        print np.dot(af.rot2d(30), p030)
        # rot 0 deg
        #   cw into quad 1
        self.assert_(self.arraysclose(p030, np.dot(af.rot2d(30), p000)))
        self.assert_(self.arraysclose(p045, np.dot(af.rot2d(45), p000)))
        self.assert_(self.arraysclose(p060, np.dot(af.rot2d(60), p000)))
        self.assert_(self.arraysclose(p090, np.dot(af.rot2d(90), p000)))
        #   cw into quad 2
        self.assert_(self.arraysclose(p120, np.dot(af.rot2d(120), p000)))
        self.assert_(self.arraysclose(p135, np.dot(af.rot2d(135), p000)))
        self.assert_(self.arraysclose(p150, np.dot(af.rot2d(150), p000)))
        self.assert_(self.arraysclose(p180, np.dot(af.rot2d(180), p000)))
        #   cw into quad 3
        self.assert_(self.arraysclose(p210, np.dot(af.rot2d(210), p000)))
        self.assert_(self.arraysclose(p225, np.dot(af.rot2d(225), p000)))
        self.assert_(self.arraysclose(p240, np.dot(af.rot2d(240), p000)))
        self.assert_(self.arraysclose(p270, np.dot(af.rot2d(270), p000)))
        #   cw into quad 4
        self.assert_(self.arraysclose(p300, np.dot(af.rot2d(300), p000)))
        self.assert_(self.arraysclose(p315, np.dot(af.rot2d(315), p000)))
        self.assert_(self.arraysclose(p330, np.dot(af.rot2d(330), p000)))
        self.assert_(self.arraysclose(p360, np.dot(af.rot2d(360), p000)))

        # rot 30 deg
        #   cw
        self.assert_(self.arraysclose(p060, np.dot(af.rot2d(30), p030)))
        self.assert_(self.arraysclose(p090, np.dot(af.rot2d(60), p030)))
        self.assert_(self.arraysclose(p120, np.dot(af.rot2d(90), p030)))
        self.assert_(self.arraysclose(p150, np.dot(af.rot2d(120), p030)))
        self.assert_(self.arraysclose(p180, np.dot(af.rot2d(150), p030)))
        self.assert_(self.arraysclose(p210, np.dot(af.rot2d(180), p030)))
        self.assert_(self.arraysclose(p240, np.dot(af.rot2d(210), p030)))
        self.assert_(self.arraysclose(p270, np.dot(af.rot2d(240), p030)))
        self.assert_(self.arraysclose(p300, np.dot(af.rot2d(270), p030)))
        self.assert_(self.arraysclose(p330, np.dot(af.rot2d(300), p030)))
        self.assert_(self.arraysclose(p360, np.dot(af.rot2d(330), p030)))
        self.assert_(self.arraysclose(p030, np.dot(af.rot2d(360), p030)))

        # rot 30 deg
        #   ccw
        self.assert_(self.arraysclose(p360, np.dot(af.rot2d(-30), p030)))
        self.assert_(self.arraysclose(p330, np.dot(af.rot2d(-60), p030)))
        self.assert_(self.arraysclose(p300, np.dot(af.rot2d(-90), p030)))
        self.assert_(self.arraysclose(p270, np.dot(af.rot2d(-120), p030)))
        self.assert_(self.arraysclose(p240, np.dot(af.rot2d(-150), p030)))
        self.assert_(self.arraysclose(p210, np.dot(af.rot2d(-180), p030)))
        self.assert_(self.arraysclose(p180, np.dot(af.rot2d(-210), p030)))
        self.assert_(self.arraysclose(p150, np.dot(af.rot2d(-240), p030)))
        self.assert_(self.arraysclose(p120, np.dot(af.rot2d(-270), p030)))
        self.assert_(self.arraysclose(p090, np.dot(af.rot2d(-300), p030)))
        self.assert_(self.arraysclose(p060, np.dot(af.rot2d(-330), p030)))
        self.assert_(self.arraysclose(p030, np.dot(af.rot2d(-360), p030)))

        # rot 30 deg
        #   cw
        self.assert_(self.arraysclose(p060, np.dot(af.rot2d(390), p030)))
        self.assert_(self.arraysclose(p090, np.dot(af.rot2d(420), p030)))
        self.assert_(self.arraysclose(p120, np.dot(af.rot2d(450), p030)))
        self.assert_(self.arraysclose(p150, np.dot(af.rot2d(480), p030)))
        self.assert_(self.arraysclose(p180, np.dot(af.rot2d(510), p030)))
        self.assert_(self.arraysclose(p210, np.dot(af.rot2d(540), p030)))
        self.assert_(self.arraysclose(p240, np.dot(af.rot2d(570), p030)))
        self.assert_(self.arraysclose(p270, np.dot(af.rot2d(600), p030)))
        self.assert_(self.arraysclose(p300, np.dot(af.rot2d(630), p030)))
        self.assert_(self.arraysclose(p330, np.dot(af.rot2d(660), p030)))
        self.assert_(self.arraysclose(p360, np.dot(af.rot2d(690), p030)))
        self.assert_(self.arraysclose(p030, np.dot(af.rot2d(720), p030)))

    def testsclrn(self):
        p1 = np.array( [0., 0., 1.] )
        p2 = np.array( [1., 2., 1.] )
        p3 = np.array( [-1., 2., 1.] )
        p4 = np.array( [2., 4., 1.] )
        p5 = np.array( [-3., 6., 1.] )
        self.assert_(np.all(p1 == np.dot(af.scl2d(2.), p1)))
        self.assert_(np.all(p1 == np.dot(af.scl2d(-3.), p1)))

        self.assert_(np.all(p4 == np.dot(af.scl2d(2.), p2)))
        self.assert_(np.all(p5 == np.dot(af.scl2d(3.), p3)))


suite = unittest.TestLoader().loadTestsFromTestCase(TestAffines)
unittest.TextTestRunner(verbosity=2).run(suite)

#if __name__ == '__main__':
#    unittest.main()
