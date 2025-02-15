# -*- coding: utf-8 -*-
"""
Module name: dso2ke

Copyright:
----------------------------------------------------------------------
dso2ke is Copyright (c) 2014 Good Will Instrument Co., Ltd All Rights Reserved.

This program is free software; you can redistribute it and/or modify it under the terms 
of the GNU Lesser General Public License as published by the Free Software Foundation; 
either version 2.1 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU Lesser General Public License for more details.

You can receive a copy of the GNU Lesser General Public License from 
http://www.gnu.org/

Note:
dso2ke uses third party software which is copyrighted by its respective copyright holder. 
For details see the copyright notice of the individual package.

----------------------------------------------------------------------
Description:
dso2ke is a python driver module used to get waveform and image from DSO.

Version: 1.10

Modified on NOV 12 2019
Updated on DEC 11 2022

Author: Kevin Meng, Petint
"""
import io
import os
import platform
import struct
import sys
import time
from struct import unpack

import numpy as np
from PIL import Image

from gw_com import Com
from gw_lan import Lan

__version__ = "1.05"  # dso2ke module's version.

sModelList = [
    ['GDS-2072E', 'DCS-2072E', 'IDS-2072E', 'GDS-72072E', 'MSO-2072E', 'MSO-72072E', 'MSO-2072EA', 'MSO-72072EA',
     'MDO-2072EC', 'MDO-72072EC', 'MDO-2072EG', 'MDO-72072EG', 'MDO-2072EX', 'MDO-72072EX', 'MDO-2072ES', 'MDO-72072ES',
     'GDS-2102E', 'DCS-2102E', 'IDS-2102E', 'GDS-72102E', 'MSO-2102E', 'MSO-72102E', 'MSO-2102EA', 'MSO-72102EA',
     'MDO-2102EC', 'MDO-72102EC', 'MDO-2102EG', 'MDO-72102EG', 'MDO-2102EX', 'MDO-72102EX', 'MDO-2102ES', 'MDO-72102ES',
     'GDS-2202E', 'DCS-2202E', 'IDS-2202E', 'GDS-72202E', 'MSO-2202E', 'MSO-72202E', 'MSO-2202EA', 'MSO-72202EA',
     'MDO-2202EC', 'MDO-72202EC', 'MDO-2202EG', 'MDO-72202EG', 'MDO-2202EX', 'MDO-72202EX', 'MDO-2202ES', 'MDO-72202ES',
     'RSMSO-2102E', 'RSMSO-2202E', 'RSMSO-2102EA', 'RSMSO-2202EA', 'RSMDO-2102EG', 'RSMDO-2202EG', 'RSMDO-2102EX',
     'RSMDO-2202EX',
     'MDO-2102A', 'MDO-2202A', 'MDO-2302A', 'MDO-2102AG', 'MDO-2202AG', 'MDO-2302AG'],
    ['GDS-2074E', 'DCS-2074E', 'IDS-2074E', 'GDS-72074E', 'MSO-2074E', 'MSO-72074E', 'MSO-2074EA', 'MSO-72074EA',
     'MDO-2074EC', 'MDO-72074EC', 'MDO-2074EG', 'MDO-72074EG', 'MDO-2074EX', 'MDO-72074EX', 'MDO-2074ES', 'MDO-72074ES',
     'GDS-2104E', 'DCS-2104E', 'IDS-2104E', 'GDS-72104E', 'MSO-2104E', 'MSO-72104E', 'MSO-2104EA', 'MSO-72104EA',
     'MDO-2104EC', 'MDO-72104EC', 'MDO-2104EG', 'MDO-72104EG', 'MDO-2104EX', 'MDO-72104EX', 'MDO-2104ES', 'MDO-72104ES',
     'GDS-2204E', 'DCS-2204E', 'IDS-2204E', 'GDS-72204E', 'MSO-2204E', 'MSO-72204E', 'MSO-2204EA', 'MSO-72204EA',
     'MDO-2204EC', 'MDO-72204EC', 'MDO-2204EG', 'MDO-72204EG', 'MDO-2204EX', 'MDO-72204EX', 'MDO-2204ES', 'MDO-72204ES',
     'RSMSO-2104E', 'RSMSO-2204E', 'RSMSO-2104EA', 'RSMSO-2204EA', 'RSMDO-2104EG', 'RSMDO-2204EG', 'RSMDO-2104EX',
     'RSMDO-2204EX']]


