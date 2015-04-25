#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 10:23:28 2015

@author: drvmotor
TITLE: python3.3 equivlent for Xillubus operations
all pieces of orig. C-source are stripped

# include <stdio.h>
# include <stdlib.h>
# include <stdint.h>
# include <fcntl.h>
# include <unistd.h>
# include <sys/mman.h>
# include <string.h>

# define DEV_FILENAME "/dev/uio0"
# define MMAP_SIZE 0x1000
# define STRING_BLOCK_SIZE 0x7 // 7 bytes
"""
import sys
import mmap

if __name__ == '__main__':
    # Actual device
    DEV_FILENAME = "/dev/uio0"
else:
    # dummy device for unit test
    DEV_FILENAME = "dvc"

MMAP_SIZE = 0x1000
STRING_BLOCK_SIZE = 0x07
CMD_GET = 0
CMD_SET = 1

value = 0
cmd = CMD_GET

def parse_value(strval, errstr):
 try:
    res = int(strval, 0)
 except ValueError:
    print(errstr)
    usage(sys.argv[0])
    sys.exit(1)
 return res


class Xillybus():
	# xmap=0

	def __init__(self, dev_fn=''):
		fdev = open(dev_fn, 'r+b')
		self.xmap = mmap.mmap(
		    fdev.fileno(), MMAP_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0)
	def read_bit(self, ptr, bit):
		ba = bit >> 3;
		self.xmap.seek(ptr + ba)
		bb = (self.xmap.read_byte() >> (bit & 7))
		print("{0}\n".format(bb & 1))
		return 0

	def write_bit(self, ptr, bit, val):
		ba = bit >> 3
		bit &= 7
		self.xmap.seek(ptr + ba)
		bb = self.xmap.read_byte()
		if val == 0:
			bb &= ~(1 << bit)
		else:
			bb &= 1 << bit
		self.xmap.seek(ptr + ba)
		self.xmap.write_byte((bb))
		return 0

	def read_byte(self,ptr):
		self.xmap.seek(ptr)
		bbb=self.xmap.read_byte()
		print("{0}\n".format(hex(bbb)))
		return 0

	def write_byte(self,ptr,val):
		self.xmap.seek(ptr)
		self.xmap.write_byte((val & 255))
		return 0

	def read_int16(self,ptr):
		self.xmap.seek(ptr)
		#bbb = ord(self.xmap.read_byte())
		bbb = self.xmap.read_byte() & 255
		#bbc = ord(self.xmap.read_byte())
		bbc = self.xmap.read_byte() & 255
		bbd = bbb+(bbc*256)
		print("{0}\n".format(hex(bbd)))
		return 0

	def write_int16(self,ptr,val):
		self.xmap.seek(ptr)
		self.xmap.write_byte((val & 255))
		self.xmap.write_byte((val>>8))
		return 0

	def read_int32(self,ptr):
		self.xmap.seek(ptr)
		bbb= self.xmap.read_byte()
		bbb+= self.xmap.read_byte()<<8
		bbb+= self.xmap.read_byte()<<16
		bbb+= self.xmap.read_byte()<<24
		print("{0}\n".format(hex(bbb)))
		return 0
   
	def write_int32(self,ptr,val):
		self.xmap.seek(ptr)
		self.xmap.write_byte(val & 255)
		self.xmap.write_byte((val>>8) & 255)
		self.xmap.write_byte((val>>16) & 255)
		self.xmap.write_byte((val>>24)& 255)
		return 0

	def read_string(self,ptr,length):
		self.xmap.seek(ptr)
		s=''
		while len(s)<length*2:
			d1 = hex(self.xmap.read_byte())
			d = d1[2:4]
			if len(d) < 2 :
				d= '0'+ d
			s += d
		print( "{0}\n".format(s))
		return 0

	def h2bin(self,s,j):
		x=s[j]
		if (x >= '0') and (x <= '9'):
			return ord(x)-ord('0')
		elif (x>='A') and (x <= 'F'):
			return ord(x)-ord('A')+10
		else:
			return -1
			
	def write_string(self,ptr,sss):
		if (len(sss) & 1) != 0:
			print( "Invalid string\n")
			sys.exit(1)
		SSS=sss.upper()
		ddd=[]
		for j in range(0,len(SSS),2):
			dgh=self.h2bin(SSS,j)
			dgl=self.h2bin(SSS,j+1)
			if (dgh < 0) or (dgl < 0):
				print( "Illegal string value at index {0}: {1}\n".format(j,sss))
			ddd += [dgh*16 + dgl]
		self.xmap.seek(ptr)
		for x in ddd:
			self.xmap.write_byte((x & 255))
		return 0
		
	def read_bin(self,ptr,offset,length):
		self.xmap.seek(ptr+offset//8)
		binbuf=''
		cnt=0
		offset &= 7
		byteval=0
		while length >0:
			length-=1
			if cnt == 0:
				byteval=self.xmap.read_byte() >> offset
				cnt = 8-offset
				offset = 0
			cnt-=1
			sym=chr((byteval & 1)+ ord('0'))
			byteval >>=1
			binbuf +=sym
		print( "{0}\n".format(binbuf))
		return 0 

	def write_bin(self,ptr,offset,sss):
		if len(sss)==0:
			return 0
		for x in sss:#validation
			if (x != '0') and (x != '1'):
				return -1
		# position
		begin = ptr+offset//8 
		offset &= 7
		self.xmap.seek(begin)
		begval=self.xmap.read_byte()
		self.xmap.seek(begin)#restore pos
		for sym in sss:
			msk = ~(1 << offset)
			bitv = ord(sym)-ord('0')
			begval &= msk
			begval |= bitv << offset
			offset += 1
			if offset > 7:
				# store byte
				self.xmap.write_byte(begval)
				begval = 0
				offset = 0
		if offset != 0:
			self.xmap.write_byte(begval)
		return 0

def usage(s=""):
	print("Usage:\n")
	print(s," get address { bit num | byte | int16 | int32 | string length | binary offset length }\n")
	print(s," set address { bit num | byte | int16 | int32 | string | binary offset } value\n")

def get_func(addr=0,xil=0):
	pass
def set_func(addr=0,xil=0):
	pass  
	    
def main():
#  """
# if (argc < 4) {
# printf("Too few arguments\n");
# usage(argv[0]);
# return 1;
# }
# """
	retcode =0
	if len(sys.argv) < 4:
	    print("Too few arguments\n")
	    usage(sys.argv[0])
	    sys.exit(1)
	# check addr
	address= parse_value(sys.argv[2],"Invalid address: {0}\n".format(sys.argv[2]))
	# memmap device
	xil=Xillybus(DEV_FILENAME)
	# check cmd
	if sys.argv[1]=="get":
		retcode = get_func(address,xil)
	elif sys.argv[1]=="set":
		if len(sys.argv) < 5:
			print( "Missing value for set command\n")
			usage(sys.argv[0])
			sys.exit(1)
		retcode = set_func(address,xil)
	else: #just error
		print("Invalid command: {0}\n".format(sys.argv[1]))
		usage(sys.argv[0])
		sys.exit(1)
	
	return retcode
	
