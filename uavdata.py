from os.path import isfile
from multidata import MultiData
import struct
import array

class UAVData(MultiData):

    def __init__(self, fspec):

        self.os_table = array.array('i')

        d = []
        if isfile(fspec):
            MultiData.__init__(self, fspec)
        else:
            raise RuntimeError('UAVData only accepts a filename in ctor')
        # only hadling single file
        fn = self.finfo.files[0]
        with open(fn, 'rb') as fs:
            fs.seek(0, 2)
            filesize = fs.tell()
            #print 'filesize = ', filesize
            fs.seek(0, 0)
            version = fs.read(16)
            version = version[0:8]
            #print 'version = ', version
            vers = float(version[5:8])
            #print 'vers = ', vers
            tmps = fs.read(8)
            self.K, offsettable = struct.unpack('ii', tmps)
            #print 'self.K = ', self.K
            #print 'offsettable = ', offsettable
            if vers == 1.8:
                file_header_size = 16 + 6 * 4 # file header
                file_header_size += 24 * 48 # token data list
                frame_header_size = 16 * 4 + 8 * 8
                minfilesize = file_header_size
                # frame headers for Background and NUC frames
                minfilesize += 2 * frame_header_size

                if filesize < minfilesize:
                    raise RuntimeError('UAVData: filesize too small')

                if offsettable > filesize:
                    raise RuntimeError('UAVData: bad offset table location')
                
                fs.seek(0x18, 0)
                tmps = fs.read(4)
                os_header = struct.unpack('i', tmps)
                
                minfilesize = offsettable + self.K * 4

                if filesize < minfilesize:
                    raise RuntimeError('UAVData: filesize too small')

                fs.seek(offsettable, 0)
                #print 'fs.tell() = ', fs.tell()
                #print 'itemsize = ', self.os_table.itemsize
                self.os_table.fromfile(fs, self.K)

                if len(self.os_table) <= 0:
                    raise RuntimeError('UAVData: offset table has zero length')

                fs.seek(self.os_table[0], 0)
                head = array.array('i')
                head.fromfile(fs, 18)
                self.M = head[5]
                self.N = head[4]
                hdrlen = head[10]
                nelms = self.M * self.N
                
                #print 'self.os_table = ', self.os_table
                #print 'nrows = ', self.M
                #print 'ncols = ', self.N
                #print 'hdrlen = ', hdrlen

                fs.seek(0x1c, 0)
                tmps = fs.read(4)
                bkg_os, = struct.unpack('i', tmps)
                fs.seek(bkg_os + hdrlen, 0)
                self.raw_dark = array.array('H')
                self.raw_dark.fromfile(fs, 2 * nelms)

                fs.seek(0x20, 0)
                tmps = fs.read(4)
                nuc_os, = struct.unpack('i', tmps)
                fs.seek(nuc_os + hdrlen, 0)
                self.raw_nuc = array.array('f')
                self.raw_nuc.fromfile(fs, 4 * nelms)


    def framemeta(self, index):
        val = {}
        fn = self.finfo.files[0]
        with open(fn, 'rb') as fs:
            fs.seek(self.os_table[index])
            dat = fs.read(4 * 16 + 8 * 8)
            i = 0
            val['LTime'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['MSTime'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['FrameCounter'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['DroppedFrames'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['FrameSizeX'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['FrameSizeY'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['TargetRange'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['Altitude'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['FocusStepOffset'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['BytesPerPixel'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['OffsetToImageData'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['CameraUsed'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['FilterWheelPosition'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['FocusMotorIndex'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['IntegrationTimeNS'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['TargetDeltaRange'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['TargetAzimuth'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['TargetElevation'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['TargetLatitude'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['TargetLongitutde'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['TargetAltitude'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['AircraftLatitude'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['AircraftLongitude'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['AircraftAltitude'], = struct.unpack('d', dat[i:i+8]);
        return val


    def frame(self, index):
        val = {}
        fn = self.finfo.files[0]
        with open(fn, 'rb') as fs:
            fs.seek(self.os_table[index])
            dat = fs.read(4 * 16 + 8 * 8)
            i = 0
            val['LTime'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['MSTime'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['FrameCounter'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['DroppedFrames'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['FrameSizeX'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['FrameSizeY'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['TargetRange'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['Altitude'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['FocusStepOffset'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['BytesPerPixel'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['OffsetToImageData'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['CameraUsed'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['FilterWheelPosition'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['FocusMotorIndex'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['IntegrationTimeNS'], = struct.unpack('I', dat[i:i+4]); i += 4
            val['TargetDeltaRange'], = struct.unpack('i', dat[i:i+4]); i += 4
            val['TargetAzimuth'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['TargetElevation'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['TargetLatitude'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['TargetLongitutde'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['TargetAltitude'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['AircraftLatitude'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['AircraftLongitude'], = struct.unpack('d', dat[i:i+8]); i += 8
            val['AircraftAltitude'], = struct.unpack('d', dat[i:i+8]);
            val['Data'] = array.array('H')
            val['Data'].fromfile(fs, val['FrameSizeX'] * val['FrameSizeY'])
        return val

    def __len__(self):
        return len(self.os_table)

    def __getitem__(self, key):
        if type(key) != type(1):
            raise TypeError('uavdata object can only be indexed by interger type')
        if key < 0 or key >= len(self):
            raise IndexError('uavdata object attempt to index out of range')
        val = self.frame(key)
        return val['Data']