def generate_lut():
    global lu_table
    num = 65536
    lu_table = []
    for i in range(num):
        pixel888 = [0] * 3
        pixel888[0] = (i >> 8) & 0xf8
        pixel888[1] = (i >> 3) & 0xfc
        pixel888[2] = (i << 3) & 0xf8
        lu_table.append(pixel888)


class Dso:
    def __init__(self, interface):
        if os.name == 'posix':  # unix
            if os.uname()[1] == 'raspberrypi':
                self.osname = 'pi'
            else:
                self.osname = 'unix'
        else:
            self.osname = f'win {platform.uname()[2]}'
        if interface != '':
            self.connect(interface)
        else:
            self.chnum = 4
            self.connection_status = 0
        global inbuffer
        self.ver = __version__  # Driver version.
        self.iWave = [[], [], [], []]
        self.vdiv = [[], [], [], []]
        self.vunit = [[], [], [], []]
        self.dt = [[], [], [], []]
        self.vpos = [[], [], [], []]
        self.hpos = [[], [], [], []]
        self.ch_list = []
        self.info = [[], [], [], []]
        generate_lut()

    def connect(self, pname):
        if pname.count('.') == 3 and pname.count(':') == 1:  # Check if str is ip address or not.
            try:
                self.IO = Lan(pname)
            except :
                print('Open LAN port failed!')
                return
        elif ('/dev/ttyACM' in pname) or ('COM' in pname):  # Check if str is COM port.
            try:
                self.IO = Com(pname)
            except:
                print('Open COM port failed!')
                return
            self.IO.clearbuff()
        else:
            return
        self.write = self.IO.write
        self.read = self.IO.getdata
        self.readBytes = self.IO.readbytes
        self.closeIO = self.IO.closeIO
        self.write('*IDN?\n')
        model_name = self.read().split(',')[1]
        print('%s connected to %s successfully!' % (model_name, pname))
        if (self.osname == 'win10') and ('COM' in pname):
            self.write(':USBDelay ON\n')  # Prevent data loss on Win 10.
            print('Send :USBDelay ON')
        if (model_name in sModelList[0]):
            self.chnum = 2  # Got a 2 channel DSO.
            self.connection_status = 1

        elif (model_name in sModelList[1]):
            self.chnum = 4  # Got a 4 channel DSO.
            self.connection_status = 1
        else:
            self.chnum = 4
            self.connection_status = 0
            print('Device not found!')
            return

        if not os.path.exists('port.config'):
            f = open('port.config', 'wb')
            f.write(pname)
            f.close()

    def getBlockData(self):  # Used to get image data.
        global inbuffer
        inbuffer = self.readBytes(10)
        length = len(inbuffer)
        self.headerlen = 2 + int(inbuffer[1])
        pkg_length = int(inbuffer[2:self.headerlen]) + self.headerlen + 1  # Block #48000[..8000bytes raw data...]<LF>
        print("Data transferring...  ")

        pkg_length = pkg_length - length
        while True:
            print('%8d\r' % pkg_length)
            if pkg_length == 0:
                break
            else:
                if pkg_length > 100000:
                    length = 100000
                else:
                    length = pkg_length
                try:
                    buf = self.readBytes(length)
                except KeyboardInterrupt:
                    print('KeyboardInterrupt!')
                    self.closeIO()
                    sys.exit(0)
                num = len(buf)
                inbuffer += buf
                pkg_length = pkg_length - num

    def ImageDecode(self, type):
        if (type):  # 1 for RLE decode, 0 for PNG decode.
            raw_data = []
            # Convert 8 bits array to 16 bits array.
            data = unpack('<%sH' % (len(inbuffer[self.headerlen:-1]) / 2), inbuffer[self.headerlen:-1])
            l = len(data)
            if (l % 2 != 0):  # Ignore reserved data.
                l = l - 1
            package_length = len(data)
            index = 0
            bmp_size = 0
            while True:
                length = data[index]
                value = data[index + 1]
                index += 2
                bmp_size += length
                buf = [value for x in range(0, length)]
                raw_data += buf
                if (index >= l):
                    break
            width = 800
            height = 480
            # Convert from rgb565 into rgb888
            index = 0
            rgb_buf = []
            num = width * height
            for index in range(num):
                rgb_buf += lu_table[raw_data[index]]
            img_buf = struct.pack("1152000B", *rgb_buf)
            self.im = Image.frombuffer('RGB', (width, height), img_buf, 'raw', 'RGB', 0, 1)
        else:  # 0 for PNG decode.
            self.im = Image.open(io.BytesIO(inbuffer[self.headerlen:-1]))
            print('PngDecode()')
        if (self.osname == 'pi'):
            self.im = self.im.transpose(Image.FLIP_TOP_BOTTOM)  # For raspberry pi only.

    def getRawData(self, header_on, ch):  # Used to get waveform's raw data.
        global inbuffer
        self.dataMode = []
        print('Waiting CH%d data... ' % ch)
        if (header_on == True):
            self.write(":HEAD ON\n")
        else:
            self.write(":HEAD OFF\n")

        if (self.checkAcqState(ch) == -1):
            return
        self.write(":ACQ%d:MEM?\n" % ch)  # Write command(get raw datas) to DSO.

        index = len(self.ch_list)
        if header_on:
            if index == 0:  # Getting first waveform => reset self.info.
                self.info = [[], [], [], []]

            self.info[index] = self.read().split(';')
            num = len(self.info[index])
            self.info[index][num - 1] = self.info[index][num - 2]  # Convert info[] to csv compatible format.
            self.info[index][num - 2] = 'Mode,Fast'
            sch = [s for s in self.info[index] if "Source" in s]
            self.ch_list.append(sch[0].split(',')[1])
            sdt = [s for s in self.info[index] if "Sampling Period" in s]
            self.dt[index] = float(sdt[0].split(',')[1])
            sdv = [s for s in self.info[index] if "Vertical Scale" in s]
            self.vdiv[index] = float(sdv[0].split(',')[1])
            svpos = [s for s in self.info[index] if "Vertical Position" in s]
            self.vpos[index] = float(svpos[0].split(',')[1])
            shpos = [s for s in self.info[index] if "Horizontal Position" in s]
            self.hpos[index] = float(shpos[0].split(',')[1])
            svunit = [s for s in self.info[index] if "Vertical Units" in s]
            self.vunit[index] = svunit[0].split(',')[1]
        self.getBlockData()
        self.points_num = len(inbuffer[self.headerlen:-1]) / 2  # Calculate sample points length.
        self.iWave[index] = unpack('>%sh' % (len(inbuffer[self.headerlen:-1]) / 2), inbuffer[self.headerlen:-1])
        del inbuffer
        return index  # Return the buffer index.

    def checkAcqState(self, ch):
        str_stat = ":ACQ%d:STAT?\n" % ch
        loop_cnt = 0
        max_cnt = 0
        while True:  # Checking acquisition is ready or not.
            self.write(str_stat)
            state = self.read()
            if state[0] == '1':
                break
            time.sleep(0.1)
            loop_cnt += 1
            if loop_cnt >= 50:
                print('Please check signal!')
                loop_cnt = 0
                max_cnt += 1
                if max_cnt == 5:
                    return -1
        return 0

    def convertWaveform(self, ch, factor):
        dv = self.vdiv[ch] / 25
        if (factor == 1):
            num = self.points_num
            fWave = [0] * num
            for x in range(num):  # Convert 16 bits signed to floating point number.
                fWave[x] = float(self.iWave[ch][x]) * dv
        else:  # Reduced to helf points.
            num = self.points_num / factor
            fWave = [0] * num
            for x in range(num):  # Convert 16 bits signed to floating point number.
                i = factor * x
                fWave[x] = float(self.iWave[ch][i]) * dv
        return fWave

    def readrawdatafile(self, filename):
        # Check file format(csv or lsf)
        self.info = [[], [], [], []]
        if filename.lower().endswith('.csv'):
            self.datatype = 'csv'
        elif filename.lower().endswith('.lsf'):
            self.datatype = 'lsf'
        else:
            return -1
        f = open(filename, 'rb')
        info = []
        # Read file header.
        if self.datatype == 'csv':
            for x in range(26):
                info.append(f.readline().split(b',\r\n')[0])
            bytedata = info[0].split(b',')[1]
            if (bytedata != b'2.0E') and (bytedata != b'2.0MA'):  # Check format version
                f.close()
                print('Format error!')
                return -1
            count = info[5].count(b'CH')  # Check channel number in file.
            wave = f.read().splitlines()  # Read raw data from file.
            self.points_num = len(wave)
            if info[24].split(b',')[1] == 'Fast':
                self.dataMode = 'Fast'
            else:
                self.dataMode = 'Detail'
        else:
            info = f.readline().split(b';')  # The last item will be '\n'.
            bytedata = info[0].split(b'Format,')[1]
            if (bytedata != '2.0E') and (bytedata != '2.0MA'):  # Check format version
                f.close()
                print('Format error!')
                return -1
            if f.read(1) != '#':
                print('Format error!')
                sys.exit(0)
            digit = int(f.read(1))
            num = int(f.read(digit))
            count = 1
            wave = f.read()  # Read raw data from file.
            self.points_num = len(wave) / 2  # Calculate sample points length.
            self.dataMode = 'Fast'
        f.close()

        print('Plotting waveform...')
        if (count == 1):  # 1 channel
            self.iWave[0] = [0] * self.points_num
            self.ch_list.append(info[5].split(b',')[1])
            self.vunit[0] = info[6].split(b',')[1]  # Get vertical units.
            self.vdiv[0] = float(info[12].split(b',')[1])  # Get vertical scale. => Voltage for ADC's single step.
            self.vpos[0] = float(info[13].split(b',')[1])  # Get vertical position.
            self.hpos[0] = float(info[16].split(b',')[1])  # Get horizontal position.
            self.dt[0] = float(info[19].split(b',')[1])  # Get sample period.
            dv1 = self.vdiv[0] / 25
            vpos = int(self.vpos[0] / dv1) + 128
            vpos1 = self.vpos[0]
            num = self.points_num
            if self.datatype == 'csv':
                for x in range(26):
                    self.info[0].append(info[x])
                if self.dataMode == 'Fast':
                    for x in range(num):
                        value = int(wave[x].split(b',')[0])
                        self.iWave[0][x] = value
                else:
                    for x in range(num):
                        value = float(wave[x].split(b',')[1])
                        self.iWave[0][x] = int(value / dv1)
            else:  # lsf file
                for x in range(24):
                    self.info[0].append(info[x])
                self.info[0].append('Mode,Fast')  # Convert info[] to csv compatible format.
                self.info[0].append(info[24])
                self.iWave[0] = np.array(unpack('<%sh' % (len(wave) / 2), wave))
                for x in range(num):  # Convert 16 bits signed number to floating point number.
                    self.iWave[0][x] -= vpos
            del wave
            return 1
        else:  # multi channel, csv file only.
            # write waveform's info to self.info[]
            for ch in range(count):
                self.info[ch].append(info[0])
            for x in range(1, 25):
                str = info[x].split(',')
                for ch in range(count):
                    self.info[ch].append('%s,%s' % (str[2 * ch], str[2 * ch + 1]))
            str = info[25].split(',')
            for ch in range(count):
                self.info[ch].append('%s' % str[2 * ch])

            for ch in range(count):
                self.ch_list.append(info[5].split(',')[2 * ch + 1])
                self.iWave[ch] = [0] * self.points_num
                self.vunit[ch] = info[6].split(',')[2 * ch + 1]  # Get vertical units.
                self.vdiv[ch] = float(
                    info[12].split(b',')[2 * ch + 1])  # Get vertical scale. => Voltage for ADC's single step.
                self.vpos[ch] = float(info[13].split(b',')[2 * ch + 1])  # Get vertical position.
                self.hpos[ch] = float(info[16].split(b',')[2 * ch + 1])  # Get horizontal position.
                self.dt[ch] = float(info[19].split(b',')[2 * ch + 1])  # Get sample period.
            num = self.points_num
            if (self.dataMode == 'Fast'):
                for ch in range(count):
                    self.iWave[ch] = [0] * num
                for i in range(num):
                    str = wave[i].split(',')
                    for ch in range(count):
                        index = 2 * ch
                        self.iWave[ch][i] = int(str[index])
            else:
                dv = []
                for ch in range(count):
                    dv.append(self.vdiv[ch] / 25)
                for i in range(num):
                    str = wave[i].split(',')
                    for ch in range(count):
                        index = 2 * ch + 1
                        value = float(wave[i].split(',')[index])
                        self.iWave[ch][i] = int(value / dv[ch])
            del wave
            return count

    def ischannelon(self, ch):
        self.write(":CHAN%d:DISP?\n" % ch)
        onoff = self.read()
        onoff = onoff[:-1]
        if onoff == 'ON':
            return True
        else:
            return False
