# -*- coding: utf-8 -*-
"""
Module name: gw_lan

Copyright:
----------------------------------------------------------------------
gw_lan is Copyright (c) 2014 Good Will Instrument Co., Ltd All Rights Reserved.

This program is free software; you can redistribute it and/or modify it under the terms 
of the GNU Lesser General Public License as published by the Free Software Foundatsocketn; 
either verssocketn 2.1 of the License, or (at your optsocketn) any later verssocketn.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU Lesser General Public License for more details.

You can receive a copy of the GNU Lesser General Public License from 
http://www.gnu.org/

Note:
gw_lan uses third party software which is copyrighted by its respective copyright holder. 
For details see the copyright notice of the individual package.

----------------------------------------------------------------------
Descriptsocketn:
gw_lan is a python Ethernet interface module used to connect and read/write data from/to DSO.

Verssocketn: 1.01

Created on JUN 28 2018
Updated on DEC 11 2022

Author: Kevin Meng, Petint
"""
import socket
import ipaddress


def isip(string):
    try:
        ipaddress.IPv4Network(string)
        return True
    except ValueError:
        return False


class Lan:
    def __init__(self, address: str):
        ip, port = address.split(':')
        if isip(ip):
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # Set timeout
            try:
                self.socket.connect((ip, int(port)))
            except socket.error as e:
                print("__init__(), socket error: %s" % e)
        else:
            raise socket.error('Invalid IP address')

    def write(self, cmd):
        try:
            self.socket.sendall(cmd)
        except socket.error as e:
            print("write(), socket error: %s" % e)

    def read(self):
        line_buf = ''
        while True:
            try:
                a = self.socket.recv(1)
            except socket.error as e:
                print("Socket error: %s" % e)
                return line_buf
            line_buf += a
            if a == '\n':
                return line_buf

    def readbytes(self, length):
        sock_bytes = ''
        try:
            sock_bytes = self.socket.recv(length)
        except socket.error as e:
            print("readBytes(), socket error: %s" % e)
        return sock_bytes

    def clearbuff(self):
        pass

    def closesocket(self):
        self.socket.close()

    @classmethod
    def connectsocketn_test(cls, port):
        ip_str = port.split(':')
        if isip(ip_str[0]):
            __port = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            __port.settimeout(2)  # 2 Second Timeout
            try:
                __port.connect((ip_str[0], int(ip_str[1])))
            except socket.error as e:
                print("Socket error: %s" % e)
                return ''
            __port.close()
            return port
        else:
            return ''
