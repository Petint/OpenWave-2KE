# -*- coding: utf-8 -*-
"""
Module name: gw_com

Copyright:
----------------------------------------------------------------------
gw_com is Copyright (c) 2014 Good Will Instrument Co., Ltd All Rights Reserved.

This program is free software; you can redistribute it and/or modify it under the terms 
of the GNU Lesser General Public License as published by the Free Software Foundation; 
either version 2.1 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU Lesser General Public License for more details.

You can receive a copy of the GNU Lesser General Public License from 
http://www.gnu.org/

Note:
gw_com uses third party software which is copyrighted by its respective copyright holder. 
For details see the copyright notice of the individual package.

----------------------------------------------------------------------
Description:
gw_com is a python USB interface module used to connect and read/write data from/to DSO.

Version: 1.02

Created on JUN 28 2018
Updated on DEC 11 2022

Author: Kevin Meng, Petint
"""
import time
import serial
from serial.tools import list_ports

usb_id = {'2184': ['003f', '0040', '0041', '0042'], '098f': ['2204']}  # USB VID/PID


class Com:
    def __init__(self, port: str):
        try:
            self.tty = serial.Serial(port, baudrate=38400, bytesize=8, parity='N', stopbits=1, xonxoff=False,
                                     dsrdtr=False, timeout=5)
        except serial.SerialException:
            raise Exception(f'Failed to open {port}')

    def write(self, cmd):
        try:
            self.tty.write(cmd)
        except serial.SerialException:
            raise Exception(f'Write failed on {self.tty.name}')

    def read(self):
        try:
            return self.tty.readline()
        except serial.SerialException:
            raise Exception(f'Read failed on {self.tty.name}')

    def readbytes(self, length: int):
        try:
            return self.tty.read(length)
        except serial.SerialException:
            raise Exception(f'Read failed on {self.tty.name}')

    def clearbuf(self):
        time.sleep(0.5)
        while True:
            num = self.tty.inWaiting()
            if num == 0:
                break
            else:
                print('-')
            self.tty.flushInput()  # Clear input buffer.
            time.sleep(0.1)

    def close(self):
        self.tty.close()

    @classmethod
    def connection_test(cls, port):
        __port = serial.Serial(port, baudrate=38400, bytesize=8, parity='N', stopbits=1, xonxoff=False, dsrdtr=False,
                               timeout=5)
        __port.close()
        return port

    @classmethod
    def scanports(cls):
        port_list = list(list_ports.comports())
        for tty in port_list:
            port = tty[2].split('=')
            # print str
            if port[0] == 'USB VID:PID':
                port = port[1].split(' ')[0]  # Extract VID and PID from string.
                port = port.split(':')
                print(port)
                if port[0] in usb_id:
                    if port[1].lower() in usb_id[port[0]]:
                        port = tty[0]
                        try:
                            __port = serial.Serial(port, baudrate=38400, bytesize=8, parity='N', stopbits=1,
                                                   xonxoff=False, dsrdtr=False, timeout=5)
                        except serial.SerialException as e:
                            print(e)
                            continue
                        time.sleep(0.5)
                        while True:
                            num = __port.inWaiting()
                            if num == 0:
                                break
                            else:
                                print('-')
                            __port.flushInput()  # Clear input buffer.
                            time.sleep(0.1)
                        __port.close()
                        return port
        print('Device not found!')
        return ''
