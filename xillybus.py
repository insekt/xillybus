import mmap
import sys

MMAP_SIZE = 0x1000


class Xillybus():

    def __init__(self, dev=''):
        fdev = open(dev, 'r+b')
        self.xmap = mmap.mmap(fdev.fileno(), MMAP_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0)

    def write_bit(self, ptr, bit, value):
        self.xmap.seek(ptr)
        byte = self.__read_byte()
        if value == 0:
            byte &= ~(1 << bit)
        elif value == 1:
            byte |= 1 << bit
        self.xmap.seek(ptr)
        self.__write_byte(byte)

    def read_bit(self, ptr, bit):
        self.xmap.seek(ptr)
        return self.__read_byte() >> bit & 0x01

    def write_bin(self, ptr, offset, value):
        self.xmap.seek(ptr)
        byte = self.__read_byte()
        for i, digit in enumerate(value[::-1]):  # For each bit in value
            if digit == '0':
                byte &= ~(1 << (offset + i))
            elif digit == '1':
                byte |= 1 << (offset + i)
        self.xmap.seek(ptr)
        self.__write_byte(byte)

    def read_bin(self, ptr, offset, length):
        self.xmap.seek(ptr)
        return self.__read_byte() >> offset & (0xFF >> (8 - length))

    def __write_byte(self, value):
        if sys.version_info[0] == 3:
            self.xmap.write_byte(value)
        elif sys.version_info[0] == 2:
            self.xmap.write_byte(chr(value))

    def write_byte(self, ptr, value):
        self.xmap.seek(ptr)
        self.__write_byte(value)

    def __read_byte(self):
        if sys.version_info[0] == 3:
            return self.xmap.read_byte()
        elif sys.version_info[0] == 2:
            return int(self.xmap.read_byte().encode("hex"), 16)

    def read_byte(self, ptr):
        self.xmap.seek(ptr)
        return self.__read_byte()
    
    def write_int16(self, ptr, value):
        self.xmap.seek(ptr)
        if sys.version_info[0] == 3:
            self.xmap.write_byte(value & 0xFF)
            self.xmap.write_byte(value >> 8 & 0xFF)
        elif sys.version_info[0] == 2:
            self.xmap.write_byte(chr(value & 0xFF))
            self.xmap.write_byte(chr(value >> 8 & 0xFF))

    def read_int16(self, ptr):
        self.xmap.seek(ptr)
        value = self.__read_byte()
        value += self.__read_byte() << 8
        return value

    def write_int32(self, ptr, value):
        self.xmap.seek(ptr)
        if sys.version_info[0] == 3:
            self.xmap.write_byte(value & 0xFF)
            self.xmap.write_byte(value >> 8 & 0xFF)
            self.xmap.write_byte(value >> 16 & 0xFF)
            self.xmap.write_byte(value >> 24 & 0xFF)
        elif sys.version_info[0] == 2:
            self.xmap.write_byte(chr(value & 0xFF))
            self.xmap.write_byte(chr(value >> 8 & 0xFF))
            self.xmap.write_byte(chr(value >> 16 & 0xFF))
            self.xmap.write_byte(chr(value >> 24 & 0xFF))

    def read_int32(self, ptr):
        self.xmap.seek(ptr)
        value = self.__read_byte()
        value += self.__read_byte() << 8
        value += self.__read_byte() << 16
        value += self.__read_byte() << 24
        return value

    def write_str(self, ptr, value):
        self.xmap.seek(ptr)
        for i in range(0, len(value), 2):
            self.__write_byte(int(value[i:i+2], 16))

    def read_str(self, ptr, length):
        self.xmap.seek(ptr)
        l = []
        for i in range(1, length):
            l.append('{:02X}'.format(self.__read_byte()))
        value = ''.join(l)
        return value
