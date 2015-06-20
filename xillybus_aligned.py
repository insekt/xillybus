import sys
import mmap

MMAP_SIZE = 0x1000

# All writes and reads are aligned

def check_bit(offset):
    if not 0 <= offset <= 31:
        print('Error: offset must be in range 0-31')
        sys.exit(1)

def check_bin(offset, length):
    if not 0 <= offset <= 30:
        print('Error: offset must be in range 0-30')
        sys.exit(1) 
    if not 2 <= length <= 32:
        print('Error: length must be in range 2-30')
        sys.exit(1) 
    if offset + length > 32:
        print('Error: offset + length out of range')
        sys.exit(1)

def check_byte(ptr):
    shift = ptr % 4
    if not shift <= 3:
        print('Error: address out of register range')
        sys.exit(1)

def check_int16(ptr):
    shift = ptr % 4
    if not shift <= 2:
        print('Error: address out of register range')
        sys.exit(1)

class Xillybus():

    def __init__(self, dev=''):
        fdev = open(dev, 'r+b')
        self.xmap = mmap.mmap(
            fdev.fileno(), MMAP_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0)

    # All other functions use write_int32 and read_int32 to access register
    # These functions use aligned address, it means ADDRESS % 4 == 0
    def write_int32_(self, ptr, value):
        shift = ptr % 4
        ptr = ptr - shift
        self.xmap.seek(ptr)
        self.xmap.write_byte(value & 0xFF)
        self.xmap.write_byte(value >> 8 & 0xFF)
        self.xmap.write_byte(value >> 16 & 0xFF)
        self.xmap.write_byte(value >> 24 & 0xFF)

    def read_int32(self, ptr):
        shift = ptr % 4
        ptr = ptr - shift
        self.xmap.seek(ptr)
        value = self.xmap.read_byte()
        value += self.xmap.read_byte() << 8
        value += self.xmap.read_byte() << 16
        value += self.xmap.read_byte() << 24
        return value

    def write_bit(self, ptr, offset, value):
        check_bit(offset)
        register = self.read_int32(ptr)
        if value == 0:
            register &= ~(1 << 8 * (ptr % 4) + offset) # Here and further, 8 * (ptr % 4) is a shift from 1 byte
        elif value == 1:
            register |= 1 << 8 * (ptr % 4) + offset
        self.write_int32(ptr, register)

    def read_bit(self, ptr, offset):
        check_bit(offset)
        return self.read_int32(ptr) >> (8 * (ptr % 4) + offset) & 0x1

    def write_bin(self, ptr, offset, value):    
        check_bin(offset, len(value))
        register = self.read_int32(ptr)
        for i, digit in enumerate(value[::-1]): # For each bit in value, HighLow
            if digit == '0':
                register &= ~(1 << (8 * (ptr % 4) + offset + i))
            elif digit == '1':
                register |= 1 << (8 * (ptr % 4) + offset + i)
        self.write_int32(ptr, register)

    def read_bin(self, ptr, offset, length):
        check_bin(offset, length)
        return self.read_int32(ptr) >> (8 * (ptr % 4) + offset) & (0xFF >> (32 - length))

    def write_byte(self, ptr, value):
        check_byte(ptr)
        register = self.read_int32(ptr) & ~(0xFF << 8 * (ptr % 4)) # Write 0s
        register |= value << 8 * (ptr % 4) # Write value
        self.write_int32(ptr, register)
            
    def read_byte(self, ptr):
        check_byte(ptr)
        return self.read_int32(ptr) >> 8 * (ptr % 4) & 0xFF

    def write_int16(self, ptr, value):
        check_int16(ptr)
        register = self.read_int32(ptr) & ~(0xFFFF << 8 * (ptr % 4))
        register |= value << 8 * ptr % 4
        self.write_int32(ptr, register)

    def read_int16(self, ptr):
        check_int16(ptr)
        return self.read_int32(ptr) >> 8 * (ptr % 4) & 0xFFFF
   
    def write_str(self, ptr, value):
        value = value[::-1] # Reverse string, LowHigh -> HighLow
        self.xmap.seek(ptr)
        self.xmap.write_byte(int(value, 16) & 0xFF)
        for i in range(1, int(len(value) / 2)):
            self.xmap.write_byte(int(value, 16) >> (i * 8) & 0xFF)

    def read_str(self, ptr, length):
        self.xmap.seek(ptr)
        value = self.xmap.read_byte()
        for i in range(1, length):
            value += self.xmap.read_byte() << (i * 8)
        return '{:0{length}x}'.format(value, length = length * 2)[::-1] # Fill leading 0 and reverse HighLow -> LowHigh