# read a number from a source and validate it for max and min values 
def get_anum(s,nmin,nmax):
	num=parse_value(s,"Invalid number: {0}\n".format(s))
	if (num < nmin) or (num > nmax):
		print("Number {0} not in range [{1}..{2}]\n".format(num,nmin,nmax))
		sys.exit(1)
	return num
	
def get_bitnum(s):
	num=parse_value(s,"Invalid bit number: {0}\n".format(s))
	if (num < 0) or (num > 31):
		print("Bit number {0} not in range [0; 31]\n".format(num))
		sys.exit(1)
	return num
    
	
def get_func(addr=0,xil=0):
	if sys.argv[3]=='bit':
		bitn = get_bitnum(sys.argv[4])
		return xil.read_bit(addr,bitn)
	if sys.argv[3]=='byte':
		return xil.read_byte(addr)
	if sys.argv[3]=='int32':
		return xil.read_int32(addr)
	if sys.argv[3]=='int16':
		return xil.read_int16(addr)
	if sys.argv[3]=='string':
		lng = parse_value(sys.argv[4],"Invalid string length: {0}".format(sys.argv[4]))
		return xil.read_string(addr,lng)
	if sys.argv[3]=='binary':
		offs=get_bitnum(sys.argv[4])
		lngof=get_anum(sys.argv[5],0,0xFFFFFFFF)
		return xil.read_bin(addr,offs,lngof)
    # empty action
	print("Warning: nothing to be done\n")
	return 0
	
def set_func(addr=0,xil=0):
    # check value
	if sys.argv[3]=='bit':
	# read number
		bitn = get_bitnum(sys.argv[4])
		val= ord(sys.argv[5])-ord('0')
		return xil.write_bit(addr,bitn,val)
	if sys.argv[3]=='byte':
		val = get_anum(sys.argv[4],0,255)
		return xil.write_byte(addr,val)
	if sys.argv[3]=='int32':
		val = get_anum(sys.argv[4],0,0xFFFFFFFF)
		return xil.write_int32(addr,val)
	if sys.argv[3]=='int16':
		val = get_anum(sys.argv[4],0,0xFFFF)
		return xil.write_int16(addr,val)
	if sys.argv[3]=='string':
		return xil.write_string(addr,sys.argv[4])
	if sys.argv[3]=='binary':
		offs=get_bitnum(sys.argv[4])
		return xil.write_bin(addr,offs,sys.argv[5])
    # empty action
	print("Warning: nothing to be done\n")
	return 0
# start
if __name__ == '__main__':
	main()
