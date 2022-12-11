# -*- coding: utf-8 -*-
"""
Program name: OpenWave-2KE

Copyright:
----------------------------------------------------------------------
OpenWave-2KE is Copyright (c) 2014 Good Will Instrument Co., Ltd All Rights Reserved.

This program is free software; you can redistribute it and/or modify it under the terms 
of the GNU Lesser General Public License as published by the Free Software Foundation; 
either version 2.1 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License for more details.

You can receive a copy of the GNU Lesser General Public License from http://www.gnu.org/

Note:
OpenWave-2KE uses third party software which is copyrighted by its respective copyright 
holder. For details see the copyright notice of the individual package.

The Qt GUI Toolkit is Copyright (c) 2014 Digia Plc and/or its subsidiary(-ies).
OpenWave-2KE use Qt version 4.8 library under the terms of the LGPL version 2.1.
----------------------------------------------------------------------
Description:
OpenWave-2KE is a python example program used to get waveform and image from DSO.

Version: 1.07

Modified on APR 07 2020
Updated on DEC 11 2022

Author: Kevin Meng, Petint
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_qt import FigureCanvasQT as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as aa
from PySide6 import QtCore, QtGui
import numpy as np
from PIL import Image
import os
import sys
import time
from gw_com import Com
from gw_lan import Lan, isip
import dso2ke

__version__ = "1.07"  # OpenWave-2KE software version.
mpl.rcParams['backend.qt4'] = 'PySide'  # Used for PySide.
mpl.rcParams['agg.path.chunksize'] = 100000  # For big data.


def checkinterface(iport):
    if iport != '':
        print(iport)
    # Load config file if it exists
    elif os.path.exists('port.config'):
        f_conf = open('port.config', 'r')
        while True:
            iport = f_conf.readline()
            if iport == '':
                f_conf.close()
                return iport
            if iport[0] != '#':
                break
        f_conf.close()

    # Check ethernet connection(model name not checked)
    sInterface = iport.split('\n')[0]
    # print 'sInterface=',sInterface
    if sInterface.count('.') == 3 and sInterface.count(':') == 1:  # Got ip address.
        ip, _port = sInterface.split(':')
        if isip(ip):
            contest = Lan.connectsocketn_test(sInterface)
            if contest != '':
                return contest
    # Check COM port connection(model name not checked)
    elif 'COM' in sInterface:
        if Com.connection_test(sInterface) != '':
            return sInterface
    elif 'ttyACM' in sInterface:
        if 'ttyACM' == sInterface[0:6]:
            sInterface = '/dev/' + sInterface
        if Com.connection_test(sInterface) != '':
            return sInterface

    return Com.scanports()  # Scan all the USB port.


def show_image():
    # Turn the ticks off and show image.
    plt.clf()
    ax = plt.gca()
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    plt.imshow(dso.im)


class Window(QtGui.QWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle('OpenWave-2KE V%s' % __version__)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("openwave.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        # Waveform area.
        self.figure = plt.figure()
        self.figure.set_facecolor('white')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(800, 400)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.hide()
        # Zoom In/out and Capture Buttons
        self.zoomBtn = QtGui.QPushButton('Zoom')
        self.zoomBtn.setFixedSize(100, 30)
        self.zoomBtn.clicked.connect(self.toolbar.zoom)
        self.panBtn = QtGui.QPushButton('Pan')
        self.panBtn.setFixedSize(100, 30)
        self.panBtn.clicked.connect(self.toolbar.pan)
        self.homeBtn = QtGui.QPushButton('Home')
        self.homeBtn.setFixedSize(100, 30)
        self.homeBtn.clicked.connect(self.toolbar.home)
        self.captureBtn = QtGui.QPushButton('Capture')
        self.captureBtn.setFixedSize(100, 50)
        self.captureBtn.clicked.connect(self.manualcapture)
        if dso.connection_status == 0:
            self.captureBtn.setEnabled(False)
        self.continuousBtn = QtGui.QRadioButton('Continuous')
        self.continuousBtn.setEnabled(True)
        self.continuousBtn.clicked.connect(self.continuous)
        # Continuous capture selection
        self.captureLayout = QtGui.QHBoxLayout()
        self.captureLayout.addWidget(self.captureBtn)
        self.captureLayout.addWidget(self.continuousBtn)
        # Type: Raw Data/Image
        self.typeBtn = QtGui.QPushButton('Raw Data')
        self.typeBtn.setToolTip("Switch to get raw data or image from DSO.")
        self.typeBtn.setFixedSize(120, 50)
        self.typeFlag = True  # Initial state -> Get raw data
        self.typeBtn.setCheckable(True)
        self.typeBtn.setChecked(True)
        self.typeBtn.clicked.connect(self.typeaction)
        # Channel Selection.
        self.ch1checkBox = QtGui.QCheckBox('CH1')
        self.ch1checkBox.setFixedSize(60, 30)
        self.ch1checkBox.setChecked(True)
        self.ch2checkBox = QtGui.QCheckBox('CH2')
        self.ch2checkBox.setFixedSize(60, 30)
        if dso.chnum == 4:
            self.ch3checkBox = QtGui.QCheckBox('CH3')
            self.ch3checkBox.setFixedSize(60, 30)
            self.ch4checkBox = QtGui.QCheckBox('CH4')
            self.ch4checkBox.setFixedSize(60, 30)
        # Set channel selection layout.
        self.selectLayout = QtGui.QHBoxLayout()
        self.selectLayout.addWidget(self.ch1checkBox)
        self.selectLayout.addWidget(self.ch2checkBox)
        if dso.chnum == 4:
            self.selectLayout2 = QtGui.QHBoxLayout()
            self.selectLayout2.addWidget(self.ch3checkBox)
            self.selectLayout2.addWidget(self.ch4checkBox)
        self.typeLayout = QtGui.QHBoxLayout()
        self.typeLayout.addWidget(self.typeBtn)
        self.typeLayout.addLayout(self.selectLayout)
        if dso.chnum == 4:
            self.typeLayout.addLayout(self.selectLayout2)
        self.zoominoutLayout = QtGui.QHBoxLayout()
        self.zoominoutLayout.addWidget(self.zoomBtn)
        self.zoominoutLayout.addWidget(self.panBtn)
        self.zoominoutLayout.addWidget(self.homeBtn)
        # Save/Load/Quit button
        self.saveBtn = QtGui.QPushButton('Save')
        self.saveBtn.setFixedSize(100, 50)
        self.saveMenu = QtGui.QMenu(self)
        self.csvAction = self.saveMenu.addAction("&As CSV File")
        self.pictAction = self.saveMenu.addAction("&As PNG File")
        self.saveBtn.setMenu(self.saveMenu)
        self.saveBtn.setToolTip("Save waveform to CSV file or PNG file.")
        self.connect(self.csvaction, QtCore.SIGNAL(b"triggered()"), self.savecsvaction)
        self.connect(self.pictaction, QtCore.SIGNAL(b"triggered()"), self.savePngAction)
        self.loadBtn = QtGui.QPushButton('Load')
        self.loadBtn.setToolTip("Load CHx's raw data from file(*.csv, *.lsf).")
        self.loadBtn.setFixedSize(100, 50)
        self.loadBtn.clicked.connect(self.loadaction)
        self.quitBtn = QtGui.QPushButton('Quit')
        self.quitBtn.setFixedSize(100, 50)
        self.quitBtn.clicked.connect(self.quit)
        # set the layout
        self.waveLayout = QtGui.QHBoxLayout()
        self.waveLayout.addWidget(self.canvas)
        self.wave_box = QtGui.QVBoxLayout()
        self.wave_box.addLayout(self.waveLayout)
        self.wavectrlLayout = QtGui.QHBoxLayout()
        self.wavectrlLayout.addStretch(1)
        self.wavectrlLayout.addLayout(self.zoominoutLayout)
        self.wavectrlLayout.addStretch(1)
        self.wavectrlLayout.addLayout(self.captureLayout)
        self.wavectrlLayout.addStretch(1)
        self.saveloadLayout = QtGui.QHBoxLayout()
        self.saveloadLayout.addWidget(self.saveBtn)
        self.saveloadLayout.addWidget(self.loadBtn)
        self.saveloadLayout.addWidget(self.quitBtn)
        self.ctrl_box = QtGui.QHBoxLayout()
        self.ctrl_box.addLayout(self.typeLayout)
        self.ctrl_box.addLayout(self.saveloadLayout)
        main_box = QtGui.QVBoxLayout()
        main_box.addLayout(self.wave_box)  # Waveform area.
        main_box.addLayout(self.wavectrlLayout)  # Zoom In/Out...
        main_box.addLayout(self.ctrl_box)  # Save/Load/Quit
        self.setLayout(main_box)
        self.captured_flag = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timercapture)

    def typeaction(self):
        if self.typeFlag:
            self.typeFlag = False
            self.typeBtn.setText("Image")
            self.csvAction.setEnabled(False)
        else:
            self.typeFlag = True
            self.typeBtn.setText("Raw Data")
            self.csvAction.setEnabled(True)
        self.typeBtn.setChecked(self.typeFlag)
        self.ch1checkBox.setEnabled(self.typeFlag)
        self.ch2checkBox.setEnabled(self.typeFlag)
        if dso.chnum == 4:
            self.ch3checkBox.setEnabled(self.typeFlag)
            self.ch4checkBox.setEnabled(self.typeFlag)

    def savecsvaction(self):
        if self.typeFlag:  # Save raw data to csv file.
            file_name = QtGui.QFileDialog.getSaveFileName(self, "Save as", 'DS0001', "Fast CSV File(*.csv)")[0]
            num = len(dso.ch_list)
            # print num
            for ch in range(num):
                if not dso.info[ch]:
                    print('Failed to save data, raw data information is required!')
                    return
            sf = open(file_name, 'wt')
            item = len(dso.info[0])
            # Write file header.
            sf.write('%s,\r\n' % dso.info[0][0])
            for x in range(1, 24):
                txt = ''
                for ch in range(num):
                    txt += ('%s,' % dso.info[ch][x])
                txt += '\r\n'
                sf.write(txt)
            # Write Fast CSV mode only.
            txt = ''
            for ch in range(num):
                txt += 'Mode,Fast,'
            txt += '\r\n'
            sf.write(txt)

            txt = ''
            if num == 1:
                txt += ('%s,' % dso.info[0][25])
            else:
                for ch in range(num):
                    txt += ('%s,,' % dso.info[ch][25])
            txt += '\r\n'
            sf.write(txt)
            # Write raw data.
            item = len(dso.iWave[0])
            # print item
            tenth = int(item / 10)
            n_tenth = tenth - 1
            percent = 10
            for x in range(item):
                txt = ''
                if num == 1:
                    txt += ('%s,' % dso.iWave[0][x])
                else:
                    for ch in range(num):
                        txt += ('%s, ,' % dso.iWave[ch][x])
                txt += '\r\n'
                sf.write(txt)
                if x == n_tenth:
                    n_tenth += tenth
                    print('%3d %% Saved\r' % percent),
                    percent += 10
            sf.close()

    def savePngAction(self):
        # Save figure to png file.
        file_name = QtGui.QFileDialog.getSaveFileName(self, "Save as", 'DS0001', "PNG File(*.png)")[0]
        if file_name == '':
            return
        if self.typeFlag:  # Save raw data waveform as png file.
            main.figure.savefig(file_name)
        else:  # Save figure to png file.
            if dso.osname == 'pi':  # For raspberry pi only.
                img = dso.im.transpose(Image.FLIP_TOP_BOTTOM)
                img.save(file_name)
            else:
                dso.im.save(file_name)
        print('Saved image to %s.' % file_name)

    def loadaction(self):
        dso.ch_list = []
        full_path_name = QtGui.QFileDialog.getOpenFileName(self, self.tr("Open File"), ".",
                                                           "CSV/LSF files (*.csv *.lsf);;All files (*.*)")
        sFileName = np.compat.unicode(full_path_name).split(',')[0][3:-1]  # For PySide
        print(sFileName)
        if len(sFileName) <= 0:
            return
        if os.path.exists(sFileName):
            print('Reading file...')
            count = dso.readrawdatafile(sFileName)
            # Draw waveform.
            if count > 0:
                total_chnum = len(dso.ch_list)
                if total_chnum == 0:
                    return
                self.draw_wf(0)
        else:
            print('File not found!')

    def quit(self):
        if dso.connection_status == 1:
            dso.closeIO()
        self.close()

    def timercapture(self):
        self.capture()
        if self.continuousBtn.isChecked():
            self.timer.start(10)  # Automatic capturing.

    def manualcapture(self):
        if self.continuousBtn.isChecked():
            if self.captured_flag == 0:
                self.captured_flag = 1  # Continuous capture started.
                self.captureBtn.setText("Click to Stop")
                self.loadBtn.setEnabled(False)
                self.timer.start()
            else:
                self.captured_flag = 0  # Continuous capture stopped.
                self.captureBtn.setText("Capture")
                self.loadBtn.setEnabled(True)
                self.timer.stop()
        self.capture()

    def capture(self):
        dso.iWave = [[], [], [], []]
        dso.ch_list = []
        if self.typeFlag:  # Get raw data.
            draw_flag = False
            # Turn on the selected channels.
            if self.ch1checkBox.isChecked() and dso.ischannelon(1) is False:
                dso.write(":CHAN1:DISP ON\n")  # Set CH1 on.
            if self.ch2checkBox.isChecked() and dso.ischannelon(2) is False:
                dso.write(":CHAN2:DISP ON\n")  # Set CH2 on.
            if dso.chnum == 4:
                if self.ch2checkBox.isChecked() and dso.ischannelon(3) is False:
                    dso.write(":CHAN3:DISP ON\n")  # Set CH3 on.
                if self.ch2checkBox.isChecked() and dso.ischannelon(4) is False:
                    dso.write(":CHAN4:DISP ON\n")  # Set CH4 on.
            # Get all the selected channel's raw datas.
            if self.ch1checkBox.isChecked():
                dso.getRawData(True, 1)  # Read CH1's raw data from DSO (including header).
            if self.ch2checkBox.isChecked():
                dso.getRawData(True, 2)  # Read CH2's raw data from DSO (including header).
            if dso.chnum == 4:
                if self.ch3checkBox.isChecked():
                    dso.getRawData(True, 3)  # Read CH3's raw data from DSO (including header).
                if self.ch4checkBox.isChecked():
                    dso.getRawData(True, 4)  # Read CH4's raw data from DSO (including header).
            # Draw waveform.
            total_chnum = len(dso.ch_list)
            if total_chnum == 0:
                return
            if self.draw_wf(1) == -1:
                time.sleep(5)
                self.draw_wf(0)
        else:  # Get image.
            img_type = 1  # 1 for RLE format, 0 for PNG format.
            if img_type:
                dso.write(':DISP:OUTP?\n')  # Send command to get image from DSO.
            else:
                dso.write(':DISP:PNGOutput?\n')  # Send command to get image from DSO.
            dso.getBlockData()
            dso.ImageDecode(img_type)
            show_image()
            plt.tight_layout(True)
            self.canvas.draw()
            print('Image is ready!')

    def continuous(self):
        if self.continuousBtn.isChecked() is False:
            self.captured_flag = 0  # Continuous capture stopped.
            self.timer.stop()
            self.loadBtn.setEnabled(True)
            self.captureBtn.setText("Capture")

    def draw_wf(self, mode):
        total_chnum = len(dso.ch_list)
        num = dso.points_num
        ch_colortable = ['#C0B020', '#0060FF', '#FF0080', '#00FF60']
        ch = int(dso.ch_list[0][2]) - 1  # Get the channel of first waveform.
        plt.cla()
        plt.clf()
        # Due to the memory limitation of matplotlib, we must reduce the sample points.
        if num == 10000000:
            if total_chnum > 2:
                down_sample_factor = 4
            elif total_chnum == 2:
                down_sample_factor = 4
            else:
                down_sample_factor = 1
            num = num / down_sample_factor
        elif num == 20000000:
            if total_chnum > 1:
                down_sample_factor = 4
            else:
                down_sample_factor = 2
            num = num / down_sample_factor
        else:
            down_sample_factor = 1
        dt = dso.dt[0]  # Get dt from the first opened channel.
        t_start = dso.hpos[0] - num * dt / 2
        t_end = dso.hpos[0] + num * dt / 2
        t = np.arange(t_start, t_end, dt)
        # print t_start, t_end, dt, len(t)
        if (len(t) - num) == 1:  # Avoid floating point rounding error.
            t = t[:-1]
        wave_type = '-'  # Set waveform type to vector.
        # Draw waveforms.
        ax = [[], [], [], []]
        p = []
        for ch in range(total_chnum):
            if ch == 0:
                ax[ch] = host_subplot(111, axes_class=aa.Axes)
                ax[ch].set_xlabel("Time (sec)")
            else:
                ax[ch] = ax[0].twinx()
            ax[ch].set_ylabel("%s Units: %s" % (dso.ch_list[ch], dso.vunit[ch]))
            ch_color = ch_colortable[int(dso.ch_list[ch][2]) - 1]
            if ch > 1:
                new_fixed_axis = ax[ch].get_grid_helper().new_fixed_axis
                ax[ch].axis["right"] = new_fixed_axis(loc="right", axes=ax[ch], offset=(60 * (ch - 1), 0))
            ax[ch].set_xlim(t_start, t_end)
            ax[ch].set_ylim(-4 * dso.vdiv[ch] - dso.vpos[ch],
                            4 * dso.vdiv[ch] - dso.vpos[ch])  # Setup vertical display range.
            fwave = dso.convertWaveform(ch, down_sample_factor)
            if ch == 0:
                try:
                    p = ax[ch].plot(t, fwave, color=ch_color, ls=wave_type, label=dso.ch_list[ch])
                except:  # TODO: find and fix exception type
                    if mode == 1:
                        # print sys.exc_info()[0]
                        time.sleep(5)
                        print('Trying to plot again!')
                    return -1
            else:
                try:
                    p += ax[ch].plot(t, fwave, color=ch_color, ls=wave_type, label=dso.ch_list[ch])
                except:  # TODO: find and fix exception type
                    if mode == 1:
                        # print sys.exc_info()[0]
                        time.sleep(5)
                        print('Trying to plot again!')
                    return -1
        if total_chnum > 1:
            labs = [c.get_label() for c in p]
            plt.legend(p, labs, loc='upper right')
        plt.tight_layout()
        self.canvas.draw()
        del ax, t, p
        return 0


if __name__ == '__main__':

    print('-' * 77)
    with open('license.txt', 'r') as lic_file:
        lic_file.read()
    print('-' * 77)
    print('OpenWave-2KE V%s\n' % __version__)

    # Get command line arguments.
    cmd = sys.argv[-1]
    if 'OpenWave' in cmd:
        cmd = ''

    # Check interface according to config file or command line argument.
    port = checkinterface(cmd)

    # Connecting to a DSO.
    dso = dso2ke.Dso(port)

    app = QtGui.QGuiApplication(sys.argv)
    main = Window()
    main.show()
    sys.exit(app.exec_())
